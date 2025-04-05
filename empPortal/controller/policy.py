from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users,Branch,PolicyInfo,PolicyDocument, DocumentUpload, PolicyVehicleInfo
from empPortal.model import BankDetails
from ..forms import DocumentUploadForm
from django.contrib.auth import authenticate, login ,logout
from django.core.files.storage import FileSystemStorage
import re
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

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.views.decorators.csrf import csrf_exempt
from pprint import pprint 
import pdfkit
from django.templatetags.static import static  # ✅ Import static
from django.template.loader import render_to_string

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()

# views.py
from django.http import JsonResponse
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
        policy.bqp = request.POST.get('father_name')
        policy.pos_name = request.POST.get('vehicle_owner_number')
        policy.branch_name = request.POST.get('registration_city')
        policy.supervisor_name = request.POST.get('vehicle_type')
        policy.policy_type = request.POST.get('policy_type')
        policy.policy_plan = request.POST.get('policy_duration')
        policy.sum_insured = request.POST.get('idv_value')
        policy.od_premium = request.POST.get('od_premium')
        policy.tp_premium = request.POST.get('tp_premium')
        policy.pa_count = request.POST.get('pa_count', '0')
        policy.pa_amount = request.POST.get('pa_amount', '0.00')
        policy.driver_count = request.POST.get('driver_count', '0')
        policy.driver_amount = request.POST.get('driver_amount', '0.00')

        policy.save()
        return redirect('edit-policy-vehicle-details', policy_no=quote(policy.policy_number))



def edit_vehicle_details(request, policy_no):
    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

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
        return redirect('edit-policy-docs', policy_no=quote(policy.policy_number))

    return render(request, 'policy/edit-policy-vehicle.html', {
        'policy': policy,
        'policy_data': policy_data,
        'vehicle': vehicle
    })


def edit_policy_docs(request, policy_no):
    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    if request.method == 'POST':
        
        return redirect('edit-agent-payment-info', policy_no=quote(policy.policy_number))
    

    return render(request, 'policy/edit-policy-docs.html', {
        'policy': policy,
        'policy_data': policy_data,
        'vehicle': vehicle
    })



def edit_agent_payment_info(request, policy_no):
    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    if request.method == 'POST':
        return redirect('edit-insurer-payment-info', policy_no=quote(policy.policy_number))


    return render(request, 'policy/edit-agent-payment-info.html', {
        'policy': policy,
        'policy_data': policy_data,
        'vehicle': vehicle
    })



def edit_insurer_payment_info(request, policy_no):
    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    if request.method == 'POST':
        return redirect('edit-franchise-payment-info', policy_no=quote(policy.policy_number))

    return render(request, 'policy/edit-insurer-payment-info.html', {
        'policy': policy,
        'policy_data': policy_data,
        'vehicle': vehicle
    })


def edit_franchise_payment_info(request, policy_no):
    policy = get_object_or_404(PolicyInfo, policy_number=policy_no)
    policy_data = PolicyDocument.objects.filter(policy_number=policy_no).first()

    try:
        vehicle = PolicyVehicleInfo.objects.get(policy_number=policy.policy_number)
    except PolicyVehicleInfo.DoesNotExist:
        vehicle = None

    if request.method == 'POST':
        return redirect('policy-data')

    return render(request, 'policy/edit-franchise-payment-info.html', {
        'policy': policy,
        'policy_data': policy_data,
        'vehicle': vehicle
    })