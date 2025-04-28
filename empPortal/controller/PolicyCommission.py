from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users, PolicyUploadDoc,Branch,PolicyInfo,PolicyDocument, DocumentUpload, FranchisePayment, InsurerPaymentDetails, PolicyVehicleInfo, AgentPaymentDetails, UploadedExcel, UploadedZip
from ..models import BulkPolicyLog,ExtractedFile, BqpMaster
from empPortal.model import Referral
from django.db.models import Q

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
from django.templatetags.static import static 
from django.template.loader import render_to_string
from django_q.tasks import async_task
import pandas as pd
from collections import Counter
from io import BytesIO
from ..utils import getUserNameByUserId, policy_product
logging.getLogger('faker').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
OPENAI_API_KEY = settings.OPENAI_API_KEY
from django.core.paginator import Paginator

from django.db.models import Q, F, Value
from django.db.models.functions import Lower
import json
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
     

def agent_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user_id = request.user.id
    role_id = Users.objects.filter(id=user_id).values_list('role_id', flat=True).first()

    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if role_id != 1 and str(request.user.department_id) != "5":
        filters_q &= Q(rm_id=user_id)

    # Exclude policies having agent payment
    base_qs = PolicyDocument.objects.filter(filters_q).exclude(
        policy_agent_info__isnull=False
    ).order_by('-id')

    # Only load required fields (optimization)
    base_qs = base_qs.only(
        'id', 'policy_number', 'vehicle_number', 'holder_name', 
        'insurance_provider', 'extracted_text', 'vehicle_type'
    )

    filters = {
        'policy_number': request.GET.get('policy_number', '').strip().lower(),
        'vehicle_number': request.GET.get('vehicle_number', '').strip().lower(),
        'engine_number': request.GET.get('engine_number', '').strip().lower(),
        'chassis_number': request.GET.get('chassis_number', '').strip().lower(),
        'vehicle_type': request.GET.get('vehicle_type', '').strip().lower(),
        'policy_holder_name': request.GET.get('policy_holder_name', '').strip().lower(),
        'mobile_number': request.GET.get('mobile_number', '').strip().lower(),
        'insurance_provider': request.GET.get('insurance_provider', '').strip().lower(),
        'start_date': request.GET.get('start_date', '').strip(),
        'end_date': request.GET.get('end_date', '').strip(),
        'manufacturing_year_from': request.GET.get('manufacturing_year_from', '').strip(),
        'manufacturing_year_to': request.GET.get('manufacturing_year_to', '').strip(),
        'fuel_type': request.GET.get('fuel_type', '').strip().lower(),
        'gvw_from': request.GET.get('gvw_from', '').strip(),
    }

    any_filter_applied = any(value for key, value in filters.items() if key not in ['start_date', 'end_date', 'manufacturing_year_from', 'manufacturing_year_to', 'gvw_from'])

    filtered = []

    if any_filter_applied:
        for obj in base_qs:
            data = obj.extracted_text or {}
            if not isinstance(data, dict):
                try:
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    continue

            if not data:
                continue

            match = True

            if filters['policy_number'] and filters['policy_number'] not in data.get('policy_number', '').lower():
                match = False
            if filters['vehicle_number'] and filters['vehicle_number'] not in data.get('vehicle_number', '').lower():
                match = False
            if filters['engine_number'] and filters['engine_number'] not in str(data.get('vehicle_details', {}).get('engine_number', '')).lower():
                match = False
            if filters['chassis_number'] and filters['chassis_number'] not in str(data.get('vehicle_details', {}).get('chassis_number', '')).lower():
                match = False
            if filters['vehicle_type'] and filters['vehicle_type'] not in str(data.get('vehicle_details', {}).get('vehicle_type', '')).lower():
                match = False
            if filters['policy_holder_name'] and filters['policy_holder_name'] not in data.get('insured_name', '').lower():
                match = False
            if filters['mobile_number'] and filters['mobile_number'] not in str(data.get('contact_information', {}).get('phone_number', '')).lower():
                match = False
            if filters['insurance_provider'] and filters['insurance_provider'] not in data.get('insurance_company', '').lower():
                match = False

            # Add more conditions here for date and range filters

            if match:
                obj.json_data = data
                filtered.append(obj)
    else:
        filtered = []  # no filter, empty

    if role_id != 1 and str(request.user.department_id) != "5":
        policy_count = PolicyDocument.objects.filter(status=6, rm_id=user_id).count()
    else:
        policy_count = PolicyDocument.objects.filter(status=6).count()

    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    paginator = Paginator(filtered, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'policy-commission/agent-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "per_page": per_page,
        'filters': {k: request.GET.get(k, '') for k in filters},
        'filtered_policy_ids': [obj.id for obj in filtered],
        'filtered_count': len(filtered),
    })

