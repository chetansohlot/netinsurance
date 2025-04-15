from django import template
from datetime import datetime
import re

register = template.Library()

@register.filter
def fallback(primary, secondary):
    return primary or secondary

@register.filter
def blank_if_none_or_text_none(value):
    if value in [None, 'None']:
        return ''
    return value

@register.filter
def indian_currency(value):
    try:
        value = float(value)
        int_part, dot, decimal_part = f"{value:.2f}".partition(".")
        int_part = int(int_part)
        if int_part < 1000:
            return f"{int_part}.{decimal_part}"
        else:
            s = str(int_part)
            last3 = s[-3:]
            rest = s[:-3]
            rest = ",".join([rest[max(i - 2, 0):i] for i in range(len(rest), 0, -2)][::-1])
            return f"{rest},{last3}.{decimal_part}" if rest else f"{last3}.{decimal_part}"
    except:
        return value
    
    
@register.filter
def get_item(dictionary, key):
    """Returns the value from a dictionary given a key."""
    return dictionary.get(key, "-")

@register.filter
def format_date(value, output_format="%Y-%m-%d"):
    """Convert '03-Mar-2025' to '2025-03-03' (YYYY-MM-DD)."""
    try:
        if not value:
            return ""

        value = str(value).strip()  # Ensure it's a string

        # Convert 'DD-MMM-YYYY' → 'YYYY-MM-DD'
        date_obj = datetime.strptime(value, "%d-%b-%Y")

        # Format as YYYY-MM-DD
        return date_obj.strftime(output_format)
    except ValueError:
        return "Invalid Date"

   
@register.filter
def title_case(value):
    """Convert a string to title case (first letter capitalized)."""
    if isinstance(value, str):
        return value.title()
    return value

@register.filter
def trim(value):
    """Removes leading and trailing spaces from a string."""
    return value.strip() if isinstance(value, str) else value
 
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