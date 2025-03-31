import builtins
from pprint import pprint
import requests
from django.conf import settings
from datetime import datetime
from django.utils.timezone import now
from django.db import models, connection
import pytz
IST = pytz.timezone("Asia/Kolkata")

from django.shortcuts import render,redirect, get_object_or_404
from .models import Commission, Users, QuotationCustomer, Leads, VehicleInfo, QuotationVehicleDetail
from django.contrib import messages
from django.urls import reverse

ist_now = now().astimezone(IST)

def dd(*args):
    """Dump and Debug - Prints values but does NOT stop execution."""
    for arg in args:
        pprint(arg)  # Pretty print the data
    return  # Remove sys.exit()

# Register `dd()` globally
builtins.dd = dd

def send_sms_post(number, message):
    """
    Sends an SMS using the POST method.

    :param number: Phone number as a string.
    :param message: The SMS content.
    :return: API response in JSON format.
    """
    url = "http://sms.myoperator.biz/V2/http-api-post.php"

    payload = {
        "apikey": settings.MYOPERATOR_API_KEY,
        "senderid": settings.MYOPERATOR_SENDER_ID,
        "number": number,
        "message": message,
        "format": "json",
    }

    response = requests.post(url, json=payload)

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return {"error": "Invalid response", "response_text": response.text}

class LogType(models.TextChoices):
    INFO = "INFO", "Info"
    WARNING = "WARNING", "Warning"
    ERROR = "ERROR", "Error"
    DEBUG = "DEBUG", "Debug"
    AUDIT = "AUDIT", "Audit"
    SECURITY = "SECURITY", "Security"
    OTHER = "OTHER", "Other"




def create_or_update_lead(request, cus_id):
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch existing vehicle info
    vehicle_info = VehicleInfo.objects.filter(customer_id=cus_id).first()
    if not vehicle_info:
        messages.error(request, "Vehicle information not found for this customer.")
        return redirect(reverse("create-vehicle-info", args=[cus_id]))

    # Fetch customer details
    customer = get_object_or_404(QuotationCustomer, customer_id=cus_id)

    # Check if a lead already exists with the same mobile number
    existing_lead = Leads.objects.filter(mobile_number=customer.mobile_number).first()

    # Prepare the data to store
    lead_data = {
        'customer_id': customer.customer_id,
        'mobile_number': customer.mobile_number,
        'email_address': customer.email_address,
        'quote_date': customer.quote_date,
        'name_as_per_pan': customer.name_as_per_pan,
        'pan_card_number': customer.pan_card_number,
        'date_of_birth': customer.date_of_birth,
        'state': customer.state,
        'city': customer.city,
        'pincode': customer.pincode,
        'address': customer.address,
        'status': 'new',  # New lead status
        'lead_type': 'MOTOR',  # You can customize based on the vehicle type
    }

    if existing_lead:
        # Update the existing lead
        for field, value in lead_data.items():
            setattr(existing_lead, field, value)
        existing_lead.save()
        messages.success(request, "Lead updated successfully!")
    else:
        # Create a new lead
        Leads.objects.create(**lead_data)
        messages.success(request, "Lead created successfully!")

    # Redirect to the quotation info page after processing the lead
    return redirect(reverse("show-quotation-info", args=[cus_id]))

def store_log(log_type, log_for, message, user_id=None, ip_address=None):
    
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO logs (log_type, log_for, message, user_id, ip_address, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (log_type, log_for, message, user_id, ip_address, ist_now, ist_now))
