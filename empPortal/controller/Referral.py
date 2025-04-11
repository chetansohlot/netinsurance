from django.shortcuts import render,redirect, get_object_or_404
from ..models import Franchises, Department
from empPortal.model import Referral
from django.db.models import OuterRef, Subquery
from django.contrib import messages
from datetime import datetime
from django.urls import reverse
import pprint  # Import pprint for better formatting
from django.http import JsonResponse
import pdfkit
import os
from django.conf import settings
import os
from dotenv import load_dotenv
from django.templatetags.static import static  # ✅ Import static
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.forms.models import model_to_dict
import json
from django.utils.timezone import now
from django.core.paginator import Paginator
import helpers  
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
    sort_by = request.GET.get('sort_by', '')

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    referrals = Referral.objects.all()

    # Filtering
    if search_field and search_query:
        filter_args = {f"{search_field}__icontains": search_query}
        referrals = referrals.filter(**filter_args)

    # Sorting
    if sort_by == 'name-a_z':
        referrals = referrals.order_by('name')
    elif sort_by == 'name-z_a':
        referrals = referrals.order_by('-name')
    elif sort_by == 'recently_created':
        referrals = referrals.order_by('-created_at')
    elif sort_by == 'recently_updated':
        referrals = referrals.order_by('-updated_at')
    elif sort_by == 'active_first':
        referrals = referrals.order_by('-active', '-created_at')
    elif sort_by == 'inactive_first':
        referrals = referrals.order_by('active', '-created_at')
    else:
        referrals = referrals.order_by('-created_at')  # default

    total_count = referrals.count()

    # Pagination
    paginator = Paginator(referrals, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'referral/index.html', {
        'page_obj': page_obj,
        'total_count': total_count,
        'search_field': search_field,
        'search_query': search_query,
        'per_page': per_page,
        'sort_by': sort_by,
    })

def create_or_edit(request, referral_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    referral = None
    is_editing = False

    if referral_id:
        referral = get_object_or_404(Referral, id=referral_id)
        is_editing = True

    if request.method == "GET":
        return render(request, 'referral/create.html', {
            'referral': referral,
            'is_editing': is_editing,
        })

    elif request.method == "POST":
        name = request.POST.get("name", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()

        ## add field ## ---parth
        dob = request.POST.get("dob", "").strip()
        date_of_anniversary = request.POST.get("date_of_anniversary", "").strip()
        pan_card_number = request.POST.get("pan", "").strip()
        aadhar = request.POST.get("aadhar", "").strip()
        # print(aadhar)
        referral_code = (
            referral.referral_code if referral
            else generate_referral_code()
        )

        # Pre-fill values in case of error
        form_data = {
            "name": name,
            "mobile": mobile,
            "email": email,
            "address": address,
            "dob": dob,
            "date_of_anniversary": date_of_anniversary,
            "pan_card_number": pan_card_number,
            "aadhar_no": aadhar,
            "referral_code": referral_code,
        }

        # === Validation ===
        if referral:
            # For update, exclude current record from uniqueness checks
            if Referral.objects.exclude(id=referral.id).filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return render(request, 'referral/create.html', {
                    'referral': form_data,
                    'is_editing': True,
                })

            if mobile and Referral.objects.exclude(id=referral.id).filter(mobile=mobile).exists():
                messages.error(request, "Mobile number already exists.")
                return render(request, 'referral/create.html', {
                    'referral': form_data,
                    'is_editing': True,
                })

            # Save updates
            referral.name = name
            referral.email = email
            referral.mobile = mobile
            referral.address = address

            referral.dob = dob or None
            referral.date_of_anniversary = date_of_anniversary or None
            referral.pan_card_number = pan_card_number
            referral.aadhar_no = aadhar

            referral.updated_at = now()
            referral.save()

            messages.success(request, f"Referral updated successfully! ID: {referral.id}")
            return redirect(reverse("referral-management"))

        else:
            # For create, check full uniqueness
            if Referral.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return render(request, 'referral/create.html', {
                    'referral': form_data,
                    'is_editing': False,
                })

            if mobile and Referral.objects.filter(mobile=mobile).exists():
                messages.error(request, "Mobile number already exists.")
                return render(request, 'referral/create.html', {
                    'referral': form_data,
                    'is_editing': False,
                })

            new_referral = Referral.objects.create(
                name=name,
                email=email,
                mobile=mobile,
                address=address,
                referral_code=referral_code,

                dob=dob or None,
                date_of_anniversary=date_of_anniversary or None,
                pan_card_number=pan_card_number,
                aadhar_no=aadhar,

                created_at=now(),
                updated_at=now(),
            )

            messages.success(request, f"Referral created successfully! ID: {new_referral.id}")
            return redirect(reverse("referral-management"))


def generate_referral_code():
    last_referral = Referral.objects.order_by('-id').first()
    next_id = 1 if not last_referral else last_referral.id + 1
    return f"REF{str(next_id).zfill(4)}"  # e.g., REF0001, REF0023

def toggle_referral_status(request, referral_id):
    """Toggle referral active status (Activate/Deactivate)"""
    if request.method == "POST":
        referral = get_object_or_404(Referral, id=referral_id)

        # Toggle boolean status
        referral.active = not referral.active
        referral.save()

        status_text = "Active" if referral.active else "Inactive"

        return JsonResponse({
            "success": True,
            "message": f"Referral status updated to {status_text}",
            "status": status_text,
            "referral_id": referral.id
        })

    return JsonResponse({"success": False, "message": "Invalid request method!"}, status=400)
