import builtins
from pprint import pprint
import requests
from django.conf import settings

def dd(*args):
    """Dump and Debug - Prints values but does NOT stop execution."""
    for arg in args:
        pprint(arg)  # Pretty print the data
    return  # Remove sys.exit()

# Register `dd()` globally
builtins.dd = dd




# utils.py


# utils.py
import requests
from django.conf import settings


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