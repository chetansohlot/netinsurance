from django.shortcuts import render,redirect, get_object_or_404
from ..models import Franchises, Branch
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

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    branches = Branch.objects.all().order_by('-created_at')
    total_count = branches.count()

    # Pagination (10 branches per page)
    paginator = Paginator(branches, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'branches/index.html', {'page_obj': page_obj, 'total_count': total_count})


def create_or_edit(request, branch_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch existing branch if editing
    branch = None
    if branch_id:
        branch = get_object_or_404(Branch, id=branch_id)

    if request.method == "GET":
        return render(request, 'branches/create.html', {
            'branch': branch  # Pass existing data if editing
        })
    
    elif request.method == "POST":
        # Extract form data
        branch_name = request.POST.get("branch_name", "").strip()
        contact_person = request.POST.get("contact_person", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        if branch:
            # Update existing record
            branch.branch_name = branch_name
            branch.contact_person = contact_person
            branch.mobile = mobile
            branch.email = email
            branch.address = address
            branch.city = city
            branch.state = state
            branch.pincode = pincode
            branch.updated_at = now()
            branch.save()

            messages.success(request, f"Branch updated successfully! Branch ID: {branch.id}")
            return redirect(reverse("branch-management"))  # Redirect to branch listing

        else:
            # Create new record
            new_branch = Branch.objects.create(
                branch_name=branch_name,
                contact_person=contact_person,
                mobile=mobile,
                email=email,
                address=address,
                city=city,
                state=state,
                pincode=pincode,
                created_at=now(),
                updated_at=now(),
            )

            messages.success(request, f"Branch created successfully! Branch ID: {new_branch.id}")
            return redirect(reverse("branch-management"))  # Redirect to branch listing
