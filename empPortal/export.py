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
import openpyxl
from openpyxl.styles import Font, PatternFill
from django.http import HttpResponse
fake = Faker()
from django.utils import timezone
import datetime
from django.conf import settings

dt_aware = timezone.now()  # Django returns a timezone-aware datetime
dt_naive = dt_aware.replace(tzinfo=None) 

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


def download_policy_data(request):
    # Create an in-memory Excel workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Policy Data"

    # Define headers
    headers = [
        "Policy Month", "Agent Name", "SM Name", "Franchise Name", "Insurer Name", "S.P. Name",
        "Issue Date", "Risk Start Date", "Payment Status", "Insurance Company", "Policy Type",
        "Policy No", "Insured Name", "Vehicle Type", "Vehicle Make/Model", "Gross Weight", 
        "Reg. No.", "MFG Year", "Sum Insured", "Gross Prem.", "GST", "Net Prem.", "OD Prem.", 
        "TP Prem.", "Agent Comm.% OD", "Agent OD Amount", "Agent TP Comm", "Agent TP Amount", 
        "Agent Comm.% Net", "Agent Net Amt", "Agent Bonus", "Agent Total Comm.", 
        "Franchise Comm.% OD", "Franchise OD Amount", "Franchise TP Comm", "Franchise Agent TP Amount", 
        "Franchise Agent Comm.% Net", "Franchise Agent Net Amt", "Franchise Bonus", "Franchise Total Comm.", 

        "Insurer Comm.% OD", "Insurer OD Amount", "Insurer TP Comm", "Insurer TP Amount", 
        "Insurer Comm.% Net", "Insurer Net Amt", "Insurer Bonus", "Insurer Total Comm.", 
        "Profit/Loss", "TDS %", "TDS Amount", "Net Profit"
    ]

    # Apply styling to header row (Blue background, White text)
    header_fill = PatternFill(start_color="0000FF", end_color="0000FF", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font

    # Default values (to be used when database fields are missing)
    default_values = [
        "-", "-", "-", "-", "-", "-", "-", "-", "-", 
        "-", "-", "-", "-", "-", 
        "-", "-", "-", "-", "-", "-", "-", 
        "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", 
        "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"
    ]

    # Fetch data from the database
    policies = PolicyDocument.objects.filter(status=1).all().order_by('-id')
    
    
    for policy in policies:
        # Convert policy dates to naive datetime (fix timezone issue)
        issue_date = datetime.datetime.strptime(policy.policy_start_date, "%Y-%m-%d").strftime("%m-%d-%Y") if isinstance(policy.policy_start_date, str) else policy.policy_start_date.strftime("%m-%d-%Y") if policy.policy_start_date else default_values[6]
        issue_year = policy.policy_start_date.strftime("%Y") if isinstance(policy.policy_start_date, datetime.datetime) else default_values[6]
        issue_month = policy.policy_start_date.strftime("%b-%Y") if isinstance(policy.policy_start_date, datetime.datetime) else default_values[6]
        risk_start_date = policy.start_date if policy.start_date else ""

        od_premium = float(policy.od_premium.replace(',', '')) if policy.od_premium else 0.0  
        tp_premium = float(policy.tp_premium.replace(',', '')) if policy.tp_premium else 0.0  
        net_premium = float(policy.policy_total_premium.replace(',', '')) if policy.policy_total_premium else 0.0   
        
        make_and_model = (
            (policy.vehicle_make if policy.vehicle_make else "-") + 
            "/" + 
            (policy.vehicle_model if policy.vehicle_model else "-")
        )

        commission = policy.commission()
        if commission:
            od_percentage = float(commission.od_percentage) if commission.od_percentage else 0
            tp_percentage = float(commission.tp_percentage) if commission.tp_percentage else 0
            net_percentage = float(commission.net_percentage) if commission.net_percentage else 0
        else:
            od_percentage = 0
            tp_percentage = 0
            net_percentage = 0
            
        
        od_commission_amount = (od_premium * od_percentage) / 100
        tp_commission_amount = (tp_premium * tp_percentage) / 100
        net_commission_amount = (net_premium * net_percentage) / 100
        total_commission = float(od_commission_amount + tp_commission_amount + net_commission_amount)
        
        # return HttpResponse(od_commission_amount , tp_commission_amount,net_commission_amount,total_commission)
        
        broker_commision = 25  # Insurer Commission Percentage
        # Convert policy premium to float, removing commas
        tp = float(policy.policy_premium.replace(',', '')) if policy.policy_premium else 0  
        # Calculate Profit/Loss
        profit_loss = (tp * (broker_commision / 100)) - (net_commission_amount)
        total_broker_commission = (tp * (broker_commision / 100))
        # Fill in data, using database values if available, otherwise defaults
        row_data = [
            issue_month if issue_month else default_values[0],  # Policy Month
            policy.rm_name if policy.rm_name else default_values[1],  # Agent Name
            default_values[2],  # SM Name
            default_values[3],  # Franchise Name
            settings.INSURER_NAME if settings.INSURER_NAME else default_values[4],  # Insurer Name
            default_values[5],  # S.P. Name
            issue_date if issue_date else default_values[6],  # Issue Date
            risk_start_date if risk_start_date else default_values[7],  # Risk Start Date
            'Confirmed',  # Payment Status
            policy.insurance_provider if policy.insurance_provider else default_values[9],  # Insurance Company
            policy.policy_type if policy.policy_type else default_values[10],  # Policy Type
            policy.policy_number if policy.policy_number else default_values[11],  # Policy No
            policy.holder_name if policy.holder_name else default_values[12],  # Insured Name
            policy.vehicle_type if policy.vehicle_type else default_values[13],  # Vehicle Type
            make_and_model if make_and_model else default_values[14],  # Vehicle Make/Model
            policy.vehicle_gross_weight if policy.vehicle_gross_weight else default_values[15],  # Gross Weight
            policy.vehicle_number if policy.vehicle_number else default_values[16],  # Reg. No.
            policy.vehicle_manuf_date if policy.vehicle_manuf_date.isdigit() and len(policy.vehicle_manuf_date) == 4 
            else datetime.datetime.strptime(policy.vehicle_manuf_date, "%d-%m-%Y").strftime("%Y") if policy.vehicle_manuf_date 
            else default_values[17],
            

           # MFG Year
            policy.sum_insured if policy.sum_insured else default_values[18],  # Sum Insured
            policy.policy_total_premium if policy.policy_total_premium else default_values[19],  # Gross Prem.
            policy.gst if policy.gst else default_values[20],  # GST
            policy.policy_premium if policy.policy_premium else default_values[21],  # Net Prem.
            policy.od_premium if policy.od_premium else default_values[22],  # OD Prem.
            policy.tp_premium if policy.tp_premium else default_values[23],  # TP Prem.
            
            od_percentage if  od_percentage  else  default_values[24],
            od_commission_amount if od_commission_amount  else  default_values[25],
            tp_percentage if  tp_percentage  else  default_values[26], 
            tp_commission_amount if tp_commission_amount  else  default_values[27],
            net_percentage if net_percentage else  default_values[28],
            net_commission_amount if net_commission_amount  else  default_values[29],
            0,
            total_commission if total_commission  else 0,
            None,None,None,None,None,None,None,None,
            0,0,0,0,
            broker_commision if broker_commision  else 0,
            0,0,total_broker_commission,
            profit_loss,
            0,0,
            profit_loss
            # default_values[29], default_values[29], default_values[30], default_values[31],
            # default_values[32], default_values[33], default_values[34], default_values[35],
            # default_values[36], default_values[37], default_values[38], default_values[39],
            # commission.od_percentage if commission.od_percentage else default_values[40], 
            # od_commission_amount if  od_commission_amount else default_values[41], 
            # commission.tp_percentage if commission.tp_percentage else default_values[42], 
            # tp_commission_amount if  tp_commission_amount else default_values[43],
            # commission.net_percentage if commission.net_percentage else default_values[44],
            # net_commission_amount if  net_commission_amount else default_values[45],
            # commission.tp_premium if commission.tp_premium else default_values[46],
            # commission.tp_premium if commission.tp_premium else default_values[47],
            # commission.tp_premium if commission.tp_premium else default_values[48], 
            # commission.tp_premium if commission.tp_premium else default_values[49], 
            # commission.tp_premium if commission.tp_premium else default_values[50], 
            # commission.tp_premium if commission.tp_premium else default_values[51],
        ]
        ws.append(row_data)

    # Create HTTP response for downloading
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="policy_data.xlsx"'

    # Save workbook to response
    wb.save(response)

    return response

def commission_report(request):
    # Get all PolicyDocuments ordered by id in descending order
    policies = PolicyDocument.objects.filter(status=1).all().order_by('-id')
    
    # Initialize a list to store the policies with calculated commission amounts
    policy_data = []
    
    for policy in policies:
        
        # Check if the policy has a valid commission and od_premium
        if policy:
            
                # Convert to float and print values for debugging
                od_premium = float(policy.od_premium.replace(',', '')) if policy.od_premium else 0.0  
                tp_premium = float(policy.tp_premium.replace(',', '')) if policy.tp_premium else 0.0  
                net_premium = float(policy.policy_total_premium.replace(',', '')) if policy.policy_total_premium else 0.0  


                commission = policy.commission()  # Get the associated commission instance
                if commission:
                    od_percentage = float(commission.od_percentage) if commission.od_percentage else 0
                    tp_percentage = float(commission.tp_percentage) if commission.tp_percentage else 0
                    net_percentage = float(commission.net_percentage) if commission.net_percentage else 0
                else:
                    od_percentage = 0
                    tp_percentage = 0
                    net_percentage = 0

                # Calculate the commission amounts
                od_commission_amount = (od_premium * od_percentage) / 100
                tp_commission_amount = (tp_premium * tp_percentage) / 100
                net_commission_amount = (net_premium * net_percentage) / 100

                

                # Print calculated commission amounts
                # print(f"OD Commission: {od_commission_amount}, TP Commission: {tp_commission_amount}, Net Commission: {net_commission_amount}")

                # Append the calculated commission amounts and policy details to the list
                policy_data.append({
                    'policy': policy,
                    'od_commission_amount': od_commission_amount,
                    'tp_commission_amount': tp_commission_amount,
                    'net_commission_amount': net_commission_amount
                })
           
        else:
            policy_data.append({
                'policy': policy,
                'od_commission_amount': None,
                'tp_commission_amount': None,
                'net_commission_amount': None
            })

    # Pass the calculated policy data to the template
    # return HttpResponse(policy_data)
    return render(request, 'commission_report.html', {'policy_data': policy_data})