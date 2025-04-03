from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users, DocumentUpload, Branch
from empPortal.model import BankDetails
from ..forms import DocumentUploadForm
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.utils.timezone import now
from django.contrib.auth import authenticate, login ,logout
from django.core.files.storage import FileSystemStorage
import re
import requests
from fastapi import FastAPI, File, UploadFile
import fitz
import openai
import time
import json
from django.http import JsonResponse
import os
import zipfile
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import connection
import logging
logger = logging.getLogger(__name__)
import os
import pdfkit
from django.template.loader import render_to_string
from pprint import pprint 
from django.db.models import Q
from django.core.paginator import Paginator

from django.db.models.functions import Concat
from django.db.models import Q, Value

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def members(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role_id == 1:
        role_ids = [4]  # Filter for specific roles

        per_page = request.GET.get('per_page', 10)
        search_field = request.GET.get('search_field', '')  # Field to search
        search_query = request.GET.get('search_query', '')  # Search value
        sorting = request.GET.get('sorting', '')  # Sorting option
        global_search = request.GET.get('global_search', '').strip()
        
        try:
            per_page = int(per_page)
        except ValueError:
            per_page = 10  # Default to 10 if invalid value is given

        # Base QuerySet
        users = Users.objects.filter(role_id__in=role_ids)

        
        if global_search:
            users = users.annotate(
                search_full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(
                Q(search_full_name__icontains=global_search) |  
                Q(first_name__icontains=global_search) |
                Q(last_name__icontains=global_search) |
                Q(email__icontains=global_search) |
                Q(phone__icontains=global_search)  
            )

        # Apply filtering
        if search_field and search_query:
            filter_args = {f"{search_field}__icontains": search_query}
            users = users.filter(**filter_args)

        # Apply sorting
        if sorting == "name_a_z":
            users = users.order_by("first_name")
        elif sorting == "name_z_a":
            users = users.order_by("-first_name")
        elif sorting == "recently_activated":
            users = users.filter(activation_status='1').order_by("-updated_at")
        elif sorting == "recently_deactivated":
            users = users.filter(
                Q(activation_status='0') | Q(activation_status__isnull=True) | Q(activation_status='')
            ).order_by("-updated_at")
        else:
            users = users.order_by("-updated_at")

        total_agents = users.count()
        active_agents = users.filter(activation_status='1').count()
        deactive_agents = users.filter(
            Q(activation_status='0') | Q(activation_status__isnull=True) | Q(activation_status='')
        ).count()
        pending_agents = 0  # Define pending logic if needed

        # Paginate results
        paginator = Paginator(users, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'members/members.html', {
            'page_obj': page_obj,
            'total_agents': total_agents,
            'active_agents': active_agents,
            'deactive_agents': deactive_agents,
            'pending_agents': pending_agents,
            'search_field': search_field,
            'search_query': search_query,
            'global_search': global_search,
            'sorting': sorting,
            'per_page': per_page,
        })
    else:
        return redirect('login')
    
def members_inprocess(request):
    if request.user.is_authenticated:
        if request.user.role_id == 1:
            # Define the list of role IDs to filter
            # role_ids = [2, 3, 4]
            role_ids = [4]
            # Filter users whose role_id is in the specified list
            users = Users.objects.filter(role_id__in=role_ids)
        else:
            users = Users.objects.none()  # Return an empty queryset for unauthorized users
        return render(request, 'members/members-inprocess.html', {'users': users})
    else:
        return redirect('login')
    
    
def members_intraining(request):
    if request.user.is_authenticated:
        if request.user.role_id == 1:
            # Define the list of role IDs to filter
            # role_ids = [2, 3, 4]
            role_ids = [4]
            # Filter users whose role_id is in the specified list
            users = Users.objects.filter(role_id__in=role_ids)
        else:
            users = Users.objects.none()  # Return an empty queryset for unauthorized users
        return render(request, 'members/members-intraining.html', {'users': users})
    else:
        return redirect('login')
    
    
def members_inexam(request):
    if request.user.is_authenticated:
        if request.user.role_id == 1:
            # Define the list of role IDs to filter
            # role_ids = [2, 3, 4]
            role_ids = [4]
            # Filter users whose role_id is in the specified list
            users = Users.objects.filter(role_id__in=role_ids)
        else:
            users = Users.objects.none()  # Return an empty queryset for unauthorized users
        return render(request, 'members/members-inexam.html', {'users': users})
    else:
        return redirect('login')
    
    
def members_activated(request):
    if request.user.is_authenticated:
        if request.user.role_id == 1:
            # Define the list of role IDs to filter
            # role_ids = [2, 3, 4]
            role_ids = [4]
            # Filter users whose role_id is in the specified list
            users = Users.objects.filter(role_id__in=role_ids)
        else:
            users = Users.objects.none()  # Return an empty queryset for unauthorized users
        return render(request, 'members/members-activated.html', {'users': users})
    else:
        return redirect('login')
    
    
def members_rejected(request):
    if request.user.is_authenticated:
        if request.user.role_id == 1:
            # Define the list of role IDs to filter
            # role_ids = [2, 3, 4]
            role_ids = [4]
            # Filter users whose role_id is in the specified list
            users = Users.objects.filter(role_id__in=role_ids)
        else:
            users = Users.objects.none()  # Return an empty queryset for unauthorized users
        return render(request, 'members/members-rejected.html', {'users': users})
    else:
        return redirect('login')
    

    
def memberView(request, user_id):
    if request.user.is_authenticated:
        # Fetch user details and bank details
        user_details = Users.objects.get(id=user_id)
        bank_details = BankDetails.objects.filter(user_id=user_id).first()

        docs = DocumentUpload.objects.filter(user_id=user_id).first()
        # Fetch commissions for the specific member
        query = """
            SELECT c.*, u.first_name, u.last_name, c.product_id
            FROM commissions c
            INNER JOIN users u ON c.member_id = u.id
            WHERE c.member_id = %s
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [user_id])
            commissions_list = dictfetchall(cursor)

        # Define available products
        products = [
            {'id': 1, 'name': 'Motor'},
            {'id': 2, 'name': 'Health'},
            {'id': 3, 'name': 'Term'},
        ]

        # Ensure dictionary uses integer keys
        product_dict = {product['id']: product['name'] for product in products}

        # Map product names to commissions list
        for commission in commissions_list:
            product_id = commission.get('product_id')
            commission['product_name'] = product_dict.get(int(product_id), 'Unknown') if product_id is not None else 'Unknown'

        branches = Branch.objects.all().order_by('-created_at')

        
        branch = None
        if user_details.branch_id:
            branch = Branch.objects.filter(id=user_details.branch_id).first()
                
        senior = None
        if user_details.senior_id:
            senior = Users.objects.filter(id=user_details.senior_id).first()

        manager = None
        if senior and senior.senior_id:  # Ensure senior is not None before accessing senior_id
            manager = Users.objects.filter(id=senior.senior_id).first()

        return render(request, 'members/member-view.html', {
            'user_details': user_details,
            'bank_details': bank_details,
            'docs': docs,
            'branches': branches,
            'sales_manager': senior,
            'branch': branch,
            'branch_manager': manager,
            'commissions': commissions_list,  # Fixed variable name
            'products': products  # Fixed variable name
        })
    else:
        return redirect('login')
    
    
def get_branch_managers(request):
    branch_id = request.GET.get('branch_id')
    branch_managers = Users.objects.filter(branch_id=branch_id, role_id=2).values('id', 'first_name', 'last_name')
    managers_list = [{'id': manager['id'], 'full_name': f"{manager['first_name']} {manager['last_name']}"} for manager in branch_managers]
    return JsonResponse({'branch_managers': managers_list})

def get_sales_managers(request):
    branch_manager_id = request.GET.get('branch_manager_id')
    sales_managers = Users.objects.filter(senior_id=branch_manager_id, role_id=3).values('id', 'first_name', 'last_name')
    sales_list = [{'id': manager['id'], 'full_name': f"{manager['first_name']} {manager['last_name']}"} for manager in sales_managers]
    return JsonResponse({'sales_managers': sales_list})

# LATEST CODE  
from django.templatetags.static import static  # ✅ Import static

def activationPdf(request,user_id):
    """Generate a PDF for the user and return the file path."""
    wkhtml_path = os.getenv('WKHTML_PATH', r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
    customer = Users.objects.get(id=user_id)

    training_pdf_path = os.path.join(settings.MEDIA_ROOT, f'training/Training_Material_Elevate_Insurance_V1.0.pdf')

    context = {
        "user": customer,
        "support_email": "support@elevateinsurance.in",
        "company_website": "https://pos.elevateinsurance.in/",
        "sub_broker_test_url": "https://pos.elevateinsurance.in/",
        "training_material_url": training_pdf_path,
        "support_number": +918887779999,
        "logo_url": request.build_absolute_uri(static('dist/img/logo2.png'))
    }

    html_content = render_to_string("members/activation-pdf.html", context)

    options = {
        'enable-local-file-access': '',
        'page-size': 'A4',
        'encoding': "UTF-8",
    }

    pdf_path = os.path.join(settings.MEDIA_ROOT, f'account_activation_{user_id}.pdf')

    try:
        pdfkit.from_string(html_content, pdf_path, configuration=config, options=options)
        return pdf_path
    except Exception as e:
        print(f"PDF generation failed: {e}")
        return None  # Return None if PDF generation fails

def activateUser(request, user_id):
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch user documents
    docs = DocumentUpload.objects.filter(user_id=user_id).first()

    # Ensure all required documents are approved before activating the user
    if docs and all([
        docs.aadhaar_card_front_status == 'Approved',
        docs.aadhaar_card_back_status == 'Approved',
        docs.upload_pan_status == 'Approved',
        docs.upload_cheque_status == 'Approved',
        docs.tenth_marksheet_status == 'Approved'
    ]):
        try:
            # Update user activation status in the database
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET activation_status = %s WHERE id = %s",
                    ['1', user_id]
                )

            user = get_object_or_404(Users, id=user_id)
            user_email = user.email
            training_pdf_path = os.path.join(settings.MEDIA_ROOT, f'training/Training_Material_Elevate_Insurance_V1.0.pdf')
            training_pdf_path = os.path.join(settings.MEDIA_ROOT, 'training/Training_Material_Elevate_Insurance_V1.0.pdf')

            training_material_url = request.build_absolute_uri(settings.MEDIA_URL + 'training/Training_Material_Elevate_Insurance_V1.0.pdf')

            # Render email HTML template
            email_body = render_to_string('members/activation-email.html', {
                'user': user,
                "logo_url": request.build_absolute_uri(static('dist/img/logo2.png')),
                "support_email": "support@elevateinsurance.in",
                "company_website": "https://pos.elevateinsurance.in/",
                "sub_broker_test_url": "https://pos.elevateinsurance.in/",
                "training_material_url": training_material_url,
                "support_number": +918887779999,
            })

            # Prepare and send activation confirmation email
            subject = 'Account Activated Successfully'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user_email]

            email = EmailMessage(subject, email_body, from_email, recipient_list)
            email.content_subtype = "html"  # Set content type to HTML



            # Attach file if it exists
            if os.path.exists(training_pdf_path):
                email.attach_file(training_pdf_path)
            else:
                logger.error(f"Training PDF not found: {training_pdf_path}")
                
            # Generate and attach PDF
            # pdf_path = activationPdf(request, user_id)
            # if pdf_path and os.path.exists(pdf_path):
            #     email.attach_file(pdf_path)
            # else:
            #     logger.error("PDF generation failed or file not found. Skipping attachment.")

            email.send()
            messages.success(request, "User account has been activated successfully!")

        except Exception as e:
            logger.error(f"Error activating user: {e}")
            messages.error(request, "An error occurred during activation.")
    else:
        messages.error(request, "User cannot be activated. Please ensure all required documents are approved.")

    # Redirect to the member view page
    return redirect('member-view', user_id=user_id)



# LATEST CODE

    

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def myAccount(request):
    if request.user.is_authenticated:
        # Fetch user and bank details for the logged-in user
        user_details = Users.objects.get(id=request.user.id)  # Fetching the user's details
        bank_details = BankDetails.objects.filter(user_id=request.user.id).first()  # Fetching bank details

        return render(request, 'profile/my-account.html', {
            'user_details': user_details,
            'bank_details': bank_details
        })
    else:
        return redirect('login')

def members_exam(request):
    if request.user.is_authenticated:
        # Fetch user and bank details for the logged-in user
        user_details = Users.objects.get(id=request.user.id)  # Fetching the user's details

        return render(request, 'exam/index.html', {
            'user_details': user_details
        })
    else:
        return redirect('login')
    
def members_exam_mcq(request):
    if request.user.is_authenticated:
        # Fetch user and bank details for the logged-in user
        user_details = Users.objects.get(id=request.user.id)  # Fetching the user's details

        return render(request, 'exam/mcq.html', {
            'user_details': user_details
        })
    else:
        return redirect('login')


def update_user_details(request):
    if request.method == 'POST':
        user_details = Users.objects.get(id=request.user.id)
        user_details.first_name = request.POST['first_name']
        user_details.last_name = request.POST['last_name']
        user_details.email = request.POST['email']
        user_details.phone = request.POST['phone']
        user_details.gender = request.POST['gender']
        user_details.dob = request.POST['dob']
        user_details.state = request.POST['state']
        user_details.city = request.POST['city']
        user_details.pincode = request.POST['pincode']
        user_details.address = request.POST['address']
        user_details.save()

        messages.success(request, "User details updated successfully!")
        return redirect('my-account')  # Redirect back to the user profile page

def storeOrUpdateBankDetails(request):
    if request.method == "POST":
        user_id = request.user.id  # Get the logged-in user's ID
        
        # Check if the bank details already exist for this user
        bank_details, created = BankDetails.objects.get_or_create(user_id=user_id)
        
        # Update the bank details
        bank_details.account_holder_name = request.POST.get('account_holder_name')
        bank_details.re_enter_account_number = request.POST.get('re_enter_account_number')
        bank_details.account_number = request.POST.get('account_number')
        bank_details.ifsc_code = request.POST.get('ifsc_code')
        bank_details.city = request.POST.get('city')
        bank_details.state = request.POST.get('state')
        
        # Save the updated or newly created bank details
        bank_details.save()

        # Show success message
        messages.success(request, "Bank details have been updated successfully.")
        
        # Redirect to the my-account page after saving the details
        return redirect('my-account')

    # If not a POST request, redirect to my-account
    return redirect('my-account')



def update_doc_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        doc_type = data.get("docType")
        status = data.get("status")
        doc_id = data.get("docId")
        reject_note = data.get("rejectNote", "")

        if not doc_type or not status or not doc_id:
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        valid_statuses = ["Pending", "Approved", "Rejected"]
        if status not in valid_statuses:
            return JsonResponse({"error": "Invalid status"}, status=400)

        document = get_object_or_404(DocumentUpload, id=doc_id)

        status_field = f"{doc_type}_status"
        updated_at_field = f"{doc_type}_updated_at"
        reject_note_field = f"{doc_type}_reject_note"

        if not hasattr(document, status_field) or not hasattr(document, updated_at_field):
            return JsonResponse({"error": "Invalid document type"}, status=400)

        setattr(document, status_field, status)
        setattr(document, updated_at_field, now())

        # Store rejection note if status is Rejected
        if status == "Rejected" and hasattr(document, reject_note_field):
            setattr(document, reject_note_field, reject_note)

        document.save()

        return JsonResponse({"success": True, "message": f"Status updated to {status}!"})

    return JsonResponse({"error": "Invalid request method"}, status=405)
