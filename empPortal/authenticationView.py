from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect
from django.contrib import messages
from django.template import loader
from .models import Roles,Users,PolicyDocument,BulkPolicyLog
from django.contrib.auth import authenticate, login ,logout
from django.core.files.storage import FileSystemStorage
import re
import requests
from fastapi import FastAPI, File, UploadFile
import fitz
import openai
import time
import json
from django.http import JsonResponse
import os
import zipfile
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        if request.method == 'POST': 
            login_via = request.POST.get('loginvia', '').strip()
            email = request.POST.get('email', '').strip()
            mobile = request.POST.get('mobile', '').strip()
            remember_me = request.POST.get('rememberme', '').strip()
            password = request.POST.get('password', '').strip()
            login_via = '1'
            # Validation Errors
            if not login_via:
                messages.error(request, 'Login via field is required')

            if login_via == '1':  # Login via Email
                if not email:
                    messages.error(request, 'Email is required')
                elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                    messages.error(request, 'Invalid email format')
                elif not Users.objects.filter(email=email).exists():
                    messages.error(request, 'This email is invalid')

            elif login_via == 'Mobile':  # Login via Mobile
                if not mobile:
                    messages.error(request, 'Mobile is required')
                elif not mobile.isdigit():
                    messages.error(request, 'Mobile No must contain only numbers')
                elif mobile[0] <= '5':
                    messages.error(request, 'Invalid Mobile No')
                elif len(mobile) != 10:
                    messages.error(request, 'Mobile No must be of 10 digits')
                elif not Users.objects.filter(phone=mobile).exists():
                    messages.error(request, 'This mobile number is not registered with us.')

            # Password Validation
            if not password:
                messages.error(request, 'Password is required.')

            # Redirect if there are errors
            if list(messages.get_messages(request)):  
                return redirect(request.META.get('HTTP_REFERER', '/'))

            # Fetch User Data
            username = email if login_via == "1" else mobile
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials')
                return redirect(request.META.get('HTTP_REFERER', '/'))

        return render(request, 'authentication/login.html')
    

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        
        # Extract form data
        full_name = request.POST.get('full_name', '').strip()
        gender = request.POST.get('gender', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '').strip()

        # Splitting full name into first and last name
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ''
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''

        # Validation Errors
        if not full_name:
            messages.error(request, 'Full Name is required.')

        if not gender:
            messages.error(request, 'Gender is required.')

        if not email:
            messages.error(request, 'Email Address is required.')
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            messages.error(request, 'Invalid email format.')
        elif Users.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')

        if not mobile:
            messages.error(request, 'Mobile Number is required.')
        elif not mobile.isdigit():
            messages.error(request, 'Mobile number must contain only digits.')
        elif len(mobile) != 10:
            messages.error(request, 'Mobile number must be 10 digits long.')
        elif Users.objects.filter(phone=mobile).exists():
            messages.error(request, 'This mobile number is already registered.')

        if not password:
            messages.error(request, 'Password is required.')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')

        # Redirect if there are validation errors
        if messages.get_messages(request):
            return render(request, 'authentication/register.html')
    

        # Generate User ID
        last_user = Users.objects.all().order_by('-id').first()
        if last_user and last_user.user_gen_id.startswith('UR-'):
            last_user_gen_id = int(last_user.user_gen_id.split('-')[1])
            new_gen_id = f"UR-{last_user_gen_id + 1:04d}"
        else:
            new_gen_id = "UR-0001"

        # Hash password
        hashed_password = make_password(password)

        # Create new user
        user = Users(
            user_gen_id=new_gen_id,
            role_id=2,  # Assuming role is assigned later
            role_name="User",
            user_name=full_name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=mobile,
            gender=gender,
            password=hashed_password,
            status=1,
            is_superuser=0,
            is_staff= 0 ,
            is_active=0
        )
        user.save()

        # Automatically log in the user after registration
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('verify-otp')

        # messages.error(request, 'Failed to create an account.')
        # return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'authentication/register.html')

