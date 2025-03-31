import builtins
from pprint import pprint
import requests
from django.conf import settings
from datetime import datetime
from django.utils.timezone import now
from django.db import models, connection
import pytz
IST = pytz.timezone("Asia/Kolkata")

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

def store_log(log_type, log_for, message, user_id=None, ip_address=None):
    
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO logs (log_type, log_for, message, user_id, ip_address, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (log_type, log_for, message, user_id, ip_address, ist_now, ist_now))