def update_agent_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    policy_ids_str = request.POST.get('policy_ids', '')
    policy_ids = [int(id.strip()) for id in policy_ids_str.split(',') if id.strip().isdigit()]

    if not policy_ids:
        return redirect('agent-commission')

    policies = PolicyDocument.objects.filter(id__in=policy_ids).only('id', 'policy_number')

    policy_map = {policy.id: policy.policy_number for policy in policies}

    for policy_id in policy_ids:
        policy_number = policy_map.get(policy_id)
        if not policy_number:
            continue  # Skip if policy not found

        obj, created = AgentPaymentDetails.objects.get_or_create(policy_id=policy_id, defaults={'policy_number': policy_number})

        if not created:
            # If already exists, also update the policy_number (in case it was missing before)
            obj.policy_number = policy_number

        obj.agent_od_comm = request.POST.get('agent_od_commission')
        obj.agent_net_comm = request.POST.get('agent_net_commission')
        obj.agent_tp_comm = request.POST.get('agent_tp_commission')
        obj.agent_incentive_amount = request.POST.get('agent_incentive_amount')
        obj.agent_tds = request.POST.get('agent_tds')
        obj.updated_by = request.user
        obj.save()

    return redirect('agent-commission')




    
def franchisees_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.id
    role_id = Users.objects.filter(id=user_id).values_list('role_id', flat=True).first()

    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')
    if role_id != 1 and request.user.department_id != "5":
        filters_q &= Q(rm_id=user_id)
        
    base_qs = PolicyDocument.objects.filter(filters_q).order_by('-id').prefetch_related(
        'policy_agent_info', 'policy_franchise_info', 'policy_insurer_info'
    )
    
    def get_nested(data, path, default=''):
        for key in path:
            data = data.get(key) if isinstance(data, dict) else default
        return str(data).lower()



    filters = {
        'policy_number':      request.GET.get('policy_number', '').strip().lower(),
        'vehicle_number':     request.GET.get('vehicle_number', '').strip().lower(),
        'engine_number':      request.GET.get('engine_number', '').strip().lower(),
        'chassis_number':     request.GET.get('chassis_number', '').strip().lower(),
        'vehicle_type':       request.GET.get('vehicle_type', '').strip().lower(),
        'policy_holder_name':      request.GET.get('policy_holder_name', '').strip().lower(),      # maps to "Customer Name"
        'mobile_number':      request.GET.get('mobile_number', '').strip().lower(),      # maps to "Mobile Number"
        'insurance_provider': request.GET.get('insurance_provider', '').strip().lower(), # maps to "Insurance Provider"
    }

    filtered = []
    for obj in base_qs:
        raw = obj.extracted_text
        data = {}
        
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
        elif isinstance(raw, dict):
            data = raw
    
        if not data:
            continue

        if filters['policy_number'] and filters['policy_number'] not in data.get('policy_number', '').lower():
            continue
        if filters['vehicle_number'] and filters['vehicle_number'] not in data.get('vehicle_number', '').lower():
            continue
        if filters['engine_number'] and filters['engine_number'] not in get_nested(data, ['vehicle_details', 'engine_number']).lower():
            continue
        if filters['chassis_number'] and filters['chassis_number'] not in get_nested(data, ['vehicle_details', 'chassis_number']).lower():
            continue
        if filters['vehicle_type'] and filters['vehicle_type'] not in get_nested(data, ['vehicle_details', 'vehicle_type']).lower():
            continue
        if filters['policy_holder_name'] and filters['policy_holder_name'] not in data.get('insured_name', '').lower():
            continue
        if filters['mobile_number'] and filters['mobile_number'] not in data.get('contact_information', {}).get('phone_number', '').lower():
            continue
        if filters['insurance_provider'] and filters['insurance_provider'] not in data.get('insurance_company', '').lower():
            continue   

        obj.json_data = data    # attach parsed dict for the template
        filtered.append(obj)

    if role_id != 1 and request.user.department_id != "5":
        policy_count = PolicyDocument.objects.filter(status=6, rm_id=user_id).count()
    else:
        policy_count = PolicyDocument.objects.filter(status=6).count()

    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    paginator = Paginator(filtered, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'policy-commission/franchisees-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "per_page": per_page,
        'filters': {k: request.GET.get(k,'') for k in filters}
    })


    
