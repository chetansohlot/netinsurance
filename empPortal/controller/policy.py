from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users, PolicyUploadDoc,Branch,PolicyInfo,PolicyDocument, DocumentUpload, FranchisePayment, InsurerPaymentDetails, PolicyVehicleInfo, AgentPaymentDetails, UploadedExcel
from empPortal.model import Referral

from empPortal.model import BankDetails
from ..forms import DocumentUploadForm
from django.contrib.auth import authenticate, login ,logout
from django.core.files.storage import FileSystemStorage
import re,openpyxl
from django.db import IntegrityError
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
from urllib.parse import quote
from urllib.parse import urljoin
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from urllib.parse import unquote
from django.views.decorators.csrf import csrf_exempt
from pprint import pprint 
import pdfkit, logging
from django.templatetags.static import static  # ✅ Import static
from django.template.loader import render_to_string
from django_q.tasks import async_task
import pandas as pd
from collections import Counter

logger = logging.getLogger(__name__)
OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()

# views.py
from ..utils import send_sms_post
from datetime import datetime

def parse_date(date_str):
    try:
        # Try parsing with common datetime format first
        parsed = datetime.strptime(date_str, "%b. %d, %Y, %I:%M %p")
        return parsed.date()
    except ValueError:
        try:
            # Try ISO format fallback
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None  # You can handle invalid dates as needed
        

def edit_policy(request, policy_id):

    if request.method == 'POST':
        policy_number = request.POST.get('policy_number')

        # Try to find another policy with the same number
        policy = PolicyInfo.objects.filter(
            policy_number=policy_number
        ).first()

        if policy:
            policy = policy
        else:
            policy = PolicyInfo()


        # Basic Policy
        policy.policy_number = policy_number
        policy.policy_issue_date = request.POST.get('policy_issue_date')
        policy.policy_start_date = request.POST.get('policy_start_date')
        policy.policy_expiry_date = request.POST.get('policy_expiry_date')

        # Insured Details
        policy.insurer_name = request.POST.get('owner_name')
        policy.insured_mobile = request.POST.get('insured_mobile')
        policy.insured_email = request.POST.get('insured_email')
        policy.insured_address = request.POST.get('insured_address')
        policy.insured_pan = request.POST.get('insured_pan')
        policy.insured_aadhaar = request.POST.get('insured_aadhaar')

        # Policy Details
        policy.insurance_company = request.POST.get('insurance_company')
        policy.service_provider = request.POST.get('location')
        policy.insurer_contact_name = request.POST.get('owner_name')
        # policy.bqp = request.POST.get('father_name')
        # policy.pos_name = request.POST.get('vehicle_owner_number')
        policy.branch_name = request.POST.get('registration_city')
        policy.supervisor_name = request.POST.get('supervisor_name')
        policy.policy_type = request.POST.get('policy_type')
        policy.policy_plan = request.POST.get('policy_duration')
        policy.sum_insured = request.POST.get('idv_value')
        policy.od_premium = request.POST.get('od_premium')
        policy.tp_premium = request.POST.get('tp_premium')
        policy.pa_count = request.POST.get('pa_count', '0')
        policy.pa_amount = request.POST.get('pa_amount', '0.00')
        policy.driver_count = request.POST.get('driver_count', '0')
        policy.driver_amount = request.POST.get('driver_amount', '0.00')
        # policy.referral_by = request.POST.get('referral_by')
        policy.fuel_type = request.POST.get('fuel_type')
        policy.be_fuel_amount = request.POST.get('be_fuel_amount')
        policy.gross_premium = request.POST.get('gross_premium')
        policy.net_premium = request.POST.get('net_premium')

        policy.save()
        messages.success(request, "Policy Updated successfully!")

        return redirect('edit-policy-vehicle-details', policy_no=quote(policy.policy_number, safe=''))



