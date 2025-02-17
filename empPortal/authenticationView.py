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

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        if request.method == 'POST': 
            login_via = request.POST.get('login_via', '').strip()
            email = request.POST.get('email', '').strip()
            mobile = request.POST.get('mobile', '').strip()
            remember_me = request.POST.get('rememberme', '').strip()
            password = request.POST.get('password', '').strip()
            
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

            elif login_via == '2':  # Login via Mobile
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
    else:
        if request.method == 'POST':
            # Extract form data
            full_name = request.POST.get('full_name', '').strip()
            gender = request.POST.get('gender', '').strip()
            email = request.POST.get('email', '').strip()
            mobile = request.POST.get('mobile', '').strip()
            password = request.POST.get('password', '').strip()
            remember_me = request.POST.get('rememberme', '').strip()

            # Validation Errors
            if not full_name:
                messages.error(request, 'Full Name is required.')

            if not gender:
                messages.error(request, 'Gender is required.')

            if not email:
                messages.error(request, 'Email Address is required.')
            elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                messages.error(request, 'Invalid email format.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'This email is already registered.')

            if not mobile:
                messages.error(request, 'Mobile Number is required.')
            elif not mobile.isdigit():
                messages.error(request, 'Mobile number must contain only digits.')
            elif len(mobile) != 10:
                messages.error(request, 'Mobile number must be 10 digits long.')
            elif User.objects.filter(username=mobile).exists():
                messages.error(request, 'This mobile number is already registered.')

            if not password:
                messages.error(request, 'Password is required.')

            # Redirect if there are validation errors
            if messages.get_messages(request):
                return redirect(request.META.get('HTTP_REFERER', '/'))

            # Create new user if there are no validation errors
            user = User.objects.create_user(
                username=mobile,  # Using mobile number as username
                email=email,
                password=password
            )

            # Optionally, set the full name and gender if needed
            user.first_name = full_name
            user.profile.gender = gender  # Assuming you have a custom profile model for gender
            user.save()

            # Automatically log in the user after registration
            user = authenticate(request, username=mobile, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')

            messages.error(request, 'Failed to create an account.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        return render(request, 'authentication/register.html')