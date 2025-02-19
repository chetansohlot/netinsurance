from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users
from empPortal.model import BankDetails

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
from django.db import connection

from pprint import pprint 

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()


def members(request):
    if request.user.is_authenticated:
        if request.user.role_id == 1:
            users = Users.objects.filter(role_id=2)
        else:
            users = Users.objects.none()
        return render(request, 'members/members.html', {'users': users})
    else:
        return redirect('login')
    

def memberView(request, user_id):
    if request.user.is_authenticated:
        user_details = Users.objects.get(id=user_id)  # Fetching the user's details
        bank_details = BankDetails.objects.filter(user_id=user_id).first()  # Fetching bank details

        return render(request, 'members/member-view.html', {
            'user_details': user_details,
            'bank_details': bank_details
        })
    else:
        return redirect('login')
    
def activateUser(request, user_id):
    if request.user.is_authenticated:
        try:
            # Check if the user exists
            user_details = Users.objects.get(id=user_id)

            # Activate the user (set activation_status to '1')
            user_details.activation_status = '1'
            user_details.save()

            # Display success message
            messages.success(request, 'User account has been activated successfully!')

        except Users.DoesNotExist:
            # If the user does not exist, show an error message
            messages.error(request, 'User not found.')

        # Redirect back to the member view page after activation
        return redirect('member-view', user_id=user_id)
    else:
        return redirect('login')

    

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def myAccount(request):
    if request.user.is_authenticated:
        # Fetch user and bank details for the logged-in user
        user_details = Users.objects.get(id=request.user.id)  # Fetching the user's details
        bank_details = BankDetails.objects.filter(user_id=request.user.id).first()  # Fetching bank details

        return render(request, 'profile/my-account.html', {
            'user_details': user_details,
            'bank_details': bank_details
        })
    else:
        return redirect('login')


def update_user_details(request):
    if request.method == 'POST':
        user_details = Users.objects.get(id=request.user.id)
        user_details.first_name = request.POST['first_name']
        user_details.last_name = request.POST['last_name']
        user_details.email = request.POST['email']
        user_details.phone = request.POST['phone']
        user_details.gender = request.POST['gender']
        user_details.dob = request.POST['dob']
        user_details.state = request.POST['state']
        user_details.city = request.POST['city']
        user_details.pincode = request.POST['pincode']
        user_details.address = request.POST['address']
        user_details.save()

        messages.success(request, "User details updated successfully!")
        return redirect('my-account')  # Redirect back to the user profile page

def storeOrUpdateBankDetails(request):
    if request.method == "POST":
        user_id = request.user.id  # Get the logged-in user's ID
        
        # Check if the bank details already exist for this user
        bank_details, created = BankDetails.objects.get_or_create(user_id=user_id)
        
        # Update the bank details
        bank_details.account_holder_name = request.POST.get('account_holder_name')
        bank_details.re_enter_account_number = request.POST.get('re_enter_account_number')
        bank_details.account_number = request.POST.get('account_number')
        bank_details.ifsc_code = request.POST.get('ifsc_code')
        bank_details.city = request.POST.get('city')
        bank_details.state = request.POST.get('state')
        
        # Save the updated or newly created bank details
        bank_details.save()

        # Show success message
        messages.success(request, "Bank details have been updated successfully.")
        
        # Redirect to the my-account page after saving the details
        return redirect('my-account')

    # If not a POST request, redirect to my-account
    return redirect('my-account')
