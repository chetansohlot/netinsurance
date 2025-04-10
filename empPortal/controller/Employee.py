from django.shortcuts import render,redirect, get_object_or_404
from ..models import Franchises, Branch, Department, Users, Roles
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
from django.contrib.auth.hashers import make_password
import re
from django.http import JsonResponse


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
    sort_by = request.GET.get('sort_by','') # Sort Criteria

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10  

    # Fetch all employees (Active & Role not in [1, 4])
    employees = Users.objects.filter(status=1).exclude(role_id__in=[1, 4]) \
        .select_related('role') \
        .order_by('-created_at')

    # Fetch branch names separately
    branches = {str(branch.id): branch.branch_name for branch in Branch.objects.all()}

    # Fetch all users in a dictionary for supervisor lookup
    all_users = {str(user.id): user for user in Users.objects.all()}

    # Apply filtering
    if search_field and search_query:
        filter_args = {f"{search_field}__icontains": search_query}
        employees = employees.filter(**filter_args)

    ## Sort Criteria ##
    if sort_by == 'name-a_z':
        employees = employees.order_by('first_name')
    elif sort_by == 'name-z_a':
        employees = employees.order_by('-first_name')
    elif sort_by == 'recently_activated':
        employees = employees.order_by('-created_at') # latest first
    elif sort_by == 'recently_deactivated':
        employees = employees.order_by('-updated_at') # Latest Updated first
    else:
        employees = employees.order_by('-created_at')  # Default Sorting          

    total_count = employees.count()

    # Pagination
    paginator = Paginator(employees, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'employee/index.html', {
        'page_obj': page_obj, 
        'total_count': total_count,
        'search_field': search_field,
        'search_query': search_query,
        'per_page': per_page,
        'branches': branches,
        'all_users': all_users,  # Pass all users for supervisor lookup
        'sort_by' : sort_by,  ## Sort Criteria
    })