def insurer_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.id
    role_id = Users.objects.filter(id=user_id).values_list('role_id', flat=True).first()

    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')
    if role_id != 1 and request.user.department_id != "5":
        filters_q &= Q(rm_id=user_id)
        
    base_qs = PolicyDocument.objects.filter(filters_q).order_by('-id').prefetch_related(
        'policy_agent_info', 'policy_franchise_info', 'policy_insurer_info'
    )
    
    def get_nested(data, path, default=''):
        for key in path:
            data = data.get(key) if isinstance(data, dict) else default
        return str(data).lower()



    filters = {
        'policy_number':      request.GET.get('policy_number', '').strip().lower(),
        'vehicle_number':     request.GET.get('vehicle_number', '').strip().lower(),
        'engine_number':      request.GET.get('engine_number', '').strip().lower(),
        'chassis_number':     request.GET.get('chassis_number', '').strip().lower(),
        'vehicle_type':       request.GET.get('vehicle_type', '').strip().lower(),
        'policy_holder_name':      request.GET.get('policy_holder_name', '').strip().lower(),      # maps to "Customer Name"
        'mobile_number':      request.GET.get('mobile_number', '').strip().lower(),      # maps to "Mobile Number"
        'insurance_provider': request.GET.get('insurance_provider', '').strip().lower(), # maps to "Insurance Provider"
    }

    filtered = []
    for obj in base_qs:
        raw = obj.extracted_text
        data = {}
        
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
        elif isinstance(raw, dict):
            data = raw
    
        if not data:
            continue

        if filters['policy_number'] and filters['policy_number'] not in data.get('policy_number', '').lower():
            continue
        if filters['vehicle_number'] and filters['vehicle_number'] not in data.get('vehicle_number', '').lower():
            continue
        if filters['engine_number'] and filters['engine_number'] not in get_nested(data, ['vehicle_details', 'engine_number']).lower():
            continue
        if filters['chassis_number'] and filters['chassis_number'] not in get_nested(data, ['vehicle_details', 'chassis_number']).lower():
            continue
        if filters['vehicle_type'] and filters['vehicle_type'] not in get_nested(data, ['vehicle_details', 'vehicle_type']).lower():
            continue
        if filters['policy_holder_name'] and filters['policy_holder_name'] not in data.get('insured_name', '').lower():
            continue
        if filters['mobile_number'] and filters['mobile_number'] not in data.get('contact_information', {}).get('phone_number', '').lower():
            continue
        if filters['insurance_provider'] and filters['insurance_provider'] not in data.get('insurance_company', '').lower():
            continue   

        obj.json_data = data    # attach parsed dict for the template
        filtered.append(obj)

    if role_id != 1 and request.user.department_id != "5":
        policy_count = PolicyDocument.objects.filter(status=6, rm_id=user_id).count()
    else:
        policy_count = PolicyDocument.objects.filter(status=6).count()

    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    paginator = Paginator(filtered, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'policy-commission/insurer-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "per_page": per_page,
        'filters': {k: request.GET.get(k,'') for k in filters}
    })




# REMOVE BELOW ALL FUNCTION AFTER COMPLETION OF Commission

def edit_policy(request, policy_id):

    if request.method == 'POST':
        policy_id = request.POST.get('policy_id')
        policy_number = request.POST.get('policy_number')

        # Try to find another policy with the same number
        policy = PolicyInfo.objects.filter(
            policy_number=policy_number,policy_id=policy_id
        ).first()

        if policy:
            pass
        else:
            policy = PolicyInfo()
            policy.policy_id = policy_id

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
        policy.gst_premium = request.POST.get('gst_premium')

        policy.save()
        messages.success(request, "Policy Updated successfully!")

        return redirect('edit-policy-vehicle-details', policy_no=quote(policy.policy_number, safe=''))


