from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users, PersonalDocument
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


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def myAccount(request):
    if request.user.is_authenticated:
        # Fetch user and bank details for the logged-in user
        user_details = Users.objects.get(id=request.user.id)  # Fetching the user's details
        bank_details = BankDetails.objects.filter(user_id=request.user.id).first()  # Fetching bank details

        # Fetch commissions for the specific member
        query = """
            SELECT c.*, u.first_name, u.last_name, c.product_id
            FROM commissions c
            INNER JOIN users u ON c.member_id = u.id
            WHERE c.member_id = %s
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [request.user.id])
            commissions_list = dictfetchall(cursor)

        # Define available products
        products = [
            {'id': 1, 'name': 'Motor'},
            {'id': 2, 'name': 'Health'},
            {'id': 3, 'name': 'Term'},
        ]

        # Ensure dictionary uses integer keys
        product_dict = {product['id']: product['name'] for product in products}

        # Map product names to commissions list
        for commission in commissions_list:
            product_id = commission.get('product_id')
            commission['product_name'] = product_dict.get(int(product_id), 'Unknown') if product_id is not None else 'Unknown'

        return render(request, 'profile/my-account.html', {
            'user_details': user_details,
            'bank_details': bank_details,
            'products': products,
            'commissions': commissions_list  # Fixed variable name
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