def check_branch_email(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        branch_id = request.POST.get("branch_id", "").strip()
        
        print(f"Checking email: {email}, Branch ID: {branch_id}")  # Debugging

        # If editing, allow current branch email
        if branch_id:
            branch = Branch.objects.filter(id=branch_id).first()
            if branch and branch.email == email:
                return JsonResponse({"exists": False})  # Allow the current email

        # Check if email exists in any other branch
        exists = Branch.objects.filter(email=email).exists()
        print(f"Exists in DB: {exists}")  # Debugging

        return JsonResponse({"exists": exists})

    return JsonResponse({"error": "Invalid request"}, status=400)


def create_or_edit(request, employee_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    employee = None
    if employee_id:
        employee = get_object_or_404(Users, id=employee_id)

    # Only allow admins to add/edit users
    if request.user.role_id != 1:
        messages.error(request, "You do not have permission to add or edit users.")
        return redirect('employee-management')

    roles = Roles.objects.exclude(id__in=[1, 4])  # Exclude roles with ID 1 and 4
    branches = Branch.objects.all().order_by('-created_at')
    departments = Department.objects.all().order_by('-created_at')

    user_instance = None
    if employee_id:
        user_instance = get_object_or_404(Users, id=employee_id)

    if request.method == "GET":
        return render(request, 'employee/create.html', {
            'roles': roles,
            'branches': branches,
            'employee': employee,
            'departments': departments,
            'user_instance': user_instance
        })

    elif request.method == "POST":
        pan_no = request.POST.get("pan_no", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()

        # Validations
        if not first_name:
            messages.error(request, 'First Name is required')
        elif len(first_name) < 3:
            messages.error(request, 'First Name must be at least 3 characters long')

        if last_name and len(last_name) < 3:
            messages.error(request, 'Last Name must be at least 3 characters long')

        if not email:
            messages.error(request, 'Email is required')
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            messages.error(request, 'Invalid email format')
        elif not user_instance and Users.objects.filter(email=email).exists():
            messages.error(request, 'This email is already in use')

        if not phone:
            messages.error(request, 'Mobile No is required')
        elif not phone.isdigit() or len(phone) != 10 or phone[0] <= '5':
            messages.error(request, 'Invalid mobile number format')
        elif not user_instance and Users.objects.filter(phone=phone).exists():
            messages.error(request, 'This mobile number already exists.')

        if not password and not user_instance:
            messages.error(request, 'Password is required for new users')
        elif password and len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')

        if messages.get_messages(request):
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if user_instance:
            user_instance.first_name = first_name
            user_instance.last_name = last_name
            user_instance.email = email
            user_instance.phone = phone
            user_instance.pan_no = pan_no
            if password:
                user_instance.password = make_password(password)
            user_instance.save()

            messages.success(request, f"User updated successfully! User ID: {user_instance.id}")
            return redirect('employee-allocation-update', employee_id=user_instance.id)

        else:
            # Generate user_gen_id
            last_user = Users.objects.all().order_by('-id').first()
            if last_user and last_user.user_gen_id.startswith('UR-'):
                last_user_gen_id = int(last_user.user_gen_id.split('-')[1])
                new_gen_id = f"UR-{last_user_gen_id+1:04d}"
            else:
                new_gen_id = "UR-0001"

            new_user = Users.objects.create(
                user_gen_id=new_gen_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                pan_no=pan_no,
                status=1,
                password=make_password(password),
                created_at=now(),
                updated_at=now(),
            )

            messages.success(request, f"User created successfully! User ID: {new_user.id}")
            return redirect('employee-allocation-update', employee_id=new_user.id)


def create_or_edit_allocation(request, employee_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST":
        department_id = request.POST.get('department', '').strip()
        branch_id = request.POST.get('branch', '').strip()
        role_id = request.POST.get('role', '').strip()
        senior_id = request.POST.get('senior', '').strip()
        team_leader = request.POST.get('team_leader', '').strip()

        # Validate required fields
        if not department_id:
            messages.error(request, 'Department is required.')
        if not branch_id:
            messages.error(request, 'Branch is required.')
        if not role_id:
            messages.error(request, 'Role is required.')

        # Prevent assigning the Admin role
        if role_id == '1':  
            messages.error(request, "You cannot assign the Admin role.")

        # If role is 5 (Regional Manager), assign senior_id to team_leader
        if role_id == '5':
            if not team_leader:
                messages.error(request, "Team Leader selection is required for Role 5.")
            else:
                senior_id = team_leader  # Assign the Team Leader as senior

        # Check if there are any error messages
        if messages.get_messages(request):
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Fetch user data if employee_id is provided (for editing allocation)
        user_data = Users.objects.filter(id=employee_id).first() if employee_id else None

        if user_data:
            # Update allocation details
            user_data.department_id = department_id
            user_data.branch_id = branch_id
            user_data.role_id = role_id
            user_data.senior_id = senior_id
            user_data.save()
            messages.success(request, "User allocation updated successfully.")
        else:
            messages.error(request, "User not found.")

        return redirect('employee-management')

    # Fetch necessary data for the form
    departments = Department.objects.all().order_by('name')
    branches = Branch.objects.filter(status='Active').order_by('-created_at')

    roles = Roles.objects.exclude(id__in=[1, 4])
    senior_users = Users.objects.filter(role_id=2).values('id', 'first_name', 'last_name', 'senior_id')  # Managers

    senior_details = None
    tl_details = None
    tl_list = None
    employee = None  # Ensure it's defined before usage

    if employee_id:
        employee = Users.objects.filter(id=employee_id).first()
        if employee and employee.role_id == 5 and employee.senior_id:
            tl_details = Users.objects.filter(id=employee.senior_id).values(
                'id', 'first_name', 'last_name', 'senior_id'
            ).first()

            if tl_details and tl_details['senior_id']:
                senior_id = tl_details['senior_id']

                # Get the senior details
                senior_details = Users.objects.filter(id=senior_id).values(
                    'id', 'first_name', 'last_name'
                ).first()

                # Get all users who report to this senior
                tl_list = list(Users.objects.filter(senior_id=senior_id).values(
                    'id', 'first_name', 'last_name', 'role_id'
                ))
        elif employee and employee.senior_id:
            senior_details = Users.objects.filter(id=employee.senior_id).values(
                'id', 'first_name', 'last_name', 'senior_id'
            ).first()

    return render(request, 'employee/allocation-update.html', {
        'employee': employee,
        'departments': departments,
        'branches': branches,
        'roles': roles,
        'senior_users': senior_users,
        'tl_list': tl_list,
        'senior_details': senior_details,
    })


