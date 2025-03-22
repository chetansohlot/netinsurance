import random
import string
from datetime import datetime

def format_date(date, format_str="%Y-%m-%d"):
    """Format a datetime object as a string."""
    return date.strftime(format_str) if date else None

def generate_random_string(length=10):
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def is_valid_email(email):
    """Check if an email is valid."""
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False
