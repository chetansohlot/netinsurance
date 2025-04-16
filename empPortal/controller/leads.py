from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users, DocumentUpload, Branch, Leads, QuotationCustomer
from empPortal.model import BankDetails
from ..forms import DocumentUploadForm
from django.core.mail import send_mail
from django.core.mail import EmailMessage
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
import logging
logger = logging.getLogger(__name__)
import os
import pdfkit
from django.template.loader import render_to_string
from pprint import pprint 
from django.core.paginator import Paginator
from django.db.models import Q
from empPortal.model import Referral

import pandas as pd
from django.core.files.storage import default_storage
import openpyxl
from django.db.models import Max
import re

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')

    per_page = request.GET.get('per_page', 10)
    search_field = request.GET.get('search_field', '')
    search_query = request.GET.get('search_query', '')
    global_search = request.GET.get('global_search', '').strip()
    shorting = request.GET.get('shorting', '')  # Get sorting preference

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    # Base queryset
    if request.user.role_id != 1:
        leads = Leads.objects.filter(created_by=request.user.id)
    else:
        leads = Leads.objects.all()

    # Global search
    if global_search:
        leads = leads.filter(
            Q(name_as_per_pan__icontains=global_search) |
            Q(email_address__icontains=global_search) |
            Q(mobile_number__icontains=global_search) |
            Q(pan_card_number__icontains=global_search) |
            Q(state__icontains=global_search) |
            Q(city__icontains=global_search) |
            Q(lead_id__icontains=global_search)
        )

    # Field-specific search
    if search_field and search_query:
        filter_args = {f"{search_field}__icontains": search_query}
        leads = leads.filter(**filter_args)

    # Sorting
    if shorting == 'name_asc':
        leads = leads.order_by('name_as_per_pan')
    elif shorting == 'name_desc':
        leads = leads.order_by('-name_as_per_pan')
    elif shorting == 'recently_added':
        leads = leads.order_by('-created_at')
    elif shorting == 'recently_updated':
        leads = leads.order_by('-updated_at')
    else:
        leads = leads.order_by('-created_at')  # Default sort

    # Count
    total_leads = leads.count()

    # Pagination
    paginator = Paginator(leads, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'leads/index.html', {
        'page_obj': page_obj,
        'total_leads': total_leads,
        'per_page': per_page,
        'search_field': search_field,
        'search_query': search_query,
        'shorting': shorting,  # Pass to template to retain selected option
    })

    
def viewlead(request, lead_id):
    if request.user.is_authenticated:
        leads = Leads.objects.all()
        return render(request, 'leads/index.html', {'leads': leads})  # Pass leads to the template
    else:
        return redirect('login')
    
def healthLead(request):
    if request.user.is_authenticated:
        return render(request, 'leads/health-lead.html')
    else:
        return redirect('login')
    
def termlead(request):
    if request.user.is_authenticated:
        return render(request, 'leads/term-lead.html')
    else:
        return redirect('login')


from datetime import datetime

def create_or_edit_lead(request, lead_id=None):
    if not request.user.is_authenticated:
        return redirect('login')
    
    customers = QuotationCustomer.objects.all()
    lead = None
    referrals = Referral.objects.all()

    if lead_id:
        lead = get_object_or_404(Leads, id=lead_id)
    
    if request.method == "GET":
        return render(request, 'leads/create.html', {
            'lead': lead,
            'referrals': referrals,
            'customers': customers
        })

    elif request.method == "POST":
        mobile_number = request.POST.get("mobile_number", "").strip()
        email_address = request.POST.get("email_address", "").strip()
        quote_date = request.POST.get("quote_date", None)
        name_as_per_pan = request.POST.get("name_as_per_pan", "").strip()
        pan_card_number = request.POST.get("pan_card_number", "").strip() or None
        
        # ✅ Handle date_of_birth safely
        date_of_birth_str = request.POST.get("date_of_birth", "").strip()
        date_of_birth = None
        if date_of_birth_str:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format for Date of Birth. Please use YYYY-MM-DD.")
                return redirect(request.path)

        state = request.POST.get("state", "").strip()
        city = request.POST.get("city", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        address = request.POST.get("address", "").strip()
        lead_source = request.POST.get("lead_source", "").strip()
        referral_by = request.POST.get("referral_by", "").strip()
        if lead_source != 'referral_partner':
            referral_by = ''
        lead_description = request.POST.get("lead_description", "").strip()
        lead_type = request.POST.get("lead_type", "MOTOR").strip()
        status = request.POST.get("status", "new").strip()
        
        if lead:
            lead.mobile_number = mobile_number
            lead.email_address = email_address
            lead.quote_date = quote_date
            lead.name_as_per_pan = name_as_per_pan
            lead.pan_card_number = pan_card_number
            lead.date_of_birth = date_of_birth
            lead.state = state
            lead.city = city
            lead.pincode = pincode
            lead.address = address
            lead.lead_description = lead_description
            lead.lead_type = lead_type
            lead.lead_source = lead_source
            lead.referral_by = referral_by
            lead.status = status
            lead.updated_at = now()
            lead.save()
            messages.success(request, f"Lead updated successfully! Lead ID: {lead.lead_id}")
        else:
            Leads.objects.create(
                mobile_number=mobile_number,
                email_address=email_address,
                quote_date=quote_date,
                name_as_per_pan=name_as_per_pan,
                pan_card_number=pan_card_number,
                date_of_birth=date_of_birth,
                state=state,
                city=city,
                pincode=pincode,
                address=address,
                lead_description=lead_description,
                lead_source=lead_source,
                referral_by=referral_by,
                status=status,
                created_by=request.user.id,
                created_at=now(),
                updated_at=now()
            )
            messages.success(request, f"Lead created successfully!")

        return redirect("leads-mgt")

def bulk_upload_leads(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')

        if not excel_file:
            messages.error(request, "Please select a file to upload.")
            return redirect('bulk-upload-leads')

        if not excel_file.name.endswith('.xlsx'):
            messages.error(request, "Only .xlsx files are supported.")
            return redirect('leads-mgt')

        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active

            # Get latest lead_id once before loop
            latest_lead = Leads.objects.aggregate(Max('lead_id'))['lead_id__max']
            start_num = 1

            if latest_lead:
                match = re.search(r'L(\d+)', latest_lead)
                if match:
                    start_num = int(match.group(1)) + 1

            inserted = 0

            for index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if len(row) < 13:
                    messages.warning(request, f"Row {index} skipped due to missing data.")
                    continue

                try:
                    lead_id = f"L{start_num:05d}"  # Generate like L00001
                    start_num += 1  # Increment for next

                    Leads.objects.create(
                        lead_id=lead_id,
                        mobile_number=row[0],
                        email_address=row[1],
                        quote_date=row[2],
                        name_as_per_pan=row[3],
                        pan_card_number=row[4],
                        date_of_birth=row[5],
                        state=row[6],
                        city=row[7],
                        pincode=row[8],
                        lead_source=row[9],
                        address=row[10],
                        lead_description=row[11],
                        lead_type=row[12],
                    )
                    inserted += 1

                except Exception as row_error:
                    messages.warning(request, f"Error in row {index}: {row_error}")

            messages.success(request, f"{inserted} leads uploaded successfully.")
            return redirect('leads-mgt')

        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            return redirect('leads-mgt')

    return render(request, 'leads/bulk_upload.html')