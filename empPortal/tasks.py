from .models import UploadedZip, FileAnalysis, ExtractedFile, BulkPolicyLog, Commission, PolicyDocument, UnprocessedPolicyFiles
import django, dramatiq, fitz, os, zipfile, requests, re, json, traceback, time, logging
from django.conf import settings
from django.utils import timezone
from django_q.tasks import async_task
OPENAI_API_KEY = settings.OPENAI_API_KEY
from django.db.models import F
from .utils import getUserNameByUserId, commisionRateByMemberId, insurercommisionRateByMemberId
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import filepath_to_uri
logger = logging.getLogger(__name__)

def create_bulk_log(file_id):
    zip_instance = UploadedZip.objects.get(id=file_id)
    
    # Initialize Counters
    error_pdf_files = 0
    error_process_pdf_files = 0
    uploaded_files = 0
    duplicate_files = 0
    bulk_log = BulkPolicyLog.objects.create(
        camp_name=zip_instance.campaign_name,
        file_name=zip_instance.file.name,
        count_total_files=zip_instance.total_files,
        count_not_pdf=zip_instance.non_pdf_files_count,
        count_pdf_files=zip_instance.pdf_files_count,
        file_url=zip_instance.file.url,
        count_error_pdf_files=0,
        count_error_process_pdf_files=0,
        count_uploaded_files=0,
        count_duplicate_files=0,
        rm_id=zip_instance.rm_id,  
        created_by=zip_instance.created_by.id,
        status=1,
    )
    zip_instance.bulk_log = bulk_log
    zip_instance.save()
    
    async_task('empPortal.tasks.process_zip_file', file_id)
    
def process_zip_file(zip_id):
    zip_instance = UploadedZip.objects.get(id=zip_id)

    zip_path = zip_instance.file.path
    
    pdf_file_ids = []
    
    extract_dir = os.path.join(settings.MEDIA_ROOT, 'extracted', str(zip_id))
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    for filename in os.listdir(extract_dir):
        if not filename.lower().endswith('.pdf'):
            continue  # Skip non-PDFs
 
        file_path = os.path.join(extract_dir, filename)
        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
        file_url = filepath_to_uri(os.path.join(settings.MEDIA_URL, relative_path))
        
        try:
            extracted = ExtractedFile.objects.create(
                zip_ref=zip_instance,
                file_path=file_path, 
                filename=filename,
                file_url=file_url
            )
        except Exception as e:
            logger.error(f"Error processing file_path {file_path}: {str(e)}")
            
        # add extracted_file_id in pdf_files
        pdf_file_ids.append(extracted.id)
        
    zip_instance.is_processed = True
    zip_instance.save()
    
    bulk_log = zip_instance.bulk_log
    bulk_log.status = 2
    bulk_log.save()
    
    # upload extracted files to policy document 
    async_task('empPortal.tasks.create_policy_documents_bulk', pdf_file_ids)

def create_policy_documents_bulk(file_ids):
    for file_id in file_ids:
        try:
            create_policy_document(file_id)  # call your create_policy_document function
            time.sleep(1)  # Delay between jobs
        except Exception as e:
            # Handle errors per file if needed
            logger.error(f"Error creating policy row {file_id}: {str(e)}")
    
def create_policy_document(file_id):
    file_obj = ExtractedFile.objects.get(id=file_id)
    rm_id = file_obj.zip_ref.bulk_log.rm_id
    bulk_log_id = file_obj.zip_ref.bulk_log.id
    rm_name = getUserNameByUserId(rm_id) if rm_id else None
    commision_rate = commisionRateByMemberId(rm_id)
    insurer_rate = insurercommisionRateByMemberId(1)
    if commision_rate:
        od_percentage = commision_rate.od_percentage
        net_percentage = commision_rate.net_percentage
        tp_percentage = commision_rate.tp_percentage
    else:
        od_percentage = 0.0
        net_percentage = 0.0
        tp_percentage = 0.0
        
    try:
        policy = PolicyDocument.objects.create(
            filename=file_obj.filename,
            filepath=file_obj.file_url,
            rm_id=rm_id,
            rm_name=rm_name,
            od_percent=od_percentage,
            tp_percent=tp_percentage,
            net_percent=net_percentage,
            insurer_tp_commission   = insurer_rate.tp_percentage,
            insurer_od_commission   = insurer_rate.od_percentage,
            insurer_net_commission  = insurer_rate.net_percentage,
            status=0,
            bulk_log_id=bulk_log_id
        )
    except Exception as e:
        logger.error(f"Error creating policy {file_id}: {str(e)}")
        
    file_obj.policy = policy
    file_obj.save()
    async_task('empPortal.tasks.extract_pdf_text_task', file_obj.id)
    

    
