from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users, DocumentUpload, Branch
from empPortal.model import BankDetails
from ..forms import DocumentUploadForm

from django.utils.timezone import now
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

def members(request):
    if request.user.is_authenticated:
        if request.user.role_id == 1:
            # Define the list of role IDs to filter
            # role_ids = [2, 3, 4]
            role_ids = [4]
            # Filter users whose role_id is in the specified list
            users = Users.objects.filter(role_id__in=role_ids)
        else:
            users = Users.objects.none()  # Return an empty queryset for unauthorized users
        return render(request, 'members/members.html', {'users': users})
    else:
        return redirect('login')
    
def memberView(request, user_id):
    if request.user.is_authenticated:
        # Fetch user details and bank details
        user_details = Users.objects.get(id=user_id)
        bank_details = BankDetails.objects.filter(user_id=user_id).first()

        docs = DocumentUpload.objects.filter(user_id=user_id).first()
        # Fetch commissions for the specific member
        query = """
            SELECT c.*, u.first_name, u.last_name, c.product_id
            FROM commissions c
            INNER JOIN users u ON c.member_id = u.id
            WHERE c.member_id = %s
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [user_id])
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

        branches = Branch.objects.all().order_by('-created_at')

        return render(request, 'members/member-view.html', {
            'user_details': user_details,
            'bank_details': bank_details,
            'docs': docs,
            'branches': branches,
            'commissions': commissions_list,  # Fixed variable name
            'products': products  # Fixed variable name
        })
    else:
        return redirect('login')
    
    
def get_branch_managers(request):
    branch_id = request.GET.get('branch_id')
    branch_managers = Users.objects.filter(branch_id=branch_id, role_id=2).values('id', 'first_name', 'last_name')
    managers_list = [{'id': manager['id'], 'full_name': f"{manager['first_name']} {manager['last_name']}"} for manager in branch_managers]
    return JsonResponse({'branch_managers': managers_list})

def get_sales_managers(request):
    branch_manager_id = request.GET.get('branch_manager_id')
    sales_managers = Users.objects.filter(senior_id=branch_manager_id, role_id=3).values('id', 'first_name', 'last_name')
    sales_list = [{'id': manager['id'], 'full_name': f"{manager['first_name']} {manager['last_name']}"} for manager in sales_managers]
    return JsonResponse({'sales_managers': sales_list})

def activateUser(request, user_id):
    if request.user.is_authenticated:
        docs = DocumentUpload.objects.filter(user_id=user_id).first()
        
        # Check if all required documents are approved
        if (
            docs and
            docs.aadhaar_card_front_status == 'Approved' and
            docs.aadhaar_card_back_status == 'Approved' and
            docs.upload_pan_status == 'Approved' and
            docs.upload_cheque_status == 'Approved' and
            docs.tenth_marksheet_status == 'Approved'
        ):
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET activation_status = %s WHERE id = %s",
                    ['1', user_id]
                )

            # Display success message
            messages.success(request, 'User account has been activated successfully!')
        else:
            messages.error(request, 'User cannot be activated. Please ensure all required documents are approved.')

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


def update_doc_status(request):
    if request.method == "POST":
        
        try:
            data = json.loads(request.body)  # Correct way to get JSON data
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
        doc_type = data.get("docType")
        status = data.get("status")
        doc_id = data.get("docId")

        # Validate inputs
        if not doc_type or not status or not doc_id:
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        # Check if status is valid
        valid_statuses = ["Pending", "Approved", "Rejected"]
        if status not in valid_statuses:
            return JsonResponse({"error": "Invalid status"}, status=400)

        # Fetch the document record
        document = get_object_or_404(DocumentUpload, id=doc_id)

        # Check if the requested document type exists in the model
        status_field = f"{doc_type}_status"
        updated_at_field = f"{doc_type}_updated_at"

        if not hasattr(document, status_field) or not hasattr(document, updated_at_field):
            return JsonResponse({"error": "Invalid document type"}, status=400)

        # Update status and timestamp
        setattr(document, status_field, status)
        setattr(document, updated_at_field, now())
        document.save()

        return JsonResponse({"success": True, "message": f"Status updated to {status}!"})
    
    return JsonResponse({"error": "Invalid request method"}, status=405)