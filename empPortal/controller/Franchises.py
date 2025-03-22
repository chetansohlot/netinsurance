from django.shortcuts import render,redirect, get_object_or_404
from ..models import Franchises
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

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    franchises = Franchises.objects.all().order_by('-created_at')

    # Pagination (10 franchises per page)
    paginator = Paginator(franchises, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'franchises/index.html', {'page_obj': page_obj})


def create_or_edit(request, franchise_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch existing franchise if editing
    franchise = None
    if franchise_id:
        franchise = get_object_or_404(Franchises, id=franchise_id)

    if request.method == "GET":
            
        return render(request, 'franchises/create.html', {
            'franchise': franchise  # Pass existing data if editing
        })
    
    elif request.method == "POST":
        # Extract form data
        name = request.POST.get("name", "").strip()
        contact_person = request.POST.get("contact_person", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        gst_number = request.POST.get("gst_number", "").strip() or None
        pan_number = request.POST.get("pan_number", "").strip() or None
        registration_no = request.POST.get("registration_no", "").strip() or None
        
        if franchise:
            # Update existing record
            franchise.name = name
            franchise.contact_person = contact_person
            franchise.mobile = mobile
            franchise.email = email
            franchise.address = address
            franchise.city = city
            franchise.state = state
            franchise.pincode = pincode
            franchise.gst_number = gst_number
            franchise.pan_number = pan_number
            franchise.registration_no = registration_no
            franchise.updated_at = now()
            franchise.save()

            messages.success(request, f"Franchise updated successfully! Franchise ID: {franchise.id}")
            return redirect(reverse("franchise-management"))  # Redirect to franchise listing

        else:
            # Create new record
            new_franchise = Franchises.objects.create(
                name=name,
                contact_person=contact_person,
                mobile=mobile,
                email=email,
                address=address,
                city=city,
                state=state,
                pincode=pincode,
                gst_number=gst_number,
                pan_number=pan_number,
                registration_no=registration_no,
                created_at=now(),
                updated_at=now(),
            )

            messages.success(request, f"Franchise created successfully! Franchise ID: {new_franchise.id}")
            return redirect(reverse("franchise-management"))  # Redirect to franchise listing
