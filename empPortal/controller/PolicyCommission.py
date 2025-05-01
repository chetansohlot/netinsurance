from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users, PolicyUploadDoc,Branch,PolicyInfo,PolicyDocument, DocumentUpload, FranchisePayment, InsurerPaymentDetails, PolicyVehicleInfo, AgentPaymentDetails, UploadedExcel, UploadedZip
from ..models import BulkPolicyLog,ExtractedFile, BqpMaster
from empPortal.model import Referral
from empPortal.model import CommissionUpdateLog
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
from empPortal.model import Partner

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

    user = request.user
    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if user.role_id != 1 and str(user.department_id) not in ["3", "5"]:
        filters_q &= Q(rm_id=user.id)

    # branch_id, referral_id = get_branch_referral_ids(
    #     request.GET.get('branch_name', ''),
    #     request.GET.get('referred_by', '')
    # )
    branch_id   = request.GET.get('branch_name', '')
    referral_id = request.GET.get('referred_by', '')
    if branch_id:
        filters_q &= Q(policy_info__branch_name=str(branch_id))
    if referral_id:
        filters_q &= Q(policy_agent_info__referral_id=str(referral_id))

    exclude_q = Q(policy_agent_info__isnull=False) | Q(policy_agent_info__agent_od_comm__isnull=False) | \
                Q(policy_agent_info__agent_net_comm__isnull=False) | Q(policy_agent_info__agent_tp_comm__isnull=False) | \
                Q(policy_agent_info__agent_incentive_amount__isnull=False) | Q(policy_agent_info__agent_tds__isnull=False)

    base_qs = PolicyDocument.objects.filter(filters_q).exclude(exclude_q)
    filters_dict = get_common_filters(request)
    filtered = apply_policy_filters(base_qs, filters_dict)

    base_count_qs = PolicyDocument.objects.filter(filters_q)
    policy_count = base_count_qs.exclude(exclude_q).count()
    policy_total_count = base_count_qs.count()

    page_obj, per_page = paginate_queryset(filtered, request)
    branches = Branch.objects.all().order_by('branch_name')
    referrals = Referral.objects.all().order_by('name')
    bqpList = BqpMaster.objects.all().order_by('bqp_fname')
    partners = Partner.objects.all().order_by('name')

    return render(request, 'policy-commission/agent-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "policy_total_count": policy_total_count,
        "per_page": per_page,
        'filters': filters_dict,
        'branches': branches,
        'referrals': referrals,
        'bqpList': bqpList,
        'partners': partners,
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

        
        # Log the update
        log_commission_update(
            commission_type='agent',
            policy_id=policy_id,
            policy_number=policy_number,
            updated_by_id=request.user.id,
            updated_from='agent-commission',
            data={
                'agent_od_comm': obj.agent_od_comm,
                'agent_net_comm': obj.agent_net_comm,
                'agent_tp_comm': obj.agent_tp_comm,
                'agent_incentive_amount': obj.agent_incentive_amount,
                'agent_tds': obj.agent_tds,
            }
        )
        messages.success(request, "Agent Commission Updated successfully!")

    return redirect('agent-commission')

def franchisees_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    base_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if user.role_id != 1 and str(user.department_id) not in ["3", "5"]:
        base_q &= Q(rm_id=user.id)

    branch_id, referral_id = get_branch_referral_ids(
        request.GET.get('branch_name', ''),
        request.GET.get('referred_by', '')
    )
    if branch_id:
        base_q &= Q(policy_info__branch_name=str(branch_id))
    if referral_id:
        base_q &= Q(policy_agent_info__referral_id=str(referral_id))

    exclude_q = Q(policy_franchise_info__isnull=False) | Q(policy_franchise_info__franchise_od_comm__isnull=False) | \
                Q(policy_franchise_info__franchise_net_comm__isnull=False) | Q(policy_franchise_info__franchise_tp_comm__isnull=False) | \
                Q(policy_franchise_info__franchise_incentive_amount__isnull=False) | Q(policy_franchise_info__franchise_tds__isnull=False)

    base_queryset = PolicyDocument.objects.filter(base_q).exclude(exclude_q)
    filters = get_common_filters(request)
    filtered_policies = apply_policy_filters(base_queryset, filters)

    total_base_q = Q(status=6)
    if user.role_id != 1 and str(user.department_id) not in ["3", "5"]:
        total_base_q &= Q(rm_id=user.id)

    policy_total_count = PolicyDocument.objects.filter(total_base_q).count()
    policy_count = PolicyDocument.objects.filter(total_base_q).exclude(exclude_q).count()

    page_obj, per_page = paginate_queryset(filtered_policies, request)

    branches = Branch.objects.all().order_by('branch_name')
    referrals = Referral.objects.all().order_by('name')
    bqpList = BqpMaster.objects.all().order_by('bqp_fname')
    partners = Partner.objects.all().order_by('name')

    return render(request, 'policy-commission/franchisees-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "policy_total_count": policy_total_count,
        "per_page": per_page,
        "branches": branches,
        "referrals": referrals,
        "bqpList": bqpList,
        "bqpList": bqpList,
        "partners": partners,
        "filtered_policy_ids": [obj.id for obj in filtered_policies],
        "filtered_count": len(filtered_policies),
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

        
        log_commission_update(
            commission_type='franchise',
            policy_id=policy_id,
            policy_number=policy_number,
            updated_by_id=request.user.id,
            updated_from='franchise-commission',
            data={
                'franchise_od_comm': obj.franchise_od_comm,
                'franchise_net_comm': obj.franchise_net_comm,
                'franchise_tp_comm': obj.franchise_tp_comm,
                'franchise_incentive_amount': obj.franchise_incentive_amount,
                'franchise_tds': obj.franchise_tds,
            }
        )

        messages.success(request, "Franchise Commission Updated successfully!")

    return redirect('franchisees-commission')


def insurer_commission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if user.role_id != 1 and str(user.department_id) not in ["3", "5"]:
        filters_q &= Q(rm_id=user.id)

    branch_id, referral_id = get_branch_referral_ids(
        request.GET.get('branch_name', ''),
        request.GET.get('referred_by', '')
    )
    if branch_id:
        filters_q &= Q(policy_info__branch_name=str(branch_id))
    if referral_id:
        filters_q &= Q(policy_agent_info__referral_id=str(referral_id))

    exclude_q = Q(policy_insurer_info__isnull=False) | Q(policy_insurer_info__insurer_od_comm__isnull=False) | \
                Q(policy_insurer_info__insurer_net_comm__isnull=False) | Q(policy_insurer_info__insurer_tp_comm__isnull=False) | \
                Q(policy_insurer_info__insurer_incentive_amount__isnull=False) | Q(policy_insurer_info__insurer_tds__isnull=False)

    base_qs = PolicyDocument.objects.filter(filters_q).exclude(exclude_q)
    filters = get_common_filters(request)
    filtered = apply_policy_filters(base_qs, filters)

    base_q = Q(status=6)
    if user.role_id != 1 and str(user.department_id) not in ["3", "5"]:
        base_q &= Q(rm_id=user.id)

    policy_total_count = PolicyDocument.objects.filter(base_q).count()
    policy_count = PolicyDocument.objects.filter(base_q).exclude(exclude_q).count()

    page_obj, per_page = paginate_queryset(filtered, request)

    branches = Branch.objects.all().order_by('branch_name')
    referrals = Referral.objects.all().order_by('name')
    bqpList = BqpMaster.objects.all().order_by('bqp_fname')
    partners = Partner.objects.all().order_by('name')

    return render(request, 'policy-commission/insurer-commission.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "policy_total_count": policy_total_count,
        "per_page": per_page,
        "branches": branches,
        "referrals": referrals,
        "bqpList": bqpList,
        'filters': filters,
        'partners': partners,
        'filtered_policy_ids': [obj.id for obj in filtered],
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

        
        log_commission_update(
            commission_type='insurer',
            policy_id=policy_id,
            policy_number=policy_number,
            updated_by_id=request.user.id,
            updated_from='insurer-commission',
            data={
                'insurer_od_comm': obj.insurer_od_comm,
                'insurer_net_comm': obj.insurer_net_comm,
                'insurer_tp_comm': obj.insurer_tp_comm,
                'insurer_incentive_amount': obj.insurer_incentive_amount,
                'insurer_tds': obj.insurer_tds,
            }
        )
        messages.success(request, "Insurer Commission Updated successfully!")

    return redirect('insurer-commission')


def log_commission_update(commission_type, policy_id, policy_number, updated_by_id, updated_from, data):
    CommissionUpdateLog.objects.create(
        commission_type=commission_type,
        policy_id=policy_id,
        policy_number=policy_number,
        updated_by_id=updated_by_id,
        updated_from=updated_from,
        updated_data=data,
    )

from django.db.models import Q
from datetime import datetime
import json

def get_filter_conditions(filters):
    """
    Generate Q object conditions and post-filter lambdas for fields stored in extracted_text JSON.
    """
    db_filters = Q()
    json_filters = []

    for key, val in filters.items():
        if not val:
            continue
        val = val.strip().lower()

        if key in ['policy_number', 'vehicle_number', 'vehicle_type',
                   'policy_holder_name', 'insurance_provider']:
            field_map = {
                'policy_number': 'policy_number__icontains',
                'vehicle_number': 'vehicle_number__icontains',
                'vehicle_type': 'vehicle_type__iexact',
                'policy_holder_name': 'holder_name__icontains',
                'insurance_provider': 'insurance_provider__icontains',
            }
            db_filters &= Q(**{field_map[key]: val})

        elif key in ['insurance_company', 'mobile_number', 'engine_number', 'chassis_number', 'fuel_type']:
            json_filters.append(lambda data, k=key, v=val: v in data.get(k, '').lower())

        elif key == 'gvw_from':
            try:
                val = int(val)
                json_filters.append(lambda data, v=val: int(data.get('gvw', '0')) >= v)
            except ValueError:
                continue

        elif key in ['manufacturing_year_from', 'manufacturing_year_to']:
            try:
                year = int(val)
                if key.endswith('from'):
                    json_filters.append(lambda data, y=year: int(data.get('manufacturing_year', '0')) >= y)
                else:
                    json_filters.append(lambda data, y=year: int(data.get('manufacturing_year', '0')) <= y)
            except ValueError:
                continue

        elif key == 'start_date':
            try:
                dt = datetime.strptime(val, '%Y-%m-%d').date()
                db_filters &= Q(created_at__date__gte=dt)
            except ValueError:
                continue

        elif key == 'end_date':
            try:
                dt = datetime.strptime(val, '%Y-%m-%d').date()
                db_filters &= Q(created_at__date__lte=dt)
            except ValueError:
                continue

    return db_filters, json_filters


def apply_policy_filters(queryset, filters):
    db_q, json_conditions = get_filter_conditions(filters)
    filtered_qs = queryset.filter(db_q)

    final_list = []
    for obj in filtered_qs:
        try:
            data = obj.extracted_text if isinstance(obj.extracted_text, dict) else json.loads(obj.extracted_text or '{}')
        except Exception:
            continue

        if all(cond(data) for cond in json_conditions):
            obj.json_data = data
            final_list.append(obj)

    return final_list

def get_branch_referral_ids(branch_name, referred_by):
    branch_id = Branch.objects.filter(branch_name__iexact=branch_name).values_list('id', flat=True).first()
    referral_id = Referral.objects.filter(name__iexact=referred_by).values_list('id', flat=True).first()
    return branch_id, referral_id

def get_common_filters(request):
    return {
        key: request.GET.get(key, '').strip() for key in [
            'policy_number', 'policy_type', 'vehicle_number', 'engine_number', 'chassis_number',
            'vehicle_type', 'policy_holder_name', 'mobile_number',
            'insurance_provider', 'insurance_company', 'start_date',
            'end_date', 'manufacturing_year_from', 'manufacturing_year_to',
            'fuel_type', 'gvw_from', 'gvw_to', 'branch_name', 'referred_by', 'pos_name', 'bqp'
        ]
    }

def paginate_queryset(queryset, request, per_page_default=10):
    per_page = request.GET.get('per_page', per_page_default)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = per_page_default
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page')), per_page