def none_if_blank(value):
    return value if value and value.strip() else None

def edit_vehicle_details(request, policy_no):
    
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    decoded_policy_no = unquote(policy_no)
    # policy = get_object_or_404(PolicyInfo, policy_number=decoded_policy_no)
    policy = PolicyInfo.objects.filter(policy_number=decoded_policy_no).first()
    if not policy:
        return redirect('policy-data')
    
    policy_data = PolicyDocument.objects.filter(policy_number=decoded_policy_no).first()
    vehicle = None
    
    
    # try:
    #     vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    # except PolicyVehicleInfo.DoesNotExist:
    #     vehicle = None

    if request.method == 'POST':
        policy_id = request.POST.get('policy_id')
        
        vehicle = PolicyVehicleInfo.objects.filter(policy_number=policy.policy_number, policy_id=policy_id).first()
        if not vehicle:
            vehicle = PolicyVehicleInfo(policy_number=policy.policy_number, policy_id=policy_id)

        vehicle.vehicle_type = none_if_blank(request.POST.get('vehicle_type'))
        vehicle.vehicle_make = none_if_blank(request.POST.get('vehicle_make'))
        vehicle.vehicle_model = none_if_blank(request.POST.get('vehicle_model'))
        vehicle.vehicle_variant = none_if_blank(request.POST.get('vehicle_variant'))
        vehicle.fuel_type = none_if_blank(request.POST.get('fuel_type'))
        vehicle.gvw = none_if_blank(request.POST.get('gvw'))
        vehicle.cubic_capacity = none_if_blank(request.POST.get('cubic_capacity'))
        vehicle.seating_capacity = none_if_blank(request.POST.get('seating_capacity'))
        vehicle.registration_number = none_if_blank(request.POST.get('vehicle_reg_no'))
        vehicle.engine_number = none_if_blank(request.POST.get('engine_number'))
        vehicle.chassis_number = none_if_blank(request.POST.get('chassis_number'))
        vehicle.manufacture_year = none_if_blank(request.POST.get('mgf_year'))
        vehicle.save()
        messages.success(request, "Policy Vehicle details Updated successfully!")

        return redirect('edit-policy-docs', policy_no=quote(policy.policy_number, safe=''))

    # pdf_path = get_pdf_path(request, policy_data.filepath)    
    pdf_path = get_pdf_path(request, policy_data.filepath if policy_data else None)

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

    policy = PolicyInfo.objects.filter(policy_number=policy_no).first()
    # policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    if not policy:
        return redirect('policy-data')
    
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()
    referrals = Referral.objects.all()
    bqps = BqpMaster.objects.all()
    agent_payment = AgentPaymentDetails.objects.filter(policy_number=policy.policy_number).last()
    
    if request.method == 'POST':
        policy_id =  request.POST.get('policy_id')
        agent_payment = AgentPaymentDetails.objects.filter(policy_number=policy.policy_number,policy_id=policy_id).first()
        
        if not agent_payment:
            agent_payment = AgentPaymentDetails(policy_number=policy.policy_number,policy_id=policy_id)
        
        # agent_payment.agent_name = request.POST.get('agent_name')
        agent_payment.agent_name = request.POST.get('referral_by',None)
        agent_payment.referral_id = request.POST.get('referral_by',None)
        agent_payment.agent_payment_mod = request.POST.get('agent_payment_mod',None)
        agent_payment.transaction_id = request.POST.get('transaction_id',None)
        agent_payment.agent_payment_date = request.POST.get('agent_payment_date',None)
        agent_payment.agent_amount = request.POST.get('agent_amount',None)
        agent_payment.agent_remarks = request.POST.get('agent_remarks',None)
        agent_payment.agent_od_comm = request.POST.get('agent_od_comm',None)
        agent_payment.agent_tp_comm = request.POST.get('agent_tp_comm',None)
        agent_payment.agent_net_comm = request.POST.get('agent_net_comm',None)
        agent_payment.agent_incentive_amount = request.POST.get('agent_incentive_amount',None)
        agent_payment.agent_tds = request.POST.get('agent_tds',None)
        agent_payment.agent_od_amount = request.POST.get('agent_od_amount',None)
        agent_payment.agent_net_amount = request.POST.get('agent_net_amount',None)
        agent_payment.agent_tp_amount = request.POST.get('agent_tp_amount',None)
        agent_payment.agent_total_comm_amount = request.POST.get('agent_total_comm_amount',None)
        agent_payment.agent_net_payable_amount = request.POST.get('agent_net_payable_amount',None)
        agent_payment.agent_tds_amount = request.POST.get('agent_tds_amount',None)
        agent_payment.updated_by = request.user
        agent_payment.save()
        
    
        
        policy.bqp_id = request.POST.get('bqp',None)
        policy.pos_name = request.POST.get('pos_name',None)
        policy.referral_by = request.POST.get('referral_by',None)
        policy.save()
        messages.success(request, "Policy Agent Payment Updated successfully!")

        return redirect('edit-insurer-payment-info', policy_no=quote(policy.policy_number))

    pdf_path = get_pdf_path(request, policy_data.filepath)

    return render(request, 'policy/edit-agent-payment-info.html', {
        'policy': policy,
        'pdf_path': pdf_path,
        'policy_data': policy_data,
        'agent_payment': agent_payment,
        'bqps': bqps,
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

    insurer_payment = InsurerPaymentDetails.objects.filter(policy_number=policy.policy_number).last()
    
    if request.method == 'POST':
        policy_id =  request.POST.get('policy_id')
        
        try:
            insurer_payment = InsurerPaymentDetails.objects.filter(policy_number=policy.policy_number,policy_id=policy_id).first()
        except InsurerPaymentDetails.DoesNotExist:
            insurer_payment = InsurerPaymentDetails(policy_number=policy.policy_number,policy_id=policy_id)

        insurer_payment.insurer_payment_mode = request.POST.get('insurer_payment_mode',None)
        insurer_payment.insurer_payment_date = request.POST.get('insurer_payment_date',None)
        insurer_payment.insurer_amount = request.POST.get('insurer_amount',None)
        insurer_payment.insurer_remarks = request.POST.get('insurer_remarks',None)

        insurer_payment.insurer_od_comm = request.POST.get('insurer_od_comm',None)
        insurer_payment.insurer_od_amount = request.POST.get('insurer_od_amount',None)

        insurer_payment.insurer_tp_comm = request.POST.get('insurer_tp_comm',None)
        insurer_payment.insurer_tp_amount = request.POST.get('insurer_tp_amount',None)

        insurer_payment.insurer_net_comm = request.POST.get('insurer_net_comm',None)
        insurer_payment.insurer_net_amount = request.POST.get('insurer_net_amount',None)
        
        insurer_payment.insurer_tds = request.POST.get('insurer_tds',None)
        insurer_payment.insurer_tds_amount = request.POST.get('insurer_tds_amount',None)
        
        insurer_payment.insurer_incentive_amount = request.POST.get('insurer_incentive_amount',None)
        insurer_payment.insurer_total_comm_amount = request.POST.get('insurer_total_comm_amount',None)
        insurer_payment.insurer_net_payable_amount = request.POST.get('insurer_net_payable_amount',None)
        
        insurer_payment.insurer_total_commission = request.POST.get('insurer_total_commission',None)
        insurer_payment.insurer_receive_amount = request.POST.get('insurer_receive_amount',None)
        insurer_payment.insurer_balance_amount = request.POST.get('insurer_balance_amount',None)

        insurer_payment.active = '1'
        insurer_payment.updated_by = request.user
        
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

    franchise_payment = FranchisePayment.objects.filter(policy_number=policy.policy_number).last()
    
    if request.method == 'POST':
        policy_id =  request.POST.get('policy_id')
        try:
            franchise_payment = FranchisePayment.objects.filter(policy_number=policy.policy_number,policy_id=policy_id).first()
        except FranchisePayment.DoesNotExist:
            franchise_payment = FranchisePayment(policy_number=policy.policy_number,policy_id=policy_id)

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
        franchise_payment.updated_by = request.user
        
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
        
def bulkPolicyMgt(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        return redirect('login')
    rms = Users.objects.all()
    product_types = policy_product()
    return render(request,'policy/bulk-policy-mgt.html',{'users':rms,'product_types':product_types})

def bulkBrowsePolicy(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            if request.FILES.get("zip_file"):
                zip_file = request.FILES["zip_file"]
            else:
                zip_file = None
            camp_name = request.POST.get("camp_name")
            rm_id = request.POST.get("rm_id")
            product_type = request.POST.get("product_type")
            # Validate ZIP file format
            if not zip_file or not zip_file.name.lower().endswith(".zip"):
                messages.error(request, "Invalid file format. Only ZIP files are allowed.")
            else:
                if zip_file.size > 50 * 1024 * 1024:
                    messages.error(request, "File too large. Maximum allowed size is 50 MB.")
                else:
                    try:
                        zip_bytes = BytesIO(zip_file.read())
                        with zipfile.ZipFile(zip_bytes) as zf:
                            file_list = zf.infolist()
                            
                            root_files = [f for f in file_list if not f.is_dir() and "/" not in f.filename and "\\" not in f.filename]
                            
                            total_files = len(root_files)
                            pdf_files = [f for f in root_files if f.filename.lower().endswith(".pdf")]
                            non_pdf_files = [f for f in root_files if not f.filename.lower().endswith(".pdf")]
                            
                            directories = [f for f in root_files if f.is_dir()]
                            pdf_count = len(pdf_files)
                            non_pdf_count = len(non_pdf_files)
                            
                            if directories:
                                messages.error(request, "ZIP must not contain any folders.")
                                for folder in directories:
                                    messages.error(request, f" - Folder: {folder.filename}")
                            if total_files > 50:
                                messages.error(request, "ZIP contains more than 50 files.")
                            if non_pdf_files:
                                messages.error(request, "ZIP must contain only PDF files.")
                    except zipfile.BadZipFile:
                        messages.error(request, "The uploaded ZIP file is corrupted or invalid.")
            if not camp_name:
                messages.error(request, "Campaign Name is mandatory.")
            if not product_type:
                messages.error(request, "Product Type is mandatory.")
            if messages.get_messages(request):
                return redirect('bulk-policy-mgt')
            rm_name = getUserNameByUserId(rm_id) if rm_id else None
            bulk_log_instance = BulkPolicyLog.objects.create(
                file=ContentFile(zip_bytes.getvalue(), name=zip_file.name),
                camp_name=camp_name,
                rm_id=rm_id,
                rm_name=rm_name,
                created_by=request.user,
                count_total_files=total_files,
                count_pdf_files=0,
                count_not_pdf=0,
                count_error_pdf_files=0,
                count_error_process_pdf_files=0,
                count_uploaded_files=0,
                count_duplicate_files=0,
                product_type=product_type,
                status=1
            )
            
            bulk_log_instance.file.save(zip_file.name, ContentFile(zip_bytes.getvalue()))
            bulk_log_instance.save()
            
            messages.success(request, "ZIP uploaded successfully. Processing started in background.")
            return redirect("bulk-upload-logs")
        else:
            return redirect("bulk-policy-mgt")
    else:
        return redirect('login')






def bulkPolicyView(request, id):
    if not request.user.is_authenticated or request.user.is_active != 1:
        return redirect('login')

    # Fetch policy documents based on bulk_log_id
    policy_files = ExtractedFile.objects.filter(bulk_log_ref_id=id)
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

    return render(request, 'policy/policy-files.html', {
        'files': policy_files,
        'total_files': len(policy_files),
        'log_id': id,
        'status_counts': status_counts
    })


def bulkUploadLogs(request):
    if not request.user.is_authenticated or request.user.is_active != 1:
        messages.error(request,'Please Login First')
        return redirect('login')
    
    id  = request.user.id
        # Fetch policies
    role_id = Users.objects.filter(id=id,status=1).values_list('role_id', flat=True).first()
    if role_id != 1:
     logs =  BulkPolicyLog.objects.filter(rm_id=id).exclude(rm_id__isnull=True).order_by('-id')
    else:
      logs = BulkPolicyLog.objects.all().order_by('-id')
    
    policy_files = ExtractedFile.objects.all()
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

    return render(request,'policy/bulk-upload-logs.html',{
        'logs': logs,
        'status_counts': status_counts,
        'total_files': len(policy_files)
    })
