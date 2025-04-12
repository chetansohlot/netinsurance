from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect
from django.contrib import messages
from django.template import loader
from .models import Roles,Users, Department,PolicyDocument,BulkPolicyLog, PolicyInfo, Branch, UserFiles,UnprocessedPolicyFiles, Commission, Branch, FileAnalysis, ExtractedFile, ChatGPTLog
from django.contrib.auth import authenticate, login ,logout
from django.core.files.storage import FileSystemStorage
import re, logging
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
from datetime import datetime
from io import BytesIO
from django.db.models import Q
from .models import UploadedZip
from django.core.files.base import ContentFile
from .tasks import process_zip_file
from django_q.tasks import async_task
from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import now
from empPortal.model import Referral

OPENAI_API_KEY = settings.OPENAI_API_KEY
logger = logging.getLogger(__name__)

app = FastAPI()


def dashboard(request):
    if request.user.is_authenticated:
        user = request.user

        if request.user.role_id != 1:
            policy_qs = PolicyDocument.objects.filter(status=6, rm_id=request.user.id)
        else:
            policy_qs = PolicyDocument.objects.filter(status=6)

        policy_count = policy_qs.count()
        total_revenue = policy_qs.aggregate(Sum('policy_premium'))['policy_premium__sum'] or 0

        return render(request, 'dashboard.html', {
            'user': user,
            'policy_count': policy_count,
            'total_revenue': total_revenue,
        })
    else:
        return redirect('login')



def billings(request):
    if request.user.is_authenticated:
        return render(request,'billings.html')
    else:
        return redirect('login')

def claimTracker(request):
    if request.user.is_authenticated:
        return render(request,'claim-tracker.html')
    else:
        return redirect('login')

def checkout(request):
    if request.user.is_authenticated:
        return render(request,'checkout.html')
    else:
        return redirect('login')

def addMember(request):
    if request.user.is_authenticated:
        return render(request,'add-member.html')
    else:
        return redirect('login')
    
def userAndRoles(request):
    if request.user.is_authenticated:
        roles = Roles.objects.all()
        
        # Exclude users with role_id = 1 and ensure valid users
        users = Users.objects.exclude(role_id=1).select_related('role')

        # Create a list of users with their respective senior's name
        user_list = []
        for user in users:
            senior_name = "N/A"  # Default value if no senior is found
            
            # Ensure senior_id is valid (not None, not empty, not zero)
            if user.senior_id and str(user.senior_id).strip() not in ["", "None", "null"]:
                senior = Users.objects.filter(id=user.senior_id).first()
                if senior:
                    senior_name = f"{senior.first_name} {senior.last_name}"
            
            user_list.append({
                'id': user.id if user.id else '',
                'user_gen_id': user.user_gen_id if user.user_gen_id else '',  # Ensure it's not None
                'full_name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'phone': user.phone,
                'role_name': user.role_name,
                'status': user.status,
                'senior_name': senior_name  # Include senior's name or "N/A"
            })

        return render(request, 'user-and-roles.html', {
            'role_data': roles,
            'user_data': user_list
        })
    else:
        return redirect('login')



def newRole(request):
    if request.user.is_authenticated:
        return render(request, 'new-role.html')
    else:
        return redirect('login')