def edit_vehicle_details(request, policy_no):
    
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    decoded_policy_no = unquote(policy_no)

    policy = get_object_or_404(PolicyInfo, policy_number=decoded_policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=decoded_policy_no).first()
    
    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    if request.method == 'POST':
        if not vehicle:
            vehicle = PolicyVehicleInfo(policy_number=policy.policy_number)

        vehicle.vehicle_type = request.POST.get('vehicle_type')
        vehicle.vehicle_make = request.POST.get('vehicle_make')
        vehicle.vehicle_model = request.POST.get('vehicle_model')
        vehicle.vehicle_variant = request.POST.get('vehicle_variant')
        vehicle.fuel_type = request.POST.get('fuel_type')
        vehicle.gvw = request.POST.get('gvw')
        vehicle.cubic_capacity = request.POST.get('cubic_capacity')
        vehicle.seating_capacity = request.POST.get('seating_capacity')
        vehicle.registration_number = request.POST.get('vehicle_reg_no')
        vehicle.engine_number = request.POST.get('engine_number')
        vehicle.chassis_number = request.POST.get('chassis_number')
        vehicle.manufacture_year = request.POST.get('mgf_year')

        vehicle.save()
        messages.success(request, "Policy Vehicle details Updated successfully!")

        return redirect('edit-policy-docs', policy_no=quote(policy.policy_number, safe=''))

    pdf_path = get_pdf_path(request, policy_data.filepath)

    extracted_data = {}
    if policy_data and policy_data.extracted_text:
        if isinstance(policy_data.extracted_text, str):
            try:
                extracted_data = json.loads(policy_data.extracted_text)
            except json.JSONDecodeError:
                extracted_data = {}
        elif isinstance(policy_data.extracted_text, dict):
            extracted_data = policy_data.extracted_text  # already a dict

    return render(request, 'policy/edit-policy-vehicle.html', {
        'policy': policy,
        'policy_data': policy_data,
        'pdf_path': pdf_path,
        'extracted_data': extracted_data,
        'vehicle': vehicle
    })



def get_pdf_path(request, filepath):
    """
    Returns the absolute URI to the PDF file if it exists, otherwise an empty string.
    """
    if not filepath:
        return ""

    filepath_str = str(filepath).replace('\\', '/')
    rel_path = ""
    
    if 'media/' in filepath_str:
        rel_path = filepath_str.split('media/')[-1]
        absolute_file_path = os.path.join(settings.MEDIA_ROOT, rel_path)

        if not os.path.exists(absolute_file_path):
            # Try fallback inside empPortal/media
            fallback_path = os.path.join(settings.BASE_DIR, 'empPortal', 'media', rel_path)
            if os.path.exists(fallback_path):
                absolute_file_path = fallback_path
            else:
                rel_path = ""  # File not found in either location

        if rel_path:
            media_url_path = urljoin(settings.MEDIA_URL, rel_path.replace('\\', '/'))
            return request.build_absolute_uri(media_url_path)

    return ""



def edit_policy_docs(request, policy_no):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    policy_no = unquote(policy_no)

    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    try:
        doc_data = PolicyUploadDoc.objects.get(policy_number=policy_no)
    except PolicyUploadDoc.DoesNotExist:
        doc_data = PolicyUploadDoc(policy_number=policy_no)

    # AJAX file upload
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        field_name = request.POST.get('field_name')

        if field_name and field_name in request.FILES:
            try:
                setattr(doc_data, field_name, request.FILES[field_name])
                doc_data.active = True
                doc_data.save()

                messages.success(request, "Doc Uploaded successfully!")

                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': False, 'error': 'Invalid file field'})

    # Standard GET
    pdf_path = get_pdf_path(request, policy_data.filepath if policy_data else None)

    return render(request, 'policy/edit-policy-docs.html', {
        'policy': policy,
        'policy_data': policy_data,
        'pdf_path': pdf_path,
        'vehicle': vehicle,
        'doc_data': doc_data
    })


