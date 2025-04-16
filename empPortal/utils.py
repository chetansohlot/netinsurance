import builtins
from pprint import pprint
import requests
import json
from django.conf import settings
from datetime import datetime
from django.utils.timezone import now
from django.db import models, connection
import pytz
from django.http import HttpResponse,JsonResponse

IST = pytz.timezone("Asia/Kolkata")

from django.shortcuts import render,redirect, get_object_or_404
from .models import Commission, Users, QuotationCustomer, Leads, VehicleInfo, QuotationVehicleDetail,IrdaiAgentApiLogs
from django.contrib import messages
from django.urls import reverse
import base64
ist_now = now().astimezone(IST)
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'django-insecure-#^%otoo7@)j9a8_6m)n8om&2_x6@d2i(*mw^97pme+b-dy0#ze')

# def encrypt_text(text):
#     raw = f"{text}-{SECRET_KEY}"
#     encoded_bytes = base64.urlsafe_b64encode(raw.encode('utf-8')) 
#     return encoded_bytes.decode('utf-8')

# def decrypt_text(encrypted_text):
#     # try:
#         decoded_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
#         decoded_str = decoded_bytes.decode('utf-8')
#         decoded_text, _ = decoded_str.split('-', 1)
#         return decoded_text
#     # except Exception:
#     #     return None

def to_int(value):
    try:
        return int(value) if value not in [None, '', 'null'] else None
    except ValueError:
        return None

def dd(*args):
    """Dump and Debug - Prints values but does NOT stop execution."""
    for arg in args:
        pprint(arg)  # Pretty print the data
    return  # Remove sys.exit()

# Register `dd()` globally
builtins.dd = dd

def check_agent_linked_info(data_list):
    """
    Check whether users with given PAN numbers are already linked with any agency.

    Args:
        data_list (list): A list of dicts containing 'user_id' and 'pan_no'.

    Returns:
        list: A list of dicts with user_id, pan_no, and agency_linked status.
    """
    url = getattr(settings, 'IRDAI_AGENT_CHECK_URL', 'https://sandbox.surepass.io/api/v1/irdai/verify')
    token = getattr(settings, 'IRDAI_API_TOKEN', 'your-fallback-token')

    results = []

    for data in data_list:
        user_id = data['user_id']
        pan_no = data['pan_no']

        payload = json.dumps({
            "id_number": pan_no
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            status_code = response.status_code
            try:
                res_data = response.json()
            except ValueError:
                res_data = {"status":500,"error": "Invalid JSON response"}

            IrdaiAgentApiLogs.objects.create(
                url=url,
                user_id=user_id,
                request_payload=json.dumps(payload),
                request_headers=json.dumps(headers),
                response_status=status_code,
                response_body=json.dumps(res_data)
            )
            
            agency_linked = False
            message = ""
            agent_status = 500
            
            
                        
            if status_code == 200:
                results_data = res_data.get('data', {}).get('results', [])
                if results_data:
                    agent_status = 200
                    agency_linked = True
                    agency_name = results_data[0].get('insurer_type', 'the existing agency')
                    message = f"Please get a NOC from {agency_name}"
            elif status_code == 422:
                agency_linked = False
                agent_status = 400
           
            results.append({
                'user_id': user_id,
                'pan_no': pan_no,
                'agency_linked': agency_linked,
                'message': message,
                'agent_status': agent_status
            })

        except Exception as e:
            results.append({
                'user_id': user_id,
                'pan_no': pan_no,
                'agency_linked': False,
                'agent_status': 500,
                'error': str(e)
            })

    return results


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

def getUserNameByUserId(user_id):
    try:
        return Users.objects.get(id=user_id).full_name
    except Users.DoesNotExist:
        return None

def commisionRateByMemberId(member_id):
    commission_data = Commission.objects.filter(member_id=member_id).first()
    return commission_data

def insurercommisionRateByMemberId(member_id):
    commission_data = Commission.objects.filter(member_id=member_id).first()
    return commission_data