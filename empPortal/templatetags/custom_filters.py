from django import template
from datetime import datetime
import re

register = template.Library()

@register.filter
def format_date(value):
    """Convert '24-Feb-2025' to 'Feb. 24, 2025'"""
    try:
        return datetime.strptime(value, "%d-%b-%Y").strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return ""  # Return an empty string if parsing fails

@register.filter  # Register get_year as a valid Django template filter
def get_year(value):
    """Extracts the year from 'MM/YYYY' format."""
    if value:
        match = re.search(r"\d{2}/(\d{4})", value)
        if match:
            return match.group(1)  # Extracts the year (YYYY)
    return ""  # Return an empty string if parsing fails

@register.filter
def get_attr(obj, attr_name):
    """Safely gets an attribute from an object."""
    return getattr(obj, attr_name, "")

@register.filter
def attr(obj, field_name):
    """Returns the attribute of an object dynamically."""
    return getattr(obj, field_name, "")

@register.filter
def get_index(sequence, index):
    """Custom filter to get an item from a list using its index."""
    try:
        return sequence[index]
    except (IndexError, TypeError):
        return ""