def edit_agent_payment_info(request, policy_no):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    policy_no = unquote(policy_no)

    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()
    referrals = Referral.objects.all()
     
    try:
        agent_payment = AgentPaymentDetails.objects.get(policy_number=policy.policy_number)
    except AgentPaymentDetails.DoesNotExist:
        agent_payment = AgentPaymentDetails(policy_number=policy.policy_number)

    if request.method == 'POST':
        # agent_payment.agent_name = request.POST.get('agent_name')
        agent_payment.agent_name = request.POST.get('referral_by')
        agent_payment.agent_payment_mod = request.POST.get('agent_payment_mod')
        agent_payment.transaction_id = request.POST.get('transaction_id')
        agent_payment.agent_payment_date = request.POST.get('agent_payment_date')
        agent_payment.agent_amount = request.POST.get('agent_amount')
        agent_payment.agent_remarks = request.POST.get('agent_remarks')
        agent_payment.agent_od_comm = request.POST.get('agent_od_comm')
        agent_payment.agent_tp_comm = request.POST.get('agent_tp_comm')
        agent_payment.agent_net_comm = request.POST.get('agent_net_comm')
        agent_payment.agent_incentive_amount = request.POST.get('agent_incentive_amount')
        agent_payment.agent_tds = request.POST.get('agent_tds')
        agent_payment.agent_od_amount = request.POST.get('agent_od_amount')
        agent_payment.agent_net_amount = request.POST.get('agent_net_amount')
        agent_payment.agent_tp_amount = request.POST.get('agent_tp_amount')
        agent_payment.agent_total_comm_amount = request.POST.get('agent_total_comm_amount')
        agent_payment.agent_net_payable_amount = request.POST.get('agent_net_payable_amount')
        agent_payment.agent_tds_amount = request.POST.get('agent_tds_amount')

        agent_payment.save()
        
        policy.bqp = request.POST.get('bqp')
        policy.pos_name = request.POST.get('pos_name')
        policy.referral_by = request.POST.get('referral_by')
        policy.save()
        messages.success(request, "Policy Agent Payment Updated successfully!")

        return redirect('edit-insurer-payment-info', policy_no=quote(policy.policy_number))

    pdf_path = get_pdf_path(request, policy_data.filepath)

    return render(request, 'policy/edit-agent-payment-info.html', {
        'policy': policy,
        'pdf_path': pdf_path,
        'policy_data': policy_data,
        'agent_payment': agent_payment,
        'referrals':referrals
    })



def edit_insurer_payment_info(request, policy_no):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    policy_no = unquote(policy_no)

    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    try:
        insurer_payment = InsurerPaymentDetails.objects.get(policy_number=policy.policy_number)
    except InsurerPaymentDetails.DoesNotExist:
        insurer_payment = InsurerPaymentDetails(policy_number=policy.policy_number)

    if request.method == 'POST':
        insurer_payment.insurer_payment_mode = request.POST.get('insurer_payment_mode')
        insurer_payment.insurer_payment_date = request.POST.get('insurer_payment_date')
        insurer_payment.insurer_amount = request.POST.get('insurer_amount')
        insurer_payment.insurer_remarks = request.POST.get('insurer_remarks')

        insurer_payment.insurer_od_comm = request.POST.get('insurer_od_comm')
        insurer_payment.insurer_od_amount = request.POST.get('insurer_od_amount')

        insurer_payment.insurer_tp_comm = request.POST.get('insurer_tp_comm')
        insurer_payment.insurer_tp_amount = request.POST.get('insurer_tp_amount')

        insurer_payment.insurer_net_comm = request.POST.get('insurer_net_comm')
        insurer_payment.insurer_net_amount = request.POST.get('insurer_net_amount')
        
        insurer_payment.insurer_tds = request.POST.get('insurer_tds')
        insurer_payment.insurer_tds_amount = request.POST.get('insurer_tds_amount')
        
        insurer_payment.insurer_incentive_amount = request.POST.get('insurer_incentive_amount')
        insurer_payment.insurer_total_comm_amount = request.POST.get('insurer_total_comm_amount')
        insurer_payment.insurer_net_payable_amount = request.POST.get('insurer_net_payable_amount')
        
        insurer_payment.insurer_total_commission = request.POST.get('insurer_total_commission')
        insurer_payment.insurer_receive_amount = request.POST.get('insurer_receive_amount')
        insurer_payment.insurer_balance_amount = request.POST.get('insurer_balance_amount')

        insurer_payment.active = '1'
        insurer_payment.save()

        messages.success(request, "Insurer Payment details updated successfully!")
        return redirect('edit-franchise-payment-info', policy_no=quote(policy.policy_number))

    pdf_path = get_pdf_path(request, policy_data.filepath)

    return render(request, 'policy/edit-insurer-payment-info.html', {
        'policy': policy,
        'policy_data': policy_data,
        'pdf_path': pdf_path,
        'vehicle': vehicle,
        'insurer_payment': insurer_payment
    })




