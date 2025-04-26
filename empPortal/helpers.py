import random
import string
import logging
from datetime import datetime
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import Commission, Users, DocumentUpload, Branch
from empPortal.model import Partner
from .utils import store_log

logger = logging.getLogger(__name__)

def format_date(date, format_str="%Y-%m-%d"):
    """Format a datetime object as a string."""
    return date.strftime(format_str) if date else None

def generate_random_string(length=10):
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def is_valid_email(email):
    """Check if an email is valid."""
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def sync_user_to_partner(user_id, request=None):
    """Sync user data to Partner table and log the operation."""
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        logger.warning(f"User with ID {user_id} does not exist.")
        return False

    partner_data = {
        "pan_no": user.pan_no,
        "email": user.email,
        "phone": user.phone,
        "name": f"{user.first_name} {user.last_name}".strip(),
        "updated_at": user.updated_at,
        "active": user.user_active if hasattr(user, 'user_active') else True
    }

    partner, created = Partner.objects.update_or_create(
        user_id=user.id,
        defaults=partner_data
    )

    # Log the syncing activity if request object is provided
    if request:
        store_log(
            log_type="INFO",
            log_for="PARTNER_SYNC",
            message=f"Partner record {'created' if created else 'updated'} for user ID {user_id}",
            user_id=request.user.id if request.user.is_authenticated else None,
            ip_address=request.META.get("REMOTE_ADDR", "")
        )

    logger.info(f"Partner {'created' if created else 'updated'} for user_id: {user_id}")
    return partner

def sync_existing_users_to_partner():
    """
    Sync all existing users with role_id=4 to the Partner table if not already synced.
    """
    users_to_sync = Users.objects.filter(role_id=4)

    synced_count = 0
    for user in users_to_sync:
        partner_data = {
            "pan_no": user.pan_no,
            "email": user.email,
            "phone": user.phone,
            "name": f"{user.first_name} {user.last_name}".strip(),
            "updated_at": user.updated_at,
            "active": user.user_active if hasattr(user, 'user_active') else True
        }

        partner, created = Partner.objects.update_or_create(
            user_id=user.id,
            defaults=partner_data
        )

        logger.info(f"Partner {'created' if created else 'updated'} for user_id: {user.id}")
        synced_count += 1

    print(f"✅ Synced {synced_count} users to Partner table.")
    return synced_count