def insertRole(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            role_name = request.POST.get('role_name', '').strip()
            role_description = request.POST.get('description', '').strip()

            # Validation
            if not role_name:
                messages.error(request, 'Role Name is required')
                return render(request, 'new-role.html')

            if not role_description:
                messages.error(request, 'Description is required')
                return render(request, 'new-role.html')

            if len(role_name) < 3:
                messages.error(request, 'Role name must be at least 3 characters long')
                return render(request, 'new-role.html')

            if len(role_description) > 255:
                messages.error(request, "Description must be under 255 characters.")
                return render(request, 'new-role.html')

            if Roles.objects.filter(roleName=role_name).exists():
                messages.error(request, "Role name already exists.")
                return render(request, 'new-role.html')

            last_role = Roles.objects.all().order_by('-roleGenID').first()
            if last_role and last_role.roleGenID.startswith('RL-'):
                last_id = int(last_role.roleGenID.split('-')[1])
                new_roleGenID = f"RL-{last_id + 1:04d}"
            else:
                new_roleGenID = 'RL-0001'

            rl = Roles(roleGenID=new_roleGenID, roleName=role_name, roleDescription=role_description)
            rl.save()

            messages.success(request, "Role added successfully.")
            return redirect('user-and-roles')

        messages.error(request, 'Invalid URL')
        return render(request, 'new-role.html') 
    else:
        return redirect('login')

def createUser(request):
    if request.user.is_authenticated:
        roles = Roles.objects.all()
        branches = Branch.objects.all().order_by('-created_at')
        departments = Department.objects.all().order_by('-created_at')
        return render(request,'create-user.html',{'role_data':roles, 'branches':branches, 'departments':departments})
    else:
        return redirect('login')


def get_users_by_role(request):
    if request.method == "GET" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        role_id = request.GET.get('role_id', '')
        manager_id = request.GET.get('manager_id', '')

        if role_id and role_id.isdigit():
            role_id = int(role_id)

            if role_id == 3:  # Fetch Branch Managers
                users = Users.objects.filter(role_id=2).values('id', 'first_name', 'last_name')
                role_name = "Manager"
            elif role_id == 5 and manager_id == '':  # Fetch Regional Managers
                users = Users.objects.filter(role_id=2).values('id', 'first_name', 'last_name')
                role_name = "Manager"
            elif role_id == 5 and manager_id != '' and manager_id.isdigit():  # Fetch Team Leaders under selected Manager
                users = Users.objects.filter(senior_id=manager_id).values('id', 'first_name', 'last_name')
                role_name = "Team Leader"
            else:
                return JsonResponse({'users': []}, status=200)

            users_list = [
                {'id': user['id'], 'full_name': f"{user['first_name']} {user['last_name']} ({role_name})".strip()}
                for user in users
            ]
            return JsonResponse({'users': users_list}, status=200)

        return JsonResponse({'users': []}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def insertUser(request):
    if request.user.is_authenticated:
        
        if request.user.role_id != 1:
            messages.error(request, "You do not have permission to add users.")
            return redirect('user-and-roles')  # Redirect unauthorized users
        
        if request.method == "POST":
            username = request.POST.get('username', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            user_email = request.POST.get('email', '').strip()
            user_phone = request.POST.get('phone', 0).strip()
            role = request.POST.get('role', '').strip()
            branch = request.POST.get('branch', '').strip()
            department = request.POST.get('department', '').strip()
            senior = request.POST.get('senior', '').strip()  # New senior field
            password = request.POST.get('password', '').strip()


            if role == '1':
                messages.error(request, "You cannot create a user with this role Admin.")
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            if not username:
                messages.error(request, 'Username is required')
            elif len(username) < 3:
                messages.error(request, 'Username must be at least 3 characters long')
            elif Users.objects.filter(user_name=username).exists():
                messages.error(request,'This username is already exist')

            if not first_name:
                messages.error(request, 'First Name is required')
            elif len(first_name) < 3:
                messages.error(request, 'First Name must be at least 3 characters long')
            if not branch or not branch.isdigit():
                messages.error(request, 'Valid Branch is required')

            if last_name and len(last_name) < 3:
                messages.error(request, 'Last Name must be at least 3 characters long')

            if not user_email:
                messages.error(request, 'Email is required')
            elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user_email):
                messages.error(request, 'Invalid email format')
            elif Users.objects.filter(email=user_email).exists():
                messages.error(request,'This email is already exist')

            if not user_phone:
                messages.error(request, 'Mobile No is required')
            elif not user_phone.isdigit():
                messages.error(request, 'Mobile No must contain only numbers')
            elif user_phone[0] <= '5':
                messages.error(request, 'Mobile No must start with a number greater than 5')
            elif len(user_phone) != 10:
                messages.error(request,'Mobile No must be of 10 digits')
            elif Users.objects.filter(phone=user_phone).exists():
                messages.error(request, 'This mobile number already exists.')

            if not role:
                messages.error(request, 'Role is required')
                
            if not password:
                messages.error(request, 'Password is required')
            elif len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long')
            
            if messages.get_messages(request):
                return redirect(request.META.get('HTTP_REFERER', '/'))

            last_user = Users.objects.all().order_by('-id').first()
            if last_user and last_user.user_gen_id.startswith('UR-'):
                last_user_gen_id = int(last_user.user_gen_id.split('-')[1])
                new_gen_id = f"UR-{last_user_gen_id+1:04d}"
            else:
                new_gen_id = "UR-0001"
                
            role_data = Roles.objects.filter(id=role).first()
            role_name = role_data.roleName
            
            user_password = make_password(password)

            
            user_gen_id = new_gen_id
            user_role_id = role
            user_role_name = role_name
            user_name = username
            user_first_name = first_name
            user_last_name = last_name
            user_email = user_email
            user_phone = user_phone
            user_password = user_password
            branch_id = branch
            department_id = department
            senior_id = senior
            user_status = 1

            user = Users(
                user_gen_id=user_gen_id, 
                role_id=user_role_id, 
                role_name=user_role_name, 
                user_name=user_name, 
                first_name=user_first_name, 
                last_name=user_last_name, 
                email=user_email, 
                phone=user_phone, 
                branch_id=branch_id, 
                department_id=department_id, 
                senior_id=senior_id, 
                status=user_status, 
                password=user_password
            )
            user.save()
            
            messages.success(request, "User added successfully.")
            return redirect('user-and-roles')

        messages.error(request, 'Invalid URL')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        return redirect('login')

def editRole(request,id):
    if request.user.is_authenticated:
        role_data = Roles.objects.filter(roleGenID=id).first()
        return render(request,'edit-role.html',{'role_data':role_data})
    else:
        return redirect('login')
    
def editUser(request, id):
    if request.user.is_authenticated:
        role_data = Roles.objects.all()
        branches = Branch.objects.all().order_by('branch_name')
        departments = Department.objects.all().order_by('name')
        user_data = Users.objects.filter(user_gen_id=id).first()

        senior_users = []  # Default empty list
        if user_data and user_data.role_id == 3:  
            senior_users = Users.objects.filter(role_id=2).values('id', 'first_name', 'last_name')

        return render(request, 'edit-user.html', {
            'user_data': user_data,
            'role_data': role_data,
            'branches': branches,
            'departments': departments,
            'senior_users': senior_users
        })
    else:
        return redirect('login')

def updateRole(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            if request.POST['role_id'] == '':
                messages.error(request,'Something Went Wrong. Kindly contact to administrator')
            
            role_id = request.POST.get('role_id', '').strip()
            role_name = request.POST.get('role_name', '').strip()
            role_description = request.POST.get('description', '').strip()

            # Validation
            if not role_name:
                messages.error(request, 'Role Name is required')

            if not role_description:
                messages.error(request, 'Description is required')

            if len(role_name) < 3:
                messages.error(request, 'Role name must be at least 3 characters long')

            if len(role_description) > 255:
                messages.error(request, "Description must be under 255 characters.")

            if Roles.objects.filter(roleName=role_name).exclude(id=role_id).exists():
                messages.error(request, "Role name already exists.")

            
            if messages.get_messages(request):
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            role_data = Roles.objects.filter(id=role_id).first()
            
            if role_data is not None:
                role_data.roleName = role_name
                role_data.description = role_description
                role_data.save()
                
                messages.success(request, 'Role updated successfully.')
                return redirect('user-and-roles')
            
            else:
                messages.error(request, 'No Data Found')
                return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, 'Invalid URL')
            return redirect('user-and-roles')
    else:
        return redirect('login')
   
def updateUser(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            user_id = request.POST.get('user_id', '').strip()

            if not user_id:
                messages.error(request, 'Something Went Wrong. Kindly contact the administrator')

            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            role_id = request.POST.get('role', '').strip()
            branch_id = request.POST.get('branch', '').strip()
            department_id = request.POST.get('department', '').strip()
            senior_id = request.POST.get('senior', '').strip()

            if role_id == '1':
                messages.error(request, "You cannot update a user with this role Admin.")
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            if not first_name:
                messages.error(request, 'First Name is required')
            elif len(first_name) < 3:
                messages.error(request, 'First Name must be at least 3 characters long')

            if last_name and len(last_name) < 3:
                messages.error(request, 'Last Name must be at least 3 characters long')

            if not role_id:
                messages.error(request, 'Role is required')

            if not branch_id:
                messages.error(request, 'Branch is required')

            if messages.get_messages(request):
                return redirect(request.META.get('HTTP_REFERER', '/'))

            role_data = Roles.objects.filter(id=role_id).first()
            role_name = role_data.roleName if role_data else ''

            user_data = Users.objects.filter(id=user_id).first()

            if user_data is not None:
                user_data.role_id = role_id
                user_data.role_name = role_name
                user_data.first_name = first_name
                user_data.last_name = last_name
                user_data.branch_id = branch_id
                user_data.department_id = department_id
                user_data.senior_id = senior_id  # Update senior_id
                user_data.save()

                messages.success(request, "User updated successfully.")
                return redirect('user-and-roles')
            else:
                messages.error(request, 'Data Not Found. Kindly connect to admin department')
                return redirect('user-and-roles')
        else:
            messages.error(request, 'Invalid URL')
            return redirect('user-and-roles')
    else:
        return redirect('login')
    
def updateUserStatus(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            user_id = request.POST.get('user_id', '').strip()
            
            if not user_id:
                messages.error(request,'Something Went Wrong. Kindly contact to administrator')
            
            user_data = Users.objects.filter(id=user_id).first()
            
            if user_data is not None:
                user_data.status = 2 if user_data.status == 1 else 1
                user_data.save()
                
                messages.success(request, "Status updated successfully.")
                return redirect('user-and-roles')
            else:       
                messages.error(request, 'Data Not Found. Kinldy connect to admin department')
                return redirect('user-and-roles')
        else:
            messages.error(request, 'Invalid URL')
            return redirect('user-and-roles')
    else:
        return redirect('login')
    
def policyMgt(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    return render(request,'policy/policy-mgt.html')

def bulkPolicyMgt(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        return redirect('login')
    rms = Users.objects.all()
    return render(request,'policy/bulk-policy-mgt.html',{'users':rms})

def browsePolicy(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    if request.method == "POST" and request.FILES.get("image"):
        image = request.FILES["image"]
         # Validate ZIP file format
        if not image.name.lower().endswith(".pdf"):
            messages.error(request, "Invalid file format. Only pdf files are allowed.")
            return redirect("policy-mgt")
        
        if image.size > 2 * 1024 * 1024:  # 2MB = 1024*1024*2 bytes
            messages.error(request, "File too large. Maximum allowed size is 2 MB.")
            return redirect("policy-mgt")

        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        filepath = fs.path(filename)
        fileurl = fs.url(filename)
        extracted_text = extract_text_from_pdf(filepath)
        if "Error" in extracted_text:
            messages.error(request, extracted_text)
            return redirect('policy-mgt')
        
        member_id = request.user.id
       
        commision_rate = commisionRateByMemberId(member_id)
        insurer_rate = insurercommisionRateByMemberId(1)
        if commision_rate:
            od_percentage = commision_rate.od_percentage
            net_percentage = commision_rate.net_percentage
            tp_percentage = commision_rate.tp_percentage
        else:
            od_percentage = 0.0
            net_percentage = 0.0
            tp_percentage = 0.0

        
        processed_text = process_text_with_chatgpt(extracted_text)
        if "error" in processed_text:
            PolicyDocument.objects.create(
                filename=image.name,
                extracted_text=processed_text,
                filepath=fileurl,
                rm_name=request.user.first_name,
                rm_id=request.user.id,
                od_percent=od_percentage,
                tp_percent=tp_percentage,
                net_percent=net_percentage,
                insurer_tp_commission   = insurer_rate.tp_percentage,
                insurer_od_commission   = insurer_rate.od_percentage,
                insurer_net_commission  = insurer_rate.net_percentage,
                status=3,
            )
            
            messages.error(request, f"Failed to process policy")
            return redirect('policy-mgt')
        else:
            policy_number = processed_text.get("policy_number", None)
            if PolicyDocument.objects.filter(policy_number=policy_number).exists():
                messages.error(request, "Policy Number already exists.")
                return redirect('policy-mgt')
            
            vehicle_number = re.sub(r"[^a-zA-Z0-9]", "", processed_text.get("vehicle_number", ""))
            coverage_details = processed_text.get("coverage_details", [{}])
            od_premium = coverage_details.get('own_damage', {}).get('premium', 0)
            tp_premium = coverage_details.get('third_party', {}).get('premium', 0)
            PolicyDocument.objects.create(
                filename=image.name,
                extracted_text=processed_text,
                filepath=fileurl,
                rm_name=request.user.full_name,
                rm_id=request.user.id,
                insurance_provider=processed_text.get("insurance_company", ""),
                vehicle_number=vehicle_number,
                policy_number=policy_number,
                policy_issue_date=processed_text.get("issue_date", ""),
                policy_expiry_date=processed_text.get("expiry_date", ""),
                policy_start_date=processed_text.get('start_date', ""),
                policy_period=processed_text.get("policy_period", ""),
                holder_name=processed_text.get("insured_name", ""),
                policy_total_premium=processed_text.get("gross_premium", 0),
                policy_premium=processed_text.get("net_premium", 0),
                sum_insured=processed_text.get("sum_insured", 0),
                coverage_details=processed_text.get("coverage_details", ""),
                payment_status='Confirmed',
                policy_type=processed_text.get('additional_details', {}).get('policy_type', ""),
                vehicle_type=processed_text.get('vehicle_details', {}).get('vehicle_type', ""),
                vehicle_make=processed_text.get('vehicle_details', {}).get('make', ""),                      
                vehicle_model=processed_text.get('vehicle_details', {}).get('model', ""),                      
                vehicle_gross_weight=processed_text.get('vehicle_details', {}).get('vehicle_gross_weight', ""),                     
                vehicle_manuf_date=processed_text.get('vehicle_details', {}).get('registration_year', ""),                      
                gst=processed_text.get('gst_premium', 0),                      
                od_premium=od_premium,
                tp_premium=tp_premium,
                od_percent=od_percentage,
                tp_percent=tp_percentage,
                net_percent=net_percentage,
                insurer_tp_commission   = insurer_rate.tp_percentage,
                insurer_od_commission   = insurer_rate.od_percentage,
                insurer_net_commission  = insurer_rate.net_percentage,

                status=6,
            )
            messages.success(request, "PDF uploaded and processed successfully.")
            
        return redirect('policy-data')
    
    else:
        messages.error(request, "Please upload a PDF file.")

    return redirect('policy-mgt')

def parse_date(date_str):
    try:
        if date_str:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return None

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc)
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

def process_text_with_chatgpt(text):

    prompt = f"""
    Convert the following insurance document text into a structured JSON format without any extra comments. Ensure that numerical values (like premiums and sum insured) are **only numbers** without extra text.  if godigit replace the amount of od and tp from one another 

    ```
    {text}
    ```

    The JSON should have this structure:
    
    {{
        "policy_number": "XXXXXX/XXXXX",   # complete policy number if insurance_company is godigit policy number is 'XXXXXX / XXXXX' in this format   e
        "vehicle_number": "XXXXXXXXXX",
        "insured_name": "XXXXXX",
        "issue_date": "YYYY-MM-DD H:i:s",     
        "start_date": "YYYY-MM-DD H:i:s",
        "expiry_date": "YYYY-MM-DD H:i:s",
        "gross_premium": XXXX,    
        "net_premium": XXXX,
        "gst_premium": XXXX,
        "sum_insured": XXXX,
        "policy_period": "XX Year(s)",
        "insurance_company": "XXXXX",
        "coverage_details": {{
            "own_damage": {{
                "premium": XXXX,
                "additional_premiums": XXXX,
                "addons": {{
                    "addons": [
                        {{ "name": "XXXX", "amount": XXXX }},
                        {{ "name": "XXXX", "amount": XXXX }}
                    ],
                    "discounts": [
                        {{ "name": "XXXX", "amount": XXXX }},
                        {{ "name": "XXXX", "amount": XXXX }}
                    ]
                }}
            }},
            "third_party": {{
                "premium": XXXX,
                "additional_premiums": XXXX,
                "addons": {{
                    "addons": [
                        {{ "name": "XXXX", "amount": XXXX }},
                        {{ "name": "XXXX", "amount": XXXX }}
                    ],
                    "discounts": [
                        {{ "name": "XXXX", "amount": XXXX }},
                        {{ "name": "XXXX", "amount": XXXX }}
                    ]
                }}
            }}
        }},
        "vehicle_details": {{
            "make": "XXXX",
            "model": "XXXX",
            "variant": "XXXX",
            "registration_year": YYYY,
            "engine_number": "XXXXXXXXXXXX",
            "chassis_number": "XXXXXXXXXXXX",
            "fuel_type": "XXXX",     # diesel/petrol/cng/lpg/ev 
            "cubic_capacity": XXXX,  
            "vehicle_gross_weight": XXXX,   # in kg
            "vehicle_type": "XXXX XXXX",    # private / commercial
            "commercial_vehicle_detail": "XXXX XXXX"    
        }},
        "additional_details": {{
            "policy_type": "XXXX",        # motor stand alone policy/ motor third party liablity policy / motor pakage policy   only in these texts
            "ncb": XX,     # in percentage
            "addons": ["XXXX", "XXXX"], 
            "previous_insurer": "XXXX",
            "previous_policy_number": "XXXX"
        }},
        "contact_information": {{
            "address": "XXXXXX",
            "phone_number": "XXXXXXXXXX",
            "email": "XXXXXX"
        }}
    }}
    
    If some details are missing, leave them as blank.
    """

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    try:
        log_entry = ChatGPTLog.objects.create(
            prompt=prompt,
            created_at=now()
        )
    except:
        logger.error(f"Error In ChatGPT logentry")
        
    try:
        response = requests.post(api_url, json=data, headers=headers)

        if hasattr(response, "status_code"):
            log_entry.status_code = response.status_code
            
        if hasattr(response, "status_code") and response.status_code == 200:

            result = response.json()
            raw_output = result["choices"][0]["message"]["content"].strip()
            
            try:
                clean_json = re.sub(r"```json\n|\n```|```", "", raw_output).strip()
                
                parsed_json = json.loads(clean_json)
                log_entry.response = json.dumps(parsed_json, indent=4)
                log_entry.is_successful = True
                log_entry.save()
                return parsed_json
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error {str(e)}")
                log_entry.response = raw_output
                log_entry.error_message = f"JSON decode error: {str(e)}"
                log_entry.save()
                
                return json.dumps({
                    "error": "JSON decode error",
                    "raw_output": raw_output,
                    "details": str(e)
                }, indent=4)
        else:
            log_entry.error_message = response.text
            log_entry.save()
            return json.dumps({"error": f"API Error: {response.status_code}", "details": response.text}, indent=4)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed ,details: {str(e)}")
        
        log_entry.error_message = str(e)
        log_entry.save()
        
        return json.dumps({"error": "Request failed", "details": str(e)}, indent=4)



from django.core.paginator import Paginator

def policyData(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.id
    role_id = Users.objects.filter(id=user_id).values_list('role_id', flat=True).first()

    # Base queryset
    if role_id != 1:
        queryset = PolicyDocument.objects.filter(status=6, rm_id=user_id)
    else:
        queryset = PolicyDocument.objects.filter(status=6)

    # Handle search filters
    search_field = request.GET.get('search_field')
    search_query = request.GET.get('search_query')

    if search_field and search_query:
        if search_field == 'policy_number':
            queryset = queryset.filter(policy_number__icontains=search_query)
        elif search_field == 'vehicle_number':
            queryset = queryset.filter(vehicle_number__icontains=search_query)
        elif search_field == 'holder_name':
            queryset = queryset.filter(holder_name__icontains=search_query)
        elif search_field == 'insurance_provider':
            queryset = queryset.filter(insurance_provider__icontains=search_query)

    # Convert extracted_text JSON string to dict
    for data in queryset:
        if isinstance(data.extracted_text, str):
            try:
                data.extracted_text = json.loads(data.extracted_text)
            except json.JSONDecodeError:
                data.extracted_text = {}

    # Base queryset
    if role_id != 1:
        policy_count = PolicyDocument.objects.filter(status=6, rm_id=user_id).count()
    else:
        policy_count = PolicyDocument.objects.filter(status=6).count()

    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'policy/policy-data.html', {
        "page_obj": page_obj,
        "policy_count": policy_count,
        "search_field": search_field,
        "search_query": search_query,
        "per_page": per_page,
    })


import os
from django.conf import settings
from urllib.parse import urljoin



def editPolicy(request, id):
    if request.user.is_authenticated:
        policy_data = PolicyDocument.objects.filter(id=id).first()
        policy_number = policy_data.policy_number
        policy = PolicyInfo.objects.filter(policy_number=policy_number).first()
        pdf_path = get_pdf_path(request, policy_data.filepath)
        branches = Branch.objects.filter(status='Active').order_by('-created_at')
        referrals = Referral.objects.all()

        extracted_data = {}
        if policy_data and policy_data.extracted_text:
            if isinstance(policy_data.extracted_text, str):
                try:
                    extracted_data = json.loads(policy_data.extracted_text)
                except json.JSONDecodeError:
                    extracted_data = {}
            elif isinstance(policy_data.extracted_text, dict):
                extracted_data = policy_data.extracted_text  # already a dict
        return render(request, 'policy/edit-policy.html', {
            'policy_data': policy_data,
            'policy': policy,
            'referrals': referrals,
            'branches': branches,
            'pdf_path': pdf_path,
            'extracted_data': extracted_data,
            'file_path': policy_data.filepath,
        })
    else:
        return redirect('login')
  
  
def get_pdf_path(request, filepath):
    """
    Returns the absolute URI to the PDF file if it exists, otherwise an empty string.
    """
    if not filepath:
        return ""

    filepath_str = str(filepath).replace('\\', '/')
    rel_path = ""
    
    if 'media/' in filepath_str:
        rel_path = filepath_str.split('media/')[-1]
        absolute_file_path = os.path.join(settings.MEDIA_ROOT, rel_path)

        if not os.path.exists(absolute_file_path):
            # Try fallback inside empPortal/media
            fallback_path = os.path.join(settings.BASE_DIR, 'empPortal', 'media', rel_path)
            if os.path.exists(fallback_path):
                absolute_file_path = fallback_path
            else:
                rel_path = ""  # File not found in either location

        if rel_path:
            media_url_path = urljoin(settings.MEDIA_URL, rel_path.replace('\\', '/'))
            return request.build_absolute_uri(media_url_path)

    return ""

def parse_date(date_str):
    """Convert DD-MM-YYYY to YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date() if date_str else None
    except ValueError:
        return None  # Handle invalid date formats gracefully

def updatePolicy(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method != "POST":
        messages.error(request, 'Invalid URL')
        return redirect('policy-data')
    
    policy_id = request.POST.get('policy_id', '').strip()
    insurer_name = request.POST.get('insurer_name', '').strip()
    policy_number = request.POST.get('policy_number', '').strip()
    vehicle_reg_no = request.POST.get('vehicle_reg_no', '').strip()
    policy_holder_name = request.POST.get('policy_holder_name', '').strip()
    policy_issue_date = parse_date(request.POST.get('policy_issue_date', '').strip())
    policy_start_date = parse_date(request.POST.get('policy_start_date', '').strip())
    policy_expiry_date = parse_date(request.POST.get('policy_expiry_date', '').strip())
    policy_premium = request.POST.get('policy_premium', '').strip()
    policy_total_premium = request.POST.get('policy_total_premium', '').strip()
    policy_gst = request.POST.get('policy_gst', '').strip()
    policy_period = request.POST.get('policy_period', '').strip()
    rm_name = request.POST.get('rm_name', '').strip()
    vehicle_type = request.POST.get('vehicle_type', '').strip()
    vehicle_make = request.POST.get('vehicle_make', '').strip()
    vehicle_model = request.POST.get('vehicle_model', '').strip()
    gross_weight = request.POST.get('gross_weight', '').strip()
    mgf_year = request.POST.get('mgf_year', '').strip()
    sum_insured = request.POST.get('sum_insured', '').strip()
    od_premium = request.POST.get('od_premium', '').strip()
    tp_premium = request.POST.get('tp_premium', '').strip()


    if not policy_id:
        messages.error(request, 'Something Went Wrong. Kindly contact the administrator.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Ensure policy number is unique
    if PolicyDocument.objects.filter(policy_number=policy_number).exclude(id=policy_id).exists():
        messages.error(request, "Policy Number already exists.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    policy_data = PolicyDocument.objects.filter(id=policy_id).first()

    if policy_data:
        policy_data.insurance_provider = insurer_name
        policy_data.policy_number = policy_number
        policy_data.vehicle_number = vehicle_reg_no
        policy_data.holder_name = policy_holder_name
        policy_data.policy_issue_date = policy_issue_date
        policy_data.policy_start_date = policy_start_date
        policy_data.policy_expiry_date = policy_expiry_date
        policy_data.policy_premium = policy_premium
        policy_data.policy_total_premium = policy_total_premium
        policy_data.gst = policy_gst
        policy_data.policy_period = policy_period
        policy_data.vehicle_type = vehicle_type
        policy_data.vehicle_make = vehicle_make
        policy_data.vehicle_model = vehicle_model
        policy_data.vehicle_gross_weight = gross_weight
        policy_data.vehicle_manuf_date = mgf_year
        policy_data.sum_insured = sum_insured
        policy_data.od_premium = od_premium
        policy_data.tp_premium = tp_premium
        policy_data.rm_name = rm_name
        policy_data.save()

        messages.success(request, 'Policy updated successfully.')
        return redirect('policy-data')

    messages.error(request, 'No Data Found')
    return redirect(request.META.get('HTTP_REFERER', '/'))

def bulkBrowsePolicy(request):
    if request.user.is_authenticated:
        if request.method == "POST" and request.FILES.get("zip_file"):
            zip_file = request.FILES["zip_file"]
            camp_name = request.POST.get("camp_name") 
            rm_id = request.POST.get("rm_id")
            
            # Validate ZIP file format
            if not zip_file or not zip_file.name.lower().endswith(".zip"):
                messages.error(request, "Invalid file format. Only ZIP files are allowed.")
                return redirect("bulk-policy-mgt")
            
            if zip_file.size > 50 * 1024 * 1024:
                messages.error(request, "File too large. Maximum allowed size is 50 MB.")
                return redirect("bulk-policy-mgt")  
            
            try:
                zip_bytes = BytesIO(zip_file.read())
                with zipfile.ZipFile(zip_bytes) as zf:
                    file_list = zf.infolist()
                    total_files = len(file_list)
                    pdf_files = [f for f in file_list if f.filename.lower().endswith(".pdf")]
                    non_pdf_files = [f for f in file_list if not f.filename.lower().endswith(".pdf")]
                    
                    pdf_count = len(pdf_files)
                    non_pdf_count = len(non_pdf_files)
                    
                    if total_files > 50:
                        messages.error(request, "ZIP contains more than 50 files.")
                        return redirect("bulk-policy-mgt")
                    
                    if non_pdf_files:
                        messages.error(request, "ZIP must contain only PDF files.")
                        return redirect("bulk-policy-mgt")
            except zipfile.BadZipFile:
                messages.error(request, "The uploaded ZIP file is corrupted or invalid.")
                return redirect("bulk-policy-mgt")
            
            if not camp_name:
                messages.error(request, "Campaign Name is mandatory.")
                return redirect("bulk-policy-mgt")
            
            rm_name = getUserNameByUserId(rm_id) if rm_id else None
            
            zip_instance = UploadedZip.objects.create(
                file=ContentFile(zip_bytes.getvalue(), name=zip_file.name),
                campaign_name=camp_name,
                rm_id=rm_id,
                rm_name=rm_name,
                created_by=request.user,
                total_files=total_files,        
                pdf_files_count=pdf_count,      
                non_pdf_files_count=non_pdf_count  
            )
                        
            # Start background processing
            async_task('empPortal.tasks.create_bulk_log', zip_instance.id)
            
            messages.success(request, "ZIP uploaded successfully. Processing started in background.")
            return redirect("bulk-upload-logs")
        else:
            return redirect("bulk-policy-mgt")
    else:
        return redirect('login')

def bulkUploadLogs(request):

    id  = request.user.id
        # Fetch policies
    role_id = Users.objects.filter(id=id,status=1).values_list('role_id', flat=True).first()
    if role_id != 1:
     logs =  BulkPolicyLog.objects.filter(rm_id=id).exclude(rm_id__isnull=True).order_by('-id')
    else:
      logs = BulkPolicyLog.objects.all().order_by('-id')
    

    return render(request,'policy/bulk-upload-logs.html',{'logs': logs})

def changePassword(request):
    return render(request, 'change-password.html')

def updatePassword(request):
    if request.method == "POST":
        user = request.user
        current_password = request.POST.get("current_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not current_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("change-password")

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("change-password")

        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect("change-password")

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        messages.success(request, "Your password has been updated successfully.")
        return redirect("dashboard") 

    return redirect("change-password")

def userLogout(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("login")
    else:
        return redirect("login")
        
def failedPolicyUploadView(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    # Correct the filter logic
    unprocessable_files = UnprocessedPolicyFiles.objects.filter(bulk_log_id=id, status=1)

    return render(request, 'policy/unprocessable-files.html', {'files': unprocessable_files})
  
def bulkPolicyView(request, id):
    if not request.user.is_authenticated or request.user.is_active != 1:
        return redirect('login')
    # Correct the filter logic
    policy_files = PolicyDocument.objects.filter(bulk_log_id=id)

    return render(request, 'policy/policy-files.html', {'files': policy_files,'log_id':id})
  
def reprocessBulkPolicies(request):
    if not request.user.is_authenticated and request.user.is_active == 1:
        return redirect('login')
    if request.method == "POST":
        unprocessFiles = request.POST.get('reprocess_bulk_policies', '')
        
        if not unprocessFiles:
            messages.error(request,'Select Atleast One Policy')
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        unprocessFilesList = unprocessFiles.split(",") if unprocessFiles else []
        
        for file_id in unprocessFilesList:
            try:
                file_data = UnprocessedPolicyFiles.objects.get(id=file_id)

                individual_file_id = file_data.policy_document 
                bulk_log_id = file_data.bulk_log_id
                
                stored_path = file_data.file_path
                
                if stored_path.startswith("/media/"):
                    stored_path = stored_path.replace("/media/", "", 1)

                file_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, stored_path))

                extracted_text = extract_text_from_pdf(file_path)

                if "Error" in extracted_text:
                    continue
                
                processed_text = process_text_with_chatgpt(extracted_text)
                if "error" in processed_text:
                    policy_doc = PolicyDocument.objects.filter(id=individual_file_id).first()
                    policy_doc.extracted_text = processed_text
                    policy_doc.save()
                    
                    unprocess_policy = UnprocessedPolicyFiles.objects.filter(id=file_id).first()
                    unprocess_policy.error_message=processed_text
                    unprocess_policy.save()
                    
                else:
                    policy_number = processed_text.get("policy_number", None)
                    if PolicyDocument.objects.filter(policy_number=policy_number).exists():
                        continue
                    
                    vehicle_number = re.sub(r"[^a-zA-Z0-9]", "", processed_text.get("vehicle_number", ""))
                    coverage_details = processed_text.get("coverage_details", [{}])
                    first_coverage = coverage_details if coverage_details else {}

                    od_premium = first_coverage.get('own_damage', {}).get('premium', 0)
                    tp_premium = first_coverage.get('third_party', {}).get('premium', 0)
                    
                    policy_doc = PolicyDocument.objects.filter(id=individual_file_id).first()
                    
                    policy_doc.extracted_text = processed_text
                    policy_doc.insurance_provider = processed_text.get("insurance_company", "")
                    policy_doc.vehicle_number = vehicle_number
                    policy_doc.policy_number=policy_number
                    policy_doc.policy_issue_date=processed_text.get("issue_date", None)
                    policy_doc.policy_expiry_date=processed_text.get("expiry_date", None)
                    policy_doc.policy_period=processed_text.get("policy_period", "")
                    policy_doc.holder_name=processed_text.get("insured_name", "")
                    policy_doc.policy_total_premium=processed_text.get("gross_premium", 0)
                    policy_doc.policy_premium=processed_text.get("net_premium", 0)
                    policy_doc.sum_insured=processed_text.get("sum_insured", 0)
                    policy_doc.coverage_details=processed_text.get("coverage_details", "")
                    policy_doc.policy_start_date=processed_text.get('start_date', None)
                    policy_doc.payment_status='Confirmed'
                    policy_doc.policy_type=processed_text.get('additional_details', {}).get('policy_type', "")
                    policy_doc.vehicle_type=processed_text.get('vehicle_details', {}).get('vehicle_type', "")
                    policy_doc.vehicle_make=processed_text.get('vehicle_details', {}).get('make', "")               
                    policy_doc.vehicle_model=processed_text.get('vehicle_details', {}).get('model', "")
                    policy_doc.vehicle_gross_weight=processed_text.get('vehicle_details', {}).get('vehicle_gross_weight', "") 
                    policy_doc.vehicle_manuf_date=processed_text.get('vehicle_details', {}).get('registration_year', "")                  
                    policy_doc.gst=processed_text.get('gst_premium', 0)
                    policy_doc.od_premium=od_premium
                    policy_doc.tp_premium=tp_premium
                    policy_doc.status=6
                    policy_doc.save()
                    
                    bulk_log = BulkPolicyLog.objects.filter(id=bulk_log_id).first()
                    bulk_log.count_error_process_pdf_files -= 1
                    bulk_log.count_uploaded_files += 1
                    bulk_log.save()
                    
                    unprocess_policy = UnprocessedPolicyFiles.objects.filter(id=file_id).first()
                    unprocess_policy.error_message=''
                    unprocess_policy.status="Reprocessed"
                    unprocess_policy.save()
                    
            except UnprocessedPolicyFiles.DoesNotExist:
                print(f"File with ID {file_id} not found")

        return redirect('bulk-upload-logs')
    else:
        messages.error(request, 'Invalid URL')
        return redirect(request.META.get('HTTP_REFERER', '/'))

def continueBulkPolicies(request):
    if not request.user.is_authenticated or request.user.is_active != 1:
        return redirect('login')
    if request.method == "POST":
        log_id = request.POST.get('log_id', None)
        if log_id == None:
            return redirect('bulk-upload-logs')
        
        reprocessFiles = request.POST.get('continue_bulk_policies', '')
        
        if not reprocessFiles:
            messages.error(request,'Select Atleast One Policy')
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        reprocessFilesList = reprocessFiles.split(",") if reprocessFiles else []
        
        for file_id in reprocessFilesList:
            try:
                file_data = PolicyDocument.objects.get(id=file_id)
                file_status = file_data.status
                if file_status == 5 or file_status == 3:
                    file_obj = FileAnalysis.objects.filter(policy_id=file_id).last()
                    async_task('empPortal.tasks.process_text_from_chatgpt', file_obj.id)
               
                if file_status == 1:
                    file_obj = ExtractedFile.objects.filter(policy_id=file_id).last()
                    async_task('empPortal.tasks.extract_pdf_text_task', file_obj.id)
               
            except PolicyDocument.DoesNotExist:
                print(f"File with ID {file_id} not found in Policy Details")
            
            except FileAnalysis.DoesNotExist:
                print(f"File with ID {file_id} not found in analysing")
                
            except ExtractedFile.DoesNotExist:
                print(f"File with ID {file_id} not found in extraction")

        return redirect('bulk-policies',log_id)
    else:
        messages.error(request, 'Invalid URL')
        return redirect(request.META.get('HTTP_REFERER', '/'))

def getUserNameByUserId(user_id):
    try:
        return Users.objects.get(id=user_id).full_name
    except Users.DoesNotExist:
        return None

def commisionRateByMemberId(member_id):
    commission_data = Commission.objects.filter(member_id=member_id).first()
    return commission_data

def insurercommisionRateByMemberId(member_id):
    commission_data = Commission.objects.filter(member_id=member_id).first()
    return commission_data