def edit_franchise_payment_info(request, policy_no):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    policy_no = unquote(policy_no)

    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    try:
        franchise_payment = FranchisePayment.objects.get(policy_number=policy.policy_number)
    except FranchisePayment.DoesNotExist:
        franchise_payment = FranchisePayment(policy_number=policy.policy_number)

    if request.method == 'POST':
        franchise_payment.franchise_od_comm = request.POST.get('franchise_od_comm')
        franchise_payment.franchise_net_comm = request.POST.get('franchise_net_comm')
        franchise_payment.franchise_tp_comm = request.POST.get('franchise_tp_comm')
        franchise_payment.franchise_incentive_amount = request.POST.get('franchise_incentive_amount')
        franchise_payment.franchise_tds = request.POST.get('franchise_tds')

        franchise_payment.franchise_od_amount = request.POST.get('franchise_od_amount')
        franchise_payment.franchise_net_amount = request.POST.get('franchise_net_amount')
        franchise_payment.franchise_tp_amount = request.POST.get('franchise_tp_amount')
        franchise_payment.franchise_total_comm_amount = request.POST.get('franchise_total_comm_amount')
        franchise_payment.franchise_net_payable_amount = request.POST.get('franchise_net_payable_amount')
        franchise_payment.franchise_tds_amount = request.POST.get('franchise_tds_amount')

        franchise_payment.active = True
        franchise_payment.save()

        messages.success(request, "Franchise Payment details updated successfully!")
        return redirect('policy-data')

    pdf_path = get_pdf_path(request, policy_data.filepath)

    return render(request, 'policy/edit-franchise-payment-info.html', {
        'policy': policy,
        'policy_data': policy_data,
        'pdf_path': pdf_path,
        'vehicle': vehicle,
        'franchise_payment': franchise_payment
    })
    
def editBulkPolicy(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    return render(request,'policy/edit-bulk-policy.html')
    
def updateBulkPolicy(request):
    if not request.user.is_authenticated or request.user.is_active != 1:
        messages.error(request,'Please Login First')
        return redirect('login')
    
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        camp_name = request.POST.get("camp_name")

        # Validate Excel file format
        if not file.name.lower().endswith(".xlsx"):
            messages.error(request, "Invalid file format. Only .xlsx files are allowed.")
            return redirect("edit-bulk-policy")

        # Validate size
        if file.size > 5 * 1024 * 1024:
            messages.error(request, "File too large. Maximum allowed size is 5 MB.")
            return redirect("edit-bulk-policy")

        if not camp_name:
            messages.error(request, "Campaign Name is mandatory.")
            return redirect("edit-bulk-policy")

        try:
            wb = openpyxl.load_workbook(file, data_only=True)
            sheet = wb.active
            total_rows = sheet.max_row - 1
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {str(e)}")
            return redirect("edit-bulk-policy")

        # Save the file to model
        excelInstance = UploadedExcel.objects.create(
            file=file,
            campaign_name=camp_name,
            created_by=request.user,
            total_rows=total_rows
        )
         # Optionally: Trigger background task
        async_task('empPortal.tasks.updateBulkPolicies', excelInstance.id)

        messages.success(request, "Excel uploaded successfully. Processing started in background.")
        return redirect("edit-bulk-policy")

    return redirect("edit-bulk-policy")

def viewBulkUpdates(request):
    if not request.user.is_authenticated or request.user.is_active != 1:
        messages.error(request,'Please Login First')
        return redirect('login')
    
    id  = request.user.id
    
    # Fetch policies
    role_id = Users.objects.filter(id=id,status=1).values_list('role_id', flat=True).first()
    if role_id != 1:
        logs =  UploadedExcel.objects.filter(rm_id=id).exclude(rm_id__isnull=True).order_by('-id')
    else:
        logs = UploadedExcel.objects.all().order_by('-id')
    
    policy_files = PolicyDocument.objects.all()
    statuses = Counter(file.status for file in policy_files)

    # Ensure all statuses are included in the count, even if they're 0
    status_counts = {
        0: statuses.get(0, 0),
        1: statuses.get(1, 0),
        2: statuses.get(2, 0),
        3: statuses.get(3, 0),
        4: statuses.get(4, 0),
        5: statuses.get(5, 0),
        6: statuses.get(6, 0),
        7: statuses.get(7, 0),
    }

    return render(request,'policy/bulk-edit-logs.html',{
        'logs': logs,
        'status_counts': status_counts,
        'total_files': len(policy_files)
    })
        
