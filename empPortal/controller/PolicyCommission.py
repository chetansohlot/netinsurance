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
        
from empPortal.model import Referral
     
def agent_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')
    print("helldfdfo 234")

    user_id = request.user.id
    role_id = Users.objects.filter(id=user_id).values_list('role_id', flat=True).first()

    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if role_id != 1 and str(request.user.department_id) != "5" and str(request.user.department_id) != "3":
        filters_q &= Q(rm_id=user_id)

    branch_name = request.GET.get('branch_name', '').strip()
    referred_by = request.GET.get('referred_by', '').strip()

    branch = Branch.objects.filter(branch_name__iexact=branch_name).first()
    referral = Referral.objects.filter(name__iexact=referred_by).first()

    if branch:
        filters_q &= Q(policy_info__branch_name=str(branch.id))

    if referral:
        filters_q &= Q(policy_agent_info__referral_id=str(referral.id))
            
    exclude_q = Q(
        policy_agent_info__agent_od_comm__isnull=True
    ) | Q(
        policy_agent_info__agent_net_comm__isnull=True
    ) | Q(
        policy_agent_info__agent_tp_comm__isnull=True
    ) | Q(
        policy_agent_info__agent_incentive_amount__isnull=True
    ) | Q(
        policy_agent_info__agent_tds__isnull=True
    )
    print("hello 23sfdfdf4")

    base_qs = PolicyDocument.objects.filter(filters_q).exclude(exclude_q).order_by('-id')

    base_qs = base_qs.only(
        'id', 'policy_number', 'vehicle_number', 'holder_name', 
        'insurance_provider', 'extracted_text', 'vehicle_type'
    )

    # Applying filters
    filters = {
        'policy_number': request.GET.get('policy_number', '').strip().lower(),
        'branch_name': request.GET.get('branch_name', '').strip().lower(),
        'referred_by': request.GET.get('referred_by', '').strip().lower(),
        'vehicle_number': request.GET.get('vehicle_number', '').strip().lower(),
        'engine_number': request.GET.get('engine_number', '').strip().lower(),
        'chassis_number': request.GET.get('chassis_number', '').strip().lower(),
        'vehicle_type': request.GET.get('vehicle_type', '').strip().lower(),
        'policy_holder_name': request.GET.get('policy_holder_name', '').strip().lower(),
        'mobile_number': request.GET.get('mobile_number', '').strip().lower(),
        'insurance_provider': request.GET.get('insurance_provider', '').strip().lower(),
        'insurance_company': request.GET.get('insurance_company', '').strip().lower(),
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

            # Add filter conditions here as before

            if match:
                obj.json_data = data
                filtered.append(obj)
    else:
        filtered = []  # no filter, empty

    # Additional count filter by role and department if needed
    if role_id != 1 and str(request.user.department_id) != "5" and str(request.user.department_id) != "3":
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
    print("hello 234")
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
        messages.success(request, "Agent Commission Updated successfully!")

    return redirect('agent-commission')

def franchisees_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user_id = request.user.id
    role_id = Users.objects.filter(id=user_id).values_list('role_id', flat=True).first()

    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if role_id != 1 and str(request.user.department_id) != "5":
        filters_q &= Q(rm_id=user_id)


    branch_name = request.GET.get('branch_name', '').strip()
    referred_by = request.GET.get('referred_by', '').strip()

    branch = Branch.objects.filter(branch_name__iexact=branch_name).first()
    referral = Referral.objects.filter(name__iexact=referred_by).first()

    if branch:
        filters_q &= Q(policy_info__branch_name=str(branch.id))

    if referral:
        filters_q &= Q(policy_agent_info__referral_id=str(referral.id))

    exclude_q = Q(
        policy_franchise_info__franchise_od_comm__isnull=False
    ) | Q(
        policy_franchise_info__franchise_net_comm__isnull=False
    ) | Q(
        policy_franchise_info__franchise_tp_comm__isnull=False
    ) | Q(
        policy_franchise_info__franchise_incentive_amount__isnull=False
    ) | Q(
        policy_franchise_info__franchise_tds__isnull=False
    ) | Q(
        policy_franchise_info__isnull=False
    )
   
    base_qs = PolicyDocument.objects.filter(filters_q).exclude(exclude_q).order_by('-id')

    # Only load required fields (optimization)
    base_qs = base_qs.only(
        'id', 'policy_number', 'vehicle_number', 'holder_name', 
        'insurance_provider', 'extracted_text', 'vehicle_type'
    )

    filters = {
        'policy_number': request.GET.get('policy_number', '').strip().lower(),
        'branch_name': request.GET.get('branch_name', '').strip().lower(),
        'referred_by': request.GET.get('referred_by', '').strip().lower(),
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

    return render(request, 'policy-commission/franchisees-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "per_page": per_page,
        'filters': {k: request.GET.get(k, '') for k in filters},
        'filtered_policy_ids': [obj.id for obj in filtered],
        'filtered_count': len(filtered),
    })


def update_franchise_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    policy_ids_str = request.POST.get('policy_ids', '')
    policy_ids = [int(id.strip()) for id in policy_ids_str.split(',') if id.strip().isdigit()]

    if not policy_ids:
        return redirect('franchise-commission')

    policies = PolicyDocument.objects.filter(id__in=policy_ids).only('id', 'policy_number')

    # Create a dictionary mapping policy IDs to policy numbers
    policy_map = {policy.id: policy.policy_number for policy in policies}

    for policy_id in policy_ids:
        policy_number = policy_map.get(policy_id)
        if not policy_number:
            continue  # Skip if policy not found

        # Get or create the FranchisePayment object for this policy
        obj, created = FranchisePayment.objects.get_or_create(
            policy_id=policy_id, defaults={'policy_number': policy_number}
        )

        if not created:
            # If already exists, also update the policy_number (in case it was missing before)
            obj.policy_number = policy_number

        # Update the fields from the form data
        obj.franchise_od_comm = request.POST.get('franchise_od_commission')
        obj.franchise_net_comm = request.POST.get('franchise_net_commission')
        obj.franchise_tp_comm = request.POST.get('franchise_tp_commission')
        obj.franchise_incentive_amount = request.POST.get('franchise_incentive_amount')
        obj.franchise_tds = request.POST.get('franchise_tds')
        obj.updated_by = request.user

        # Calculate the amounts based on the commissions
        try:
            obj.franchise_od_amount = float(obj.franchise_od_comm) if obj.franchise_od_comm else 0
            obj.franchise_net_amount = float(obj.franchise_net_comm) if obj.franchise_net_comm else 0
            obj.franchise_tp_amount = float(obj.franchise_tp_comm) if obj.franchise_tp_comm else 0
            obj.franchise_total_comm_amount = obj.franchise_od_amount + obj.franchise_net_amount + obj.franchise_tp_amount
            obj.franchise_net_payable_amount = obj.franchise_total_comm_amount - (float(obj.franchise_tds) if obj.franchise_tds else 0)
            obj.franchise_tds_amount = float(obj.franchise_tds) if obj.franchise_tds else 0
        except ValueError:
            # Handle any invalid values that might cause errors when converting to float
            pass

        # Save the updated franchise payment
        obj.save()
        messages.success(request, "Franchise Commission Updated successfully!")

    return redirect('franchisees-commission')

def insurer_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user_id = request.user.id
    role_id = Users.objects.filter(id=user_id).values_list('role_id', flat=True).first()

    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if role_id != 1 and str(request.user.department_id) != "5":
        filters_q &= Q(rm_id=user_id)

    branch_name = request.GET.get('branch_name', '').strip()
    referred_by = request.GET.get('referred_by', '').strip()

    branch = Branch.objects.filter(branch_name__iexact=branch_name).first()
    referral = Referral.objects.filter(name__iexact=referred_by).first()

    if branch:
        filters_q &= Q(policy_info__branch_name=str(branch.id))

    if referral:
        filters_q &= Q(policy_agent_info__referral_id=str(referral.id))
        
    exclude_q = Q(
        policy_insurer_info__insurer_od_comm__isnull=False
    ) | Q(
        policy_insurer_info__insurer_net_comm__isnull=False
    ) | Q(
        policy_insurer_info__insurer_tp_comm__isnull=False
    ) | Q(
        policy_insurer_info__insurer_incentive_amount__isnull=False
    ) | Q(
        policy_insurer_info__insurer_tds__isnull=False
    ) | Q(
        policy_insurer_info__isnull=False
    )



    base_qs = PolicyDocument.objects.filter(filters_q).exclude(exclude_q).order_by('-id')
    print(str(base_qs.query))
    # Only load required fields (optimization)
    base_qs = base_qs.only(
        'id', 'policy_number', 'vehicle_number', 'holder_name', 
        'insurance_provider', 'extracted_text', 'vehicle_type'
    )

    filters = {
        'policy_number': request.GET.get('policy_number', '').strip().lower(),
        'branch_name': request.GET.get('branch_name', '').strip().lower(),
        'referred_by': request.GET.get('referred_by', '').strip().lower(),
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

    # Get the count of policies
    if role_id != 1 and str(request.user.department_id) != "5":
        policy_count = PolicyDocument.objects.filter(status=6, rm_id=user_id).count()
    else:
        policy_count = PolicyDocument.objects.filter(status=6).count()

    # Pagination logic
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    paginator = Paginator(filtered, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Extract filtered policy IDs to pass to the template
    filtered_policy_ids = [obj.id for obj in filtered]

    return render(request, 'policy-commission/insurer-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "per_page": per_page,
        'filters': {k: request.GET.get(k, '') for k in filters},
        'filtered_policy_ids': filtered_policy_ids,  # Correctly passing filtered_policy_ids
        'filtered_count': len(filtered),
    })



def update_insurer_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    policy_ids_str = request.POST.get('policy_ids', '')
    policy_ids = [int(id.strip()) for id in policy_ids_str.split(',') if id.strip().isdigit()]

    if not policy_ids:
        return redirect('insurer-commission')

    policies = PolicyDocument.objects.filter(id__in=policy_ids).only('id', 'policy_number')

    # Create a dictionary mapping policy IDs to policy numbers
    policy_map = {policy.id: policy.policy_number for policy in policies}

    for policy_id in policy_ids:
        policy_number = policy_map.get(policy_id)
        if not policy_number:
            continue  # Skip if policy not found

        # Get or create the InsurerPaymentDetails object for this policy
        obj, created = InsurerPaymentDetails.objects.get_or_create(
            policy_id=policy_id, defaults={'policy_number': policy_number}
        )

        if not created:
            obj.policy_number = policy_number  # Update if exists

        # Update fields from the form
        obj.insurer_od_comm = request.POST.get('insurer_od_commission')
        obj.insurer_net_comm = request.POST.get('insurer_net_commission')
        obj.insurer_tp_comm = request.POST.get('insurer_tp_commission')
        obj.insurer_incentive_amount = request.POST.get('insurer_incentive_amount')
        obj.insurer_tds = request.POST.get('insurer_tds')
        obj.updated_by = request.user

        # Calculate amounts based on commissions
        try:
            obj.insurer_od_amount = str(float(obj.insurer_od_comm) if obj.insurer_od_comm else 0)
            obj.insurer_net_amount = str(float(obj.insurer_net_comm) if obj.insurer_net_comm else 0)
            obj.insurer_tp_amount = str(float(obj.insurer_tp_comm) if obj.insurer_tp_comm else 0)
            obj.insurer_total_comm_amount = str(float(obj.insurer_od_amount) + float(obj.insurer_net_amount) + float(obj.insurer_tp_amount))
            obj.insurer_net_payable_amount = str(float(obj.insurer_total_comm_amount) - (float(obj.insurer_tds) if obj.insurer_tds else 0))
            obj.insurer_tds_amount = str(float(obj.insurer_tds) if obj.insurer_tds else 0)
        except ValueError:
            pass

        obj.save()
        messages.success(request, "Insurer Commission Updated successfully!")

    return redirect('insurer-commission')