def extract_pdf_text_task(file_id):
    try:
        file_obj = ExtractedFile.objects.get(id=file_id)
    except ExtractedFile.DoesNotExist:
        logger.error(f"ExtractedFile with ID {file_id} not found.")
        return

    policy_obj = file_obj.policy
    policy_obj.status = 1
    policy_obj.save()

    pdf_path = file_obj.file_path.path if hasattr(file_obj.file_path, "path") else file_obj.file_path
    text = extract_text_from_pdf(pdf_path)
    try:
        file_analysis = FileAnalysis.objects.create(
            zip=file_obj.zip_ref,
            extracted_file=file_obj,
            policy=policy_obj,
            filename=file_obj.filename,
            extracted_text=text,
        )
    except Exception as e:
        logger.error(f"Error in file analysing file_id {file_id} : {str(e)}")
        
    def handle_extraction_error(reason):
        logger.error(f"[ERROR] {reason}")
        BulkPolicyLog.objects.filter(id=file_obj.zip_ref.bulk_log.id).update(
            count_error_pdf_files=F('count_error_pdf_files') + 1
        )
        try:
            UnprocessedPolicyFiles.objects.create(
                policy_document=policy_obj.id,
                doc_name=file_obj.filename,
                bulk_log_id=policy_obj.bulk_log_id,
                file_path=policy_obj.filepath,
                status=1,  # pending
            )
        except Exception as e:
            logger.error(f"Error in Unprocessing File file_id {file_id} : {str(e)}")
        file_analysis.status = 2  #failed in extarction
        file_analysis.save()

    try:
        if "Error" in text:
            handle_extraction_error(text)
        else:
            file_analysis.status = 1    #extraction complete
            file_analysis.save()

            file_obj.content = text.strip()
            file_obj.is_extracted = True
            file_obj.save()

            policy_obj.status = 2
            policy_obj.save()

            # Proceed to AI processing task (uncomment if needed)
            async_task('empPortal.tasks.process_text_from_chatgpt', file_analysis.id)

            logger.info(f"Text extracted successfully for: {file_obj.id}")

    except Exception as e:
        handle_extraction_error(f"Exception occurred during extraction: {e}")
   
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc)
        return text
    except Exception as e:
        logger.debug(f"Error extracting text: {e}")
        return f"Error extracting text: {e}"


def handle_ai_processing_failure(file_obj, policy_obj):
    try:
        BulkPolicyLog.objects.filter(id=file_obj.zip_ref.bulk_log.id).update(
            count_error_pdf_files=F('count_error_pdf_files') + 1
        )
        try:
            UnprocessedPolicyFiles.objects.create(
                policy_document=policy_obj.id,
                doc_name=file_obj.filename,
                bulk_log_id=policy_obj.bulk_log_id,
                file_path=policy_obj.filepath,
                status=2,  # error at AI Processing
            )
        except Exception as e:
            logger.error(f"error in ai_processing policy_id {policy_obj.id}")   

        file_obj.status = 3  # failed in AI Processing
        file_obj.save()
    except Exception as e:
        logger.error(f"Secondary error while logging AI failure: {e}")
        traceback.print_exc()


def process_text_from_chatgpt(file_id):
    try:
        file_obj = FileAnalysis.objects.get(id=file_id)
        policy_obj = file_obj.policy

        # Mark as processing
        policy_obj.status = 3
        policy_obj.save()

        response_json = process_text_with_chatgpt(file_obj.extracted_text)

        if hasattr(response_json, "error"):
            file_obj.gpt_response = response_json
            file_obj.save()
            handle_ai_processing_failure(file_obj, policy_obj)
        else:
            # Save GPT response and mark successful
            file_obj.gpt_response = response_json
            file_obj.status = 4
            file_obj.save()

            policy_obj.status = 4
            policy_obj.extracted_text = response_json
            policy_obj.save()

            async_task('empPortal.tasks.update_policy_data', file_id)

    except FileAnalysis.DoesNotExist:
        logger.error(f"FileAnalysis with ID {file_id} not found.")
    except Exception as e:
        logger.error(f"Error in PDF processed with AI: {e}")
        # traceback.print_exc()
        if 'file_obj' in locals() and 'policy_obj' in locals():
            handle_ai_processing_failure(file_obj, policy_obj)

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
        response = requests.post(api_url, json=data, headers=headers)
        if hasattr(response, "status_code") and response.status_code == 200:
            result = response.json()
            raw_output = result["choices"][0]["message"]["content"].strip()
            try:
                clean_json = re.sub(r"```json\n|\n```|```", "", raw_output).strip()
                return json.loads(clean_json)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error {str(e)}")
                return json.dumps({
                    "error": "JSON decode error",
                    "raw_output": raw_output,
                    "details": str(e)
                }, indent=4)
        else:
            return json.dumps({"error": f"API Error: {response.status_code}", "details": response.text}, indent=4)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed ,details: {str(e)}")
        return json.dumps({"error": "Request failed", "details": str(e)}, indent=4)


