from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect
from django.contrib import messages
from django.template import loader
from .models import Roles,Users,PolicyDocument,BulkPolicyLog
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

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()

def dashboard(request):
    if request.user.is_authenticated:
        user = request.user
        return render(request,'dashboard.html',{'user':user})
    else:
        return redirect('login')

def members(request):
    if request.user.is_authenticated:
        return render(request,'members.html')
    else:
        return redirect('login')

def memberView(request):
    if request.user.is_authenticated:
        return render(request,'member-view.html')
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
        users = Users.objects.all()
        return render(request,'user-and-roles.html',{'role_data':roles,'user_data':users})
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
        return render(request,'create-user.html',{'role_data':roles})
    else:
        return redirect('login')

def insertUser(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            username = request.POST.get('username', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            user_email = request.POST.get('email', '').strip()
            user_phone = request.POST.get('phone', 0).strip()
            role = request.POST.get('role', '').strip()
            password = request.POST.get('password', '').strip()

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
            user_status = 1

            user = Users(user_gen_id=user_gen_id, role_id=user_role_id, role_name=user_role_name, user_name=user_name, first_name=user_first_name, last_name=user_last_name, email=user_email, phone=user_phone, status=user_status, password=user_password)
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

def editUser(request,id):
    if request.user.is_authenticated:
        role_data = Roles.objects.all()
        user_data = Users.objects.filter(user_gen_id=id).first()
        return render(request,'edit-user.html',{'user_data':user_data,'role_data':role_data})
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
                messages.error(request,'Something Went Wrong. Kindly contact to administrator')
            
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            role_id = request.POST.get('role', '').strip()

            if not first_name:
                messages.error(request, 'First Name is required')
            elif len(first_name) < 3:
                messages.error(request, 'First Name must be at least 3 characters long')

            if last_name and len(last_name) < 3:
                messages.error(request, 'Last Name must be at least 3 characters long')

            if not role_id:
                messages.error(request, 'Role is required')
                
            if messages.get_messages(request):
                return redirect(request.META.get('HTTP_REFERER', '/'))

            role_data = Roles.objects.filter(id=role_id).first()
            role_name = role_data.roleName
            
            user_data = Users.objects.filter(id=user_id).first()
            
            if user_data is not None:
                user_data.role_id = role_id
                user_data.role_name = role_name
                user_data.first_name = first_name
                user_data.last_name = last_name
                user_data.save()
                
                messages.success(request, "User updated successfully.")
                return redirect('user-and-roles')
            else:       
                messages.error(request, 'Data Not Found. Kinldy connect to admin department')
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
    return render(request,'policy-mgt.html')

def bulkPolicyMgt(request):
    return render(request,'bulk-policy-mgt.html')

def browsePolicy(request):
    if request.method == "POST" and request.FILES.get("image"):
        
        image = request.FILES["image"]
        
         # Validate ZIP file format
        if not image.name.endswith(".pdf"):
            messages.error(request, "Invalid file format. Only pdf files are allowed.")
            return redirect("policy-mgt")
        
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        filepath = fs.path(filename)
        fileurl = fs.url(filename)
        extracted_text = extract_text_from_pdf(filepath)
        if "Error" in extracted_text:
            messages.error(request, extracted_text)
            return redirect('policy-mgt')
        
        processed_text = process_text_with_chatgpt(extracted_text)
        # processed_text = {"policy_number": "3005/O/379425038/00/000", "vehicle_number": "HR98P4781", "insured_name": "SHELLEY MUNJAL", "issue_date": "2025-02-01", "expiry_date": "2026-02-01", "premium_amount": "1,163.00", "sum_insured": "64,073.00", "policy_period": "1 year", "total_premium": "1,372.00", "insurance_company": "ICICI Lombard General Insurance Company Limited", "coverage_details": [{"benefit": "Basic OD Premium", "amount": "612.00"}, {"benefit": "Zero Depreciation (Silver)", "amount": "449.00"}, {"benefit": "Return to Invoice", "amount": "224.00"}]}
    
        if "error" in processed_text:
            PolicyDocument.objects.create(
                filename=image.name,
                extracted_text=processed_text,
                filepath=fileurl,
                rm_name=request.user.full_name,
                status=2,
            )
            
            messages.error(request, f"Failed to process policy")
            return redirect('policy-mgt')
        
        else:
            vehicle_number = re.sub(r'[^a-zA-Z0-9]','',processed_text['vehicle_number'])
            PolicyDocument.objects.create(
                filename=image.name,
                extracted_text=processed_text,
                filepath=fileurl,
                rm_name=request.user.full_name,
                insurance_provider=processed_text['insurance_company'],
                vehicle_number=vehicle_number,
                policy_number=processed_text['policy_number'],
                policy_issue_date=processed_text['issue_date'],
                policy_expiry_date=processed_text['expiry_date'],
                policy_period=processed_text['policy_period'],
                holder_name=processed_text['insured_name'],
                policy_total_premium=processed_text['total_premium'],
                policy_premium=processed_text['premium_amount'],
                sum_insured=processed_text['sum_insured'],
                coverage_details=processed_text['coverage_details'],
                status=1,
            )
            messages.success(request, "PDF uploaded and processed successfully.")
            
        return redirect('policy-data')
    
    else:
        messages.error(request, "Please upload a PDF file.")

    return redirect('policy-mgt')

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc)
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

def process_text_with_chatgpt(text):

    prompt = f"""
    Convert the following insurance document text into structured JSON format without any extra lines of comments:
    
    ```
    {text}
    ```

    The JSON should have this structure:
    
    {{
        "policy_number": "XXXXXX / XXXXX",   #complete policy number
        "vehicle_number": "XXXXXXXXXX",    
        "insured_name": "XXXXXX",
        "issue_date": "YYYY-MM-DD",
        "start_date": "YYYY-MM-DD",
        "expiry_date": "YYYY-MM-DD",
        "gross_premium": "XXXXX",
        "net_premium": "XXXX",
        "gst_premium": "XXXX",
        "sum_insured": "XXXXX",
        "policy_period": "XX Year(s)",
        "insurance_company": "XXXXX",
        "coverage_details": [
            {{
                "own_damage": {{
                    "premium": "XXXXX",
                    "additional_premiums:"XXXX",
                    "addons": [
                        {{ "name": "XXXX", "amount": "XXXX" }}
                    ]
                }},
                "third_party": {{
                    "premium": "XXXXX",
                    "additional_premiums:"XXXX",
                    "addons": [
                        {{ "name": "XXXX","amount": "XXXX" }}
                    ]
                }}
            }}
        ],
        "vehicle_details": {{
            "make": "XXXX",
            "model": "XXXX",
            "variant": "XXXX",
            "registration_year": "YYYY",
            "engine_number": "XXXXXXXXXXXX",
            "chassis_number": "XXXXXXXXXXXX",
            "fuel_type": "XXXX",
            "cubic_capacity": "XXXX CC",
            "vehicle_gross_weight": "XXX"   #in kg if commercial vehicle
            "vehicle_type": "XXXX XXXX", # type of vehicle pvt or commercial
            "commercial_vehicle_detail":"XXXX XXXX" # if vehicle is commercial then detail in text format of commercial type 
        }},
        "additional_details": {{
            "policy_type": "XXXX",  #it must be type from Motor Stand Alone OD /Motor-Liability Only / Motor-Package Policy
            "ncb": "XX%",
            "addons": [
                "XXXX",
                "XXXX"
            ],
            "previous_insurer": "XXXX",
            "previous_policy_number": "XXXX"
        }},
        "contact_information": {{
            "address": "XXXXXX",
            "phone_number": "XXXXXXXXXX",
            "email": "XXXXXX"
        }}
    }}
    
    

    If some details are missing, leave them as `"Not Found"`.
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
        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            raw_output = result["choices"][0]["message"]["content"].strip()
            clean_json = re.sub(r"```json\n|\n```", "", raw_output).strip()
            return json.loads(clean_json)
        else:
            return json.dumps({"error": f"API Error: {response.status_code}", "details": response.text}, indent=4)
    
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": "Request failed", "details": str(e)}, indent=4)
    
def policyData(request):
    policy_data = PolicyDocument.objects.filter(status=1).order_by('-id')

    
    for data in policy_data:
        if isinstance(data.extracted_text, str):
            try:
                data.extracted_text = json.loads(data.extracted_text)  # Convert JSON string to dictionary
            except json.JSONDecodeError:
                data.extracted_text = {}  # Handle invalid JSON case
    return render(request,'policy-data.html',{"policy_data":policy_data})

def editPolicy(request,id):
    if request.user.is_authenticated:
        policy_data = PolicyDocument.objects.filter(id=id).first()
        return render(request,'edit-policy.html',{'policy_data':policy_data})
    else:
        return redirect('login')

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
    policy_issue_date = request.POST.get('policy_issue_date', '').strip()
    policy_premium = request.POST.get('policy_premium', '').strip()
    policy_total_premium = request.POST.get('policy_total_premium', '').strip()
    policy_period = request.POST.get('policy_period', '').strip()
    rm_name = request.POST.get('rm_name', '').strip()

    if not policy_id:
        messages.error(request, 'Something Went Wrong. Kindly contact the administrator.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Ensure policy number is unique
    if PolicyDocument.objects.filter(policy_number=policy_number).exclude(id=policy_id).exists():
        messages.error(request, "Policy Number already exists.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    policy_data = PolicyDocument.objects.filter(id=policy_id).first()

    if policy_data:
        # Remove the trailing comma (fixes the tuple issue)
        policy_data.insurance_provider = insurer_name
        policy_data.policy_number = policy_number
        policy_data.vehicle_number = vehicle_reg_no
        policy_data.holder_name = policy_holder_name
        policy_data.policy_issue_date = policy_issue_date
        policy_data.policy_premium = policy_premium
        policy_data.policy_total_premium = policy_total_premium
        policy_data.policy_period = policy_period
        policy_data.rm_name = rm_name
        policy_data.save()

        messages.success(request, 'Policy updated successfully.')
        return redirect('policy-data')

    messages.error(request, 'No Data Found')
    return redirect(request.META.get('HTTP_REFERER', '/'))

def bulkBrowsePolicy(request):
    if request.method == "POST" and request.FILES.get("zip_file"):
        zip_file = request.FILES["zip_file"]
        camp_name = request.POST.get("camp_name")  # Use POST instead of GET

        # Validate ZIP file format
        if not zip_file.name.endswith(".zip"):
            messages.error(request, "Invalid file format. Only ZIP files are allowed.")
            return redirect("bulk-policy-mgt")

        # Save ZIP file
        fs = FileSystemStorage()
        filename = fs.save(zip_file.name, zip_file)
        zip_filepath = fs.path(filename)  # Get full path of the saved ZIP file
        file_url = fs.url(filename)
         
        timestamp = str(int(time.time()))  # Unique folder name
        extract_path = os.path.join(fs.location, "extracted", timestamp)
        os.makedirs(extract_path, exist_ok=True)

        # Extract ZIP file
        try:
            with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                zip_ref.extractall(extract_path)
        except zipfile.BadZipFile:
            messages.error(request, "Invalid ZIP file. Please upload a valid ZIP.")
            return redirect("bulk-policy-mgt")

        # Initialize Counters
        total_files = 0
        not_pdf = 0
        pdf_files = 0
        error_pdf_files = 0
        error_process_pdf_files = 0
        uploaded_files = 0

        for file_name in os.listdir(extract_path):
            total_files += 1
            file_path = os.path.join(extract_path, file_name)
            file_path_url = os.path.join(fs.base_url, "extracted", timestamp, file_name)
            if file_name.endswith(".pdf"):
                pdf_files += 1
                extracted_text = extract_text_from_pdf(file_path)

                if "Error" in extracted_text:
                    error_pdf_files += 1
                    messages.error(request, f"Error processing {file_name}: {extracted_text}")
                    continue

                processed_text = process_text_with_chatgpt(extracted_text)

                if "error" in processed_text:
                    error_process_pdf_files += 1
                    PolicyDocument.objects.create(
                        filename=file_name,
                        extracted_text=processed_text,
                        filepath=file_path_url,
                        rm_name=request.user.full_name,
                        status=2,
                    )
                    messages.error(request, f"Error processing policy {file_name}: {processed_text}")
                else:
                    vehicle_number = re.sub(r"[^a-zA-Z0-9]", "", processed_text.get("vehicle_number", ""))
                    PolicyDocument.objects.create(
                        filename=file_name,
                        extracted_text=processed_text,
                        filepath=file_path_url,
                        rm_name=request.user.full_name,
                        insurance_provider=processed_text.get("insurance_company", ""),
                        vehicle_number=vehicle_number,
                        policy_number=processed_text.get("policy_number", ""),
                        policy_issue_date=processed_text.get("issue_date", None),
                        policy_expiry_date=processed_text.get("expiry_date", None),
                        policy_period=processed_text.get("policy_period", ""),
                        holder_name=processed_text.get("insured_name", ""),
                        policy_total_premium=processed_text.get("total_premium", 0),
                        policy_premium=processed_text.get("premium_amount", 0),
                        sum_insured=processed_text.get("sum_insured", 0),
                        coverage_details=processed_text.get("coverage_details", ""),
                        status=1,
                    )
                    uploaded_files += 1
            else:
                not_pdf += 1

        # Insert log entry in BulkPolicyLog
        BulkPolicyLog.objects.create(
            camp_name=camp_name,
            file_name=filename,
            count_total_files=total_files,
            count_not_pdf=not_pdf,
            count_pdf_files=pdf_files,
            file_url=file_url,
            count_error_pdf_files=error_pdf_files,
            count_error_process_pdf_files=error_process_pdf_files,
            count_uploaded_files=uploaded_files,
            status=1,  # Mark as completed
        )

        messages.success(
            request,
            f"ZIP file uploaded and extracted successfully. "
            f"Total Files: {total_files}, PDFs: {pdf_files}, Non-PDFs: {not_pdf}, "
            f"Uploaded: {uploaded_files}, Extraction Errors: {error_pdf_files}, Processing Errors: {error_process_pdf_files}",
        )

        return redirect("policy-data")

    else:
        messages.error(request, "Invalid request. Only ZIP files are allowed.")

    return redirect("bulk-policy-mgt")

def bulkUploadLogs(request):
    logs = BulkPolicyLog.objects.order_by('-id')
    return render(request,'bulk-upload-logs.html',{'logs': logs})

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