def check_email(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        print(f"Checking email: {email}")  # Debugging

        exists = Users.objects.filter(email=email).exists()
        print(f"Exists in DB: {exists}")  # Debugging

        return JsonResponse({"exists": exists})

    return JsonResponse({"error": "Invalid request"}, status=400)


def login_mobile_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        mobile = request.POST.get('mobile', '').strip()

        # Validation Errors
        if not mobile:
            messages.error(request, 'Mobile number is required.')
        elif not mobile.isdigit():
            messages.error(request, 'Mobile number must contain only digits.')
        elif len(mobile) != 10:
            messages.error(request, 'Mobile number must be 10 digits long.')
        elif mobile[0] <= '5':  # Mobile numbers in India start from 6-9
            messages.error(request, 'Invalid Mobile Number.')
        elif not Users.objects.filter(phone=mobile).exists():
            messages.error(request, 'This mobile number is not registered.')

        # Redirect if validation fails
        if list(messages.get_messages(request)):  
            return render(request, 'authentication/login.html')

        # Fetch User and Log Them In
        user = Users.objects.filter(phone=mobile).first()
        if user:
            user.is_login_available = 0  # Set is_login_available to 0
            user.save(update_fields=['is_login_available'])  # Save only this field
            login(request, user)  # Log in without password
            return redirect('verify-otp')

        messages.error(request, 'Login failed. Please try again.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'authentication/login.html')


def forget_pass_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        if request.method == 'POST': 
            email = request.POST.get('email', '').strip()
            # Validation Errors
            if not email:
                messages.error(request, 'Email is required')

            # Redirect if there are errors
            if list(messages.get_messages(request)):  
                return redirect(request.META.get('HTTP_REFERER', '/'))

        # Fetch User and Log Them In
            user = Users.objects.filter(email=email).first()
            if user:
                user.is_login_available = 0  # Set is_login_available to 0
                user.save(update_fields=['is_login_available'])  # Save only this field
                login(request, user)  # Log in without password
                return redirect('email-verify-otp')
            else:
                messages.error(request, 'Invalid credentials')
                return redirect(request.META.get('HTTP_REFERER', '/'))

        return render(request, 'authentication/reset-password.html')

def email_verify_otp(request):
    if request.user.is_authenticated and request.method != 'POST':
        if request.user.is_login_available == 0:
            return render(request, 'authentication/email-otp-verify.html')
        elif request.user.is_active == 1:
            return redirect('dashboard')

    if request.method == 'POST':

        request.user.is_login_available = 0
        request.user.is_active = 1
        request.user.save()
        return redirect('reset-password')

        # Extract form data
        # email = request.POST.get('email', '').strip()
        # otp = request.POST.get('otp', '').strip()

        # if not email:
        #     messages.error(request, 'Please enter your email address.')
        # elif not Users.objects.filter(email=email).exists():
        #     messages.error(request, 'This email is not registered.')

        # if not otp:
        #     messages.error(request, 'Please enter the OTP.')
        # else:
        #     stored_otp = cache.get(f'otp_{email}')  # Fetch stored OTP from cache
        #     if not stored_otp:
        #         messages.error(request, 'OTP has expired. Please request a new one.')
        #     elif otp != stored_otp:
        #         messages.error(request, 'Invalid OTP. Please try again.')

        # # Redirect if there are validation errors
        # if messages.get_messages(request):
        #     return redirect(request.META.get('HTTP_REFERER', '/'))

        # # If OTP is valid, activate the user
        # user = Users.objects.get(email=email)
        # user.is_active = True
        # user.save()

        # # Log in the user
        # login(request, user)
        # messages.success(request, 'OTP verified successfully. Welcome!')
        # return redirect('dashboard')

    return render(request, 'authentication/email-otp-verify.html')

def reset_pass_view(request):
    if request.user.is_authenticated and request.method != 'POST':
        if request.user.is_login_available == 0:
            return render(request, 'authentication/change-password.html')
        elif request.user.is_active == 1:
            return redirect('dashboard')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not new_password:
            messages.error(request, "New password is required.")
        elif not confirm_password:
            messages.error(request, "Confirm password is required.")
        elif new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")

        # If validation fails, return with error messages
        if list(messages.get_messages(request)):
            return render(request, 'authentication/change-password.html')

        # Update password and user status
        request.user.is_login_available = 1
        request.user.is_active = 1
        request.user.password = make_password(new_password)
        request.user.save()

        messages.success(request, "Password reset successfully.")
        return redirect('my-account')

    return render(request, 'authentication/change-password.html')


def register_view2(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        # Extract form data
        full_name = request.POST.get('full_name', '').strip()
        gender = request.POST.get('gender', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '').strip()

        # Splitting full name into first and last name
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ''
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''

        # Validation Errors
        if not full_name:
            messages.error(request, 'Full Name is required.')

        if not gender:
            messages.error(request, 'Gender is required.')

        if not email:
            messages.error(request, 'Email Address is required.')
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            messages.error(request, 'Invalid email format.')
        elif Users.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')

        if not mobile:
            messages.error(request, 'Mobile Number is required.')
        elif not mobile.isdigit():
            messages.error(request, 'Mobile number must contain only digits.')
        elif len(mobile) != 10:
            messages.error(request, 'Mobile number must be 10 digits long.')
        elif Users.objects.filter(phone=mobile).exists():
            messages.error(request, 'This mobile number is already registered.')

        if not password:
            messages.error(request, 'Password is required.')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')

        # Redirect if there are validation errors
        if messages.get_messages(request):
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Generate User ID
        last_user = Users.objects.all().order_by('-id').first()
        if last_user and last_user.user_gen_id.startswith('UR-'):
            last_user_gen_id = int(last_user.user_gen_id.split('-')[1])
            new_gen_id = f"UR-{last_user_gen_id + 1:04d}"
        else:
            new_gen_id = "UR-0001"

        # Hash password
        hashed_password = make_password(password)

        # Create new user
        user = Users(
            user_gen_id=new_gen_id,
            role_id=2,  # Assuming role is assigned later
            role_name="User",
            user_name=full_name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=mobile,
            gender=gender,
            password=hashed_password,
            status=1,
            is_superuser=0,
            is_staff= 0 ,
            is_active=0
        )
        user.save()

        # Automatically log in the user after registration
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('verify-otp')

        # messages.error(request, 'Failed to create an account.')
        # return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'authentication/register2.html')

def verify_otp_view(request):
    if request.user.is_authenticated and request.method != 'POST':
        if request.user.is_login_available == 0:
            return render(request, 'authentication/verify-otp.html')
        elif request.user.is_active == 1:
            return redirect('dashboard')

    if request.method == 'POST':

        request.user.is_login_available = 1
        request.user.is_active = 1
        request.user.save()
        return redirect('my-account')

        # Extract form data
        # email = request.POST.get('email', '').strip()
        # otp = request.POST.get('otp', '').strip()

        # if not email:
        #     messages.error(request, 'Please enter your email address.')
        # elif not Users.objects.filter(email=email).exists():
        #     messages.error(request, 'This email is not registered.')

        # if not otp:
        #     messages.error(request, 'Please enter the OTP.')
        # else:
        #     stored_otp = cache.get(f'otp_{email}')  # Fetch stored OTP from cache
        #     if not stored_otp:
        #         messages.error(request, 'OTP has expired. Please request a new one.')
        #     elif otp != stored_otp:
        #         messages.error(request, 'Invalid OTP. Please try again.')

        # # Redirect if there are validation errors
        # if messages.get_messages(request):
        #     return redirect(request.META.get('HTTP_REFERER', '/'))

        # # If OTP is valid, activate the user
        # user = Users.objects.get(email=email)
        # user.is_active = True
        # user.save()

        # # Log in the user
        # login(request, user)
        # messages.success(request, 'OTP verified successfully. Welcome!')
        # return redirect('dashboard')

    return render(request, 'authentication/verify-otp.html')