def update_policy_data(file_id):
    try:
        file_obj = FileAnalysis.objects.get(id=file_id)
        policy_obj = file_obj.policy
        policy_obj.status = 5
        policy_obj.save()
        bulk_log = file_obj.zip.bulk_log
        processed_text = file_obj.gpt_response or {}
        duplicate_files = 0
        uploaded_files = 0

        if not isinstance(processed_text, dict):
            processed_text = json.loads(processed_text)

        policy_number = processed_text.get("policy_number")
        if not policy_number:
            policy_obj.status = 4
            policy_obj.save()
            raise ValueError("Policy number is missing in processed_text.")

        # Check for duplicates
        if PolicyDocument.objects.filter(policy_number=policy_number).exists():
            bulk_log.count_duplicate_files += 1
            bulk_log.save()
            
            policy_obj.status = 7
            policy_obj.save()
            bulk_log.count_uploaded_files += 1
            bulk_log.save()
            if bulk_log.count_uploaded_files == bulk_log.count_pdf_files:
                bulk_log.status = 3
                bulk_log.save()
        else:
            try:
                
                vehicle_number = re.sub(r"[^a-zA-Z0-9]", "", processed_text.get("vehicle_number", ""))

                coverage_details = processed_text.get("coverage_details", [{}])
                if isinstance(coverage_details, list) and coverage_details:
                    first_coverage = coverage_details[0]
                elif isinstance(coverage_details, dict):
                    first_coverage = coverage_details
                else:
                    first_coverage = {}

                od_premium = first_coverage.get('own_damage', {}).get('premium', 0)
                tp_premium = first_coverage.get('third_party', {}).get('premium', 0)

                policy_doc = policy_obj
            
                policy_doc.insurance_provider = processed_text.get("insurance_company", "")
                policy_doc.vehicle_number = vehicle_number
                policy_doc.policy_number = policy_number
                policy_doc.policy_period = processed_text.get("policy_period", "")
                policy_doc.holder_name = processed_text.get("insured_name", "")
                policy_doc.policy_total_premium = processed_text.get("gross_premium", 0)
                policy_doc.policy_premium = processed_text.get("net_premium", 0)
                policy_doc.sum_insured = processed_text.get("sum_insured", 0)
                policy_doc.coverage_details = coverage_details
                policy_doc.policy_issue_date = processed_text.get("issue_date", "")
                policy_doc.policy_expiry_date = processed_text.get("expiry_date","")
                policy_doc.policy_start_date = processed_text.get("start_date","")
                policy_doc.payment_status = 'Confirmed'
                policy_doc.policy_type = processed_text.get('additional_details', {}).get('policy_type', "")
                vehicle_details = processed_text.get('vehicle_details', {})
                policy_doc.vehicle_type = vehicle_details.get('vehicle_type', "")
                policy_doc.vehicle_make = vehicle_details.get('make', "")
                policy_doc.vehicle_model = vehicle_details.get('model', "")
                policy_doc.vehicle_gross_weight = vehicle_details.get('vehicle_gross_weight', "")
                policy_doc.vehicle_manuf_date = vehicle_details.get('registration_year', "")
                policy_doc.gst = processed_text.get('gst_premium', 0)
                policy_doc.od_premium = od_premium
                policy_doc.tp_premium = tp_premium
                policy_doc.status = 6
                policy_doc.save()
                # Update Bulk Log
                bulk_log.count_uploaded_files += 1
                bulk_log.save()
                if bulk_log.count_uploaded_files == bulk_log.count_pdf_files:
                    bulk_log.status = 3
                    bulk_log.save()
            except Exception as e:
                logger.error(f"Error in Policy Update for policy_id {policy_obj.id}")
        

    except FileAnalysis.DoesNotExist:
        logger.error(f"File not found with the given ID")
        return json.dumps({"error": "File not found with the given ID."}, indent=4)
    except ObjectDoesNotExist as e:
        logger.error(f"Object not found Error: {str(e)}")
        return json.dumps({"error": "Object not found", "details": str(e)}, indent=4)
    except ValueError as ve:
        logger.error(f"Value error: {str(ve)}")
        return json.dumps({"error": "Value error", "details": str(ve)}, indent=4)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in GPT response for policy_id : {policy_obj.id}")
        return json.dumps({"error": "Invalid JSON in GPT response"}, indent=4)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for policy_id :{policy_obj.id} : error:{str(e)}")
        return json.dumps({"error": "Request failed", "details": str(e)}, indent=4)
    except Exception as e:
        logger.error(f"Unexpected error for policy_id :{policy_obj.id} : error:{str(e)}")
        return json.dumps({"error": "Unexpected error", "details": str(e)}, indent=4)
    