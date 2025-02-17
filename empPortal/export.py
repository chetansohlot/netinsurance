from django.http import HttpResponse
import pandas as pd 
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
from django.http import HttpResponse
from django.contrib import messages
from .models import PolicyDocument
from faker import Faker 
from .models import PolicyDocument
fake = Faker()

processed_text = {"policy_number": "3005/O/379425038/00/000", "vehicle_number": "HR98P4781", "insured_name": "SHELLEY MUNJAL", "issue_date": "2025-02-01", "expiry_date": "2026-02-01", "premium_amount": "1,163.00", "sum_insured": "64,073.00", "policy_period": "1 year", "total_premium": "1,372.00", "insurance_company": "ICICI Lombard General Insurance Company Limited", "coverage_details": [{"benefit": "Basic OD Premium", "amount": "612.00"}, {"benefit": "Zero Depreciation (Silver)", "amount": "449.00"}, {"benefit": "Return to Invoice", "amount": "224.00"}]}
    # for i in range(0,10):
    #         vehicle_number = re.sub(r'[^a-zA-Z0-9]','',processed_text['vehicle_number'])
    #         PolicyDocument.objects.create(
    #             filename=fake.name,
    #             extracted_text=processed_text,
    #             filepath="/media/daha.pdf",
    #             rm_name=request.user.full_name,
    #             insurance_provider=processed_text['insurance_company'],
    #             vehicle_number=vehicle_number,
    #             policy_number=processed_text['policy_number'],
    #             policy_issue_date=processed_text['issue_date'],
    #             policy_expiry_date=processed_text['expiry_date'],
    #             policy_period=processed_text['policy_period'],
    #             holder_name=processed_text['insured_name'],
    #             policy_total_premium=processed_text['total_premium'],
    #             policy_premium=processed_text['premium_amount'],
    #             sum_insured=processed_text['sum_insured'],
    #             coverage_details=processed_text['coverage_details'],
    #             status=1,
    #         )
# def exportPolicies(request):
#     # Query the PolicyDocument model for all policy records

#     # 
#     policies = PolicyDocument.objects.all().order_by('-id')

#     # Prepare the data for export
#     policy_data = []
#     for policy in policies:
#         policy_data.append([
#             policy.insurance_provider,
#             policy.vehicle_number,
#             policy.holder_name,
#             policy.policy_number,
#             policy.policy_issue_date,
#             policy.policy_expiry_date,
#             policy.policy_period,
#             policy.policy_premium,
#             policy.policy_total_premium
#         ])
#     # Create a DataFrame
#     columns = [
#         'Insurer Name', 'Vehicle Number', 'Holder Name', 'Policy Number', 
#         'Policy Issue Date', 'Policy Expiry Date', 'Policy Period', 
#         'Policy Premium', 'Total Premium'
#     ]
#     df = pd.DataFrame(policy_data, columns=columns)

#     # Generate the response for the Excel file
#     response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     response['Content-Disposition'] = 'attachment; filename=policy_data.xlsx'
    
#     # Write to Excel using pandas ExcelWriter
#     with pd.ExcelWriter(response, engine='openpyxl') as writer:
#         df.to_excel(writer, index=False, sheet_name='Policies')
#     # Optional: Flash a success message
#     messages.success(request, "The policy data has been successfully exported.")
    
#     return response

# def check_related_policies(request):
#     # Fetch all policies with their related old_policy
#     policies = PolicyDocument.objects.select_related('old_policy').get(id=1)

#     # Print the response in the terminal (for debugging)
#     for policy in policies:
#         print(f"Policy: {policy.policy_number}, Holder: {policy.holder_name}")

#         if policy.old_policy:
#             print(f"  ↳ Matched Old Policy: {policy.old_policy.policy_number}")

#     # Return the response in JSON format (to check in browser/Postman)
#     data = [
#         {
#             "policy_number": policy.policy_number,
#             "holder_name": policy.holder_name,
#             "old_policy_number": policy.old_policy.policy_number if policy.old_policy else "No Match"
#         }
#         for policy in policies
#     ]

#     return JsonResponse({"policies": data})

def exportPolicies(request):
    # Query the PolicyDocument model for all policy records
    policies = PolicyDocument.objects.all().order_by('-id')

    # Prepare the data for export
    policy_data = []
    for policy in policies:
        policy_data.append([
            policy.insurance_provider,
            policy.vehicle_number,
            policy.holder_name,
            policy.policy_number,
            policy.policy_issue_date,
            policy.policy_expiry_date,
            policy.policy_period,
            policy.policy_premium,
            policy.policy_total_premium,
            policy.payment_status,  # Add payment_status
            policy.policy_type,  # Add policy_type
            policy.vehicle_type,  # Add vehicle_type
            policy.vehicle_make,  # Add vehicle_make
            policy.vehicle_model,  # Add vehicle_model
            policy.vehicle_gross_weight,  # Add vehicle_gross_weight
            policy.vehicle_manuf_date,  # Add vehicle_manuf_date
            policy.gst,  # Add gst
            policy.od_premium,  # Add od_premium
            policy.tp_premium,  # Add tp_premium
        ])
    
    # Create a DataFrame
    columns = [
        'Insurer Name', 'Vehicle Number', 'Holder Name', 'Policy Number', 
        'Policy Issue Date', 'Policy Expiry Date', 'Policy Period', 
        'Policy Premium', 'Total Premium', 'Payment Status', 'Policy Type', 
        'Vehicle Type', 'Vehicle Make', 'Vehicle Model', 'Vehicle Gross Weight', 
        'Vehicle Manufacture Date', 'GST', 'OD Premium', 'TP Premium'
    ]
    df = pd.DataFrame(policy_data, columns=columns)

    # Generate the response for the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=policy_data.xlsx'
    
    # Write to Excel using pandas ExcelWriter
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Policies')
    
    # Optional: Flash a success message
    messages.success(request, "The policy data has been successfully exported.")
    
    return response
