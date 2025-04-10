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
    search_field = request.GET.get('search_field', '')  # Which field to search
    search_query = request.GET.get('search_query', '')  # Search value
    global_search = request.GET.get('global_search', '').strip()

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10  # Default to 10 if invalid value is given

    if request.user.role_id != 1:
        leads = Leads.objects.filter(created_by=request.user.id).order_by('-created_at')
    else:
        leads = Leads.objects.all().order_by('-created_at')


    if global_search:
        leads = leads.filter(
            Q(name_as_per_pan__icontains=global_search) |  # Search by name
            Q(email_address__icontains=global_search) |  # Search by email
            Q(mobile_number__icontains=global_search) |  # Search by mobile number
            Q(pan_card_number__icontains=global_search) |  # Search by PAN card number
            Q(state__icontains=global_search) |  # Search by state
            Q(city__icontains=global_search) |  # Search by city
            Q(lead_id__icontains=global_search)  # Search by city
        )

    # Apply filtering if search_field and search_query are provided
    if search_field and search_query:
        filter_args = {f"{search_field}__icontains": search_query}
        leads = leads.filter(**filter_args)

    if request.user.role_id != 1:
        total_leads = Leads.objects.filter(created_by=request.user.id).order_by('-created_at').count()
    else:
        total_leads = Leads.objects.all().order_by('-created_at').count()
    # Paginate results
    paginator = Paginator(leads, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'leads/index.html', {
        'page_obj': page_obj,
        'total_leads': total_leads,
        'per_page': per_page,
        'search_field': search_field,
        'search_query': search_query,
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




def create_or_edit_lead(request, lead_id=None):
    if not request.user.is_authenticated:
        return redirect('login')
    
    customers = QuotationCustomer.objects.all()
    
    lead = None
    if lead_id:
        lead = get_object_or_404(Leads, id=lead_id)
    
    if request.method == "GET":
        return render(request, 'leads/create.html', {'lead': lead, 'customers': customers})
    
    elif request.method == "POST":
        mobile_number = request.POST.get("mobile_number", "").strip()
        email_address = request.POST.get("email_address", "").strip()
        quote_date = request.POST.get("quote_date", None)
        name_as_per_pan = request.POST.get("name_as_per_pan", "").strip()
        pan_card_number = request.POST.get("pan_card_number", "").strip() or None
        date_of_birth = request.POST.get("date_of_birth", None)
        state = request.POST.get("state", "").strip()
        city = request.POST.get("city", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        address = request.POST.get("address", "").strip()
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
            lead.status = status
            lead.updated_at = now()
            lead.save()
            messages.success(request, f"Lead updated successfully! Lead ID: {lead.lead_id}")
        else:
            new_lead = Leads.objects.create(
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
                lead_type=lead_type,
                status=status,
                created_by=request.user.id,
                created_at=now(),
                updated_at=now()
            )
            messages.success(request, f"Lead created successfully!")
        
        return redirect("leads-mgt")