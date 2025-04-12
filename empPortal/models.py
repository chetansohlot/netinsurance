from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from datetime import datetime
from django.utils.timezone import now

from django.conf import settings

class Roles(models.Model):
    roleGenID = models.CharField(max_length=255)
    roleName = models.CharField(max_length=255)
    roleDescription = models.CharField(max_length=255)

    class Meta:
        db_table = 'roles'
        
class Commission(models.Model):
    rm_name  =models.CharField(max_length=255, unique=True)
    member_id = models.CharField(max_length=20, null=True, blank=True)
    product_id = models.CharField(max_length=20, null=True, blank=True)
    sub_broker_id = models.CharField(max_length=20, null=True, blank=True)
    tp_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    od_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    net_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_by = models.CharField(max_length=10, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "commissions"

    def __str__(self):
        return f"Commission {self.id} - Insurer {self.member_id}"
    
    from django.db import models

class VehicleInfo(models.Model):
    customer_id = models.CharField(max_length=20, null=True, blank=True)  # Nullable as per SQL table
    registration_number = models.CharField(max_length=20, null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)  # Added registration_date
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)
    make = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    variant = models.CharField(max_length=50, null=True, blank=True)
    year_of_manufacture = models.IntegerField(null=True, blank=True)
    registration_state = models.CharField(max_length=50, null=True, blank=True)
    registration_city = models.CharField(max_length=50, null=True, blank=True)
    chassis_number = models.CharField(max_length=50, null=True, blank=True)
    engine_number = models.CharField(max_length=50, null=True, blank=True)
    claim_history = models.CharField(max_length=10, choices=[("Yes", "Yes"), ("No", "No")], null=True, blank=True)
    ncb = models.CharField(max_length=10, choices=[("Yes", "Yes"), ("No", "No")], default="No", null=True, blank=True)
    ncb_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    idv_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    policy_type = models.CharField(max_length=50, null=True, blank=True)
    policy_duration = models.CharField(max_length=50, null=True, blank=True)
    policy_companies = models.CharField(max_length=50, null=True, blank=True)
    addons = models.CharField(max_length=50, null=True, blank=True)

    # Additional fields from your request
    owner_name = models.CharField(max_length=255, null=True, blank=True)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    state_code = models.CharField(max_length=20, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    vehicle_category = models.CharField(max_length=100, null=True, blank=True)
    vehicle_class_description = models.CharField(max_length=100, null=True, blank=True)
    body_type_description = models.CharField(max_length=100, null=True, blank=True)
    vehicle_color = models.CharField(max_length=50, null=True, blank=True)
    vehicle_cubic_capacity = models.CharField(max_length=20, null=True, blank=True)
    vehicle_gross_weight = models.CharField(max_length=20, null=True, blank=True)
    vehicle_seating_capacity = models.CharField(max_length=20, null=True, blank=True)
    vehicle_fuel_description = models.CharField(max_length=50, null=True, blank=True)
    vehicle_owner_number = models.CharField(max_length=20, null=True, blank=True)
    rc_expiry_date = models.DateField(null=True, blank=True)
    rc_pucc_expiry_date = models.DateField(null=True, blank=True)
    insurance_company = models.CharField(max_length=255, null=True, blank=True)
    insurance_expiry_date = models.DateField(null=True, blank=True)
    insurance_policy_number = models.CharField(max_length=255, null=True, blank=True)

    active = models.BooleanField(default=True)  # 1 for active, 0 for inactive
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quotation_vehicle_info"

    def __str__(self):
        return f"VehicleInfo {self.registration_number} - {self.customer_id}"



class QuotationCustomer(models.Model):
    customer_id = models.CharField(max_length=20, unique=True)  # For values like CUS2343545
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    email_address = models.CharField(max_length=255, null=True, blank=True)
    quote_date = models.DateField(null=True, blank=True)
    name_as_per_pan = models.CharField(max_length=255, null=True, blank=True)
    pan_card_number = models.CharField(max_length=10, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)  # 1 for active, 0 for inactive
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # vehicleinfo = models.ForeignKey(VehicleInfo, on_delete=models.CASCADE)
    class Meta:
        db_table = "quotation_customers"

    def __str__(self):
        return f"QuotationCustomer {self.customer_id} - {self.name_as_per_pan}"
    
class Leads(models.Model):
    lead_id = models.CharField(max_length=20, unique=True)  # Unique customer identifier (e.g., CUS2343545)
    mobile_number = models.CharField(max_length=15)  # Customer's mobile number
    email_address = models.CharField(max_length=255)  # Customer's email address
    quote_date = models.CharField(max_length=25,null=True, blank=True)  # Quote date
    name_as_per_pan = models.CharField(max_length=255)  # Customer's name as per PAN
    pan_card_number = models.CharField(max_length=20, null=True, blank=True)  # PAN card number (optional)
    date_of_birth = models.CharField(max_length=25,null=True, blank=True)  # Customer's date of birth (optional)
    state = models.CharField(max_length=100, null=True, blank=True)  # State of the customer
    city = models.CharField(max_length=100, null=True, blank=True)  # City of the customer
    pincode = models.CharField(max_length=10, null=True, blank=True)  # Pincode of the customer
    address = models.TextField(null=True, blank=True)  # Address of the customer
    lead_description = models.TextField(null=True, blank=True)
    lead_source = models.CharField(max_length=25, null=True, blank=True)  
    referral_by = models.CharField(max_length=25, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the lead was created
    created_by = models.CharField(max_length=20, null=True, blank=True)  
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp when the lead was last updated
    status = models.CharField(max_length=50, default='new')  # Status of the lead (new, contacted, converted, etc.)
    lead_type = models.CharField(
        max_length=10, 
        choices=[('MOTOR', 'MOTOR'), ('HEALTH', 'HEALTH'), ('TERM', 'TERM')], 
        default='MOTOR'
    )  # Type of lead (MOTOR, HEALTH, TERM)

    class Meta:
        db_table = 'leads'  # This defines the database table name

    def __str__(self):
        return f"Lead - {self.name_as_per_pan}"


class QuotationVehicleDetail(models.Model):
    registration_number = models.CharField(max_length=20, null=True, blank=True)
    vehicle_details = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)  # Default to active (1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quotation_vehicle_details"

    def __str__(self):
        return f"Vehicle {self.registration_number or 'N/A'}"

from django.db import models
from django.utils.timezone import now



class PolicyDocument(models.Model):
    filename = models.CharField(max_length=255)
    insurance_provider = models.CharField(max_length=255)
    policy_number = models.CharField(max_length=255)
    policy_issue_date = models.CharField(max_length=255)
    policy_expiry_date = models.CharField(max_length=255)
    vehicle_number = models.CharField(max_length=255)
    holder_name = models.CharField(max_length=255)
    policy_period = models.CharField(max_length=255)
    filepath = models.CharField(max_length=255)
    policy_premium = models.CharField(max_length=255)
    policy_total_premium = models.CharField(max_length=255)
    sum_insured = models.CharField(max_length=255)
    rm_name = models.CharField(max_length=255)
    rm_id = models.IntegerField()
    extracted_text = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField()
    coverage_details = models.JSONField()
    policy_start_date = models.CharField(max_length=255)
    payment_status = models.CharField(max_length=255)
    policy_type = models.CharField(max_length=255)
    vehicle_type = models.CharField(max_length=255)
    vehicle_make = models.CharField(max_length=255)
    vehicle_model = models.CharField(max_length=255)
    vehicle_gross_weight = models.CharField(max_length=255)
    vehicle_manuf_date = models.CharField(max_length=255)
    gst = models.CharField(max_length=255)
    od_premium = models.CharField(max_length=255)
    tp_premium = models.CharField(max_length=255)
    bulk_log_id = models.IntegerField()
    od_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tp_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    insurer_tp_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    insurer_od_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    insurer_net_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    def __str__(self):
        return self.filename    
    
    # commission = models.ForeignKey(Commission, to_field="rm_name", on_delete=models.SET_NULL, null=True, blank=True)

    def commission(self):
         return Commission.objects.filter(member_id=self.rm_id ).first()

    @property
    def start_date(self):
        try:
            return datetime.strptime(self.policy_start_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
        except (ValueError, TypeError):
            return None

    @property
    def issue_date(self):
        try:
            return datetime.strptime(self.policy_issue_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
        except (ValueError, TypeError):
            return None

    @property
    def expiry_date(self):
        try:
            return datetime.strptime(self.policy_expiry_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
        except (ValueError, TypeError):
            return None
        
    class Meta:
        db_table = 'policydocument'


from django.db import models

class PolicyInfo(models.Model):
    policy_id = models.CharField(max_length=20, null=True, blank=True)

    # Basic Policy
    policy_number = models.CharField(max_length=100, null=True, blank=True)
    policy_issue_date = models.CharField(max_length=35, null=True, blank=True)
    policy_start_date = models.CharField(max_length=35, null=True, blank=True)
    policy_expiry_date = models.CharField(max_length=35, null=True, blank=True)

    # Insured Details
    insurer_name = models.CharField(max_length=255, null=True, blank=True)
    insured_mobile = models.CharField(max_length=15, null=True, blank=True)
    insured_email = models.CharField(max_length=255, null=True, blank=True)
    insured_address = models.TextField(null=True, blank=True)
    insured_pan = models.CharField(max_length=20, null=True, blank=True)
    insured_aadhaar = models.CharField(max_length=20, null=True, blank=True)

    # Policy Details
    insurance_company = models.CharField(max_length=255, null=True, blank=True)
    service_provider = models.CharField(max_length=255, null=True, blank=True)
    insurer_contact_name = models.CharField(max_length=255, null=True, blank=True)
    bqp = models.CharField(max_length=255, null=True, blank=True)
    pos_name = models.CharField(max_length=255, null=True, blank=True)
    branch_name = models.CharField(max_length=255, null=True, blank=True)
    supervisor_name = models.CharField(max_length=255, null=True, blank=True)
    policy_type = models.CharField(max_length=255, null=True, blank=True)
    policy_plan = models.CharField(max_length=255, null=True, blank=True)

    sum_insured = models.CharField(max_length=20, null=True, blank=True)
    od_premium = models.CharField(max_length=20, null=True, blank=True)
    tp_premium = models.CharField(max_length=20, null=True, blank=True)
    pa_count = models.CharField(max_length=20, default='0', null=True, blank=True)
    pa_amount = models.CharField(max_length=20, null=True, blank=True)
    driver_count = models.CharField(max_length=20, null=True, blank=True)
    driver_amount = models.CharField(max_length=20, null=True, blank=True)
    referral_by = models.CharField(max_length=50, null=True, blank=True)
    fuel_type = models.CharField(max_length=50, null=True, blank=True)
    be_fuel_amount = models.CharField(max_length=50, null=True, blank=True)
    gross_premium = models.CharField(max_length=50, null=True, blank=True)
    net_premium = models.CharField(max_length=50, null=True, blank=True)
    active = models.CharField(max_length=1, choices=[('0', 'Inactive'), ('1', 'Active')], default='1')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "policy_info"

    def __str__(self):
        return f"Policy {self.policy_number} - {self.policy_id}"

class AgentPaymentDetails(models.Model):
    policy_number = models.CharField(max_length=255)
    agent_name = models.CharField(max_length=255)
    agent_payment_mod = models.CharField(max_length=255)
    agent_payment_date = models.CharField(max_length=255)
    agent_amount = models.CharField(max_length=255)
    agent_remarks = models.CharField(max_length=255)
    agent_od_comm = models.CharField(max_length=255)
    agent_net_comm = models.CharField(max_length=255)
    agent_incentive_amount = models.CharField(max_length=255)
    agent_tds = models.CharField(max_length=255)
    agent_od_amount = models.CharField(max_length=255)
    agent_net_amount = models.CharField(max_length=255)
    agent_tp_amount = models.CharField(max_length=255)
    agent_total_comm_amount = models.CharField(max_length=255)
    agent_net_payable_amount = models.CharField(max_length=255)
    agent_tds_amount = models.CharField(max_length=255)
    active = models.CharField(max_length=1, choices=[('0', 'Inactive'), ('1', 'Active')], default='1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agent_payment_details'

    def __str__(self):
        return f"{self.agent_name} - {self.policy_number}"

class FranchisePayment(models.Model):
    policy_number = models.CharField(max_length=50, unique=True)
    franchise_od_comm = models.CharField(max_length=50, blank=True, null=True)
    franchise_net_comm = models.CharField(max_length=50, blank=True, null=True)
    franchise_tp_comm = models.CharField(max_length=50, blank=True, null=True)
    franchise_incentive_amount = models.CharField(max_length=50, blank=True, null=True)
    franchise_tds = models.CharField(max_length=50, blank=True, null=True)
    franchise_od_amount = models.CharField(max_length=50, blank=True, null=True)
    franchise_net_amount = models.CharField(max_length=50, blank=True, null=True)
    franchise_tp_amount = models.CharField(max_length=50, blank=True, null=True)
    franchise_total_comm_amount = models.CharField(max_length=50, blank=True, null=True)
    franchise_net_payable_amount = models.CharField(max_length=50, blank=True, null=True)
    franchise_tds_amount = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'franchise_payments'
        verbose_name = 'Franchise Payment'
        verbose_name_plural = 'Franchise Payments'

    def __str__(self):
        return f"Franchise Payment #{self.id}"



class PolicyUploadDoc(models.Model):
    policy_number = models.CharField(max_length=100)
    re_other_endorsement = models.FileField(upload_to='policy_doc/', null=True, blank=True)
    previous_policy = models.FileField(upload_to='policy_doc/', null=True, blank=True)
    kyc_document = models.FileField(upload_to='policy_doc/', null=True, blank=True)
    proposal_document = models.FileField(upload_to='policy_doc/', null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'policy_upload_docs'  # 👈 This sets the exact table name

    def __str__(self):
        return f"Documents for Policy: {self.policy_number}"



class InsurerPaymentDetails(models.Model):
    policy_number = models.CharField(max_length=100, unique=True)

    insurer_payment_mode = models.CharField(max_length=100, blank=True, null=True)
    insurer_payment_date = models.CharField(max_length=100, blank=True, null=True)
    insurer_amount = models.CharField(max_length=50, blank=True, null=True)
    insurer_remarks = models.TextField(blank=True, null=True)

    insurer_od_comm = models.CharField(max_length=50, blank=True, null=True)
    insurer_net_comm = models.CharField(max_length=50, blank=True, null=True)
    insurer_tp_comm = models.CharField(max_length=50, blank=True, null=True)
    insurer_incentive_amount = models.CharField(max_length=50, blank=True, null=True)
    insurer_tds = models.CharField(max_length=50, blank=True, null=True)

    insurer_od_amount = models.CharField(max_length=50, blank=True, null=True)
    insurer_net_amount = models.CharField(max_length=50, blank=True, null=True)
    insurer_tp_amount = models.CharField(max_length=50, blank=True, null=True)
    insurer_total_comm_amount = models.CharField(max_length=50, blank=True, null=True)
    insurer_net_payable_amount = models.CharField(max_length=50, blank=True, null=True)
    insurer_tds_amount = models.CharField(max_length=50, blank=True, null=True)

    active = models.CharField(max_length=1, choices=[('0', 'Inactive'), ('1', 'Active')], default='1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'insurer_payment_details'

    def __str__(self):
        return f"Insurer Payment for {self.policy_number}"
    
class PolicyVehicleInfo(models.Model):
    policy_number = models.CharField(max_length=100)

    vehicle_type = models.CharField(max_length=100, null=True, blank=True)
    vehicle_make = models.CharField(max_length=100, null=True, blank=True)
    vehicle_model = models.CharField(max_length=100, null=True, blank=True)
    vehicle_variant = models.CharField(max_length=100, null=True, blank=True)
    fuel_type = models.CharField(max_length=30, null=True, blank=True)  # Originally ENUM('Petrol', 'Diesel')

    gvw = models.CharField(max_length=50, null=True, blank=True)
    cubic_capacity = models.CharField(max_length=50, null=True, blank=True)
    seating_capacity = models.CharField(max_length=10, null=True, blank=True)

    registration_number = models.CharField(max_length=100, null=True, blank=True)
    engine_number = models.CharField(max_length=100, null=True, blank=True)
    chassis_number = models.CharField(max_length=100, null=True, blank=True)
    manufacture_year = models.CharField(max_length=4, null=True, blank=True)

    active = models.CharField(max_length=1, choices=[('0', 'Inactive'), ('1', 'Active')], default='1')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "policy_vehicle_info"

    def __str__(self):
        return f"Vehicle Info - {self.policy_number}"



class CommissionHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    member_id = models.CharField(max_length=20, null=True, blank=True)
    commission_id = models.BigIntegerField(null=True, blank=True)
    insurer_id = models.BigIntegerField(null=True, blank=True)
    rm_name = models.CharField(max_length=220, null=True, blank=True)
    product_id = models.CharField(max_length=10, null=True, blank=True)
    sub_broker_id = models.CharField(max_length=20, null=True, blank=True)
    tp_percentage = models.CharField(max_length=10, null=True, blank=True)
    od_percentage = models.CharField(max_length=10, null=True, blank=True)
    net_percentage = models.CharField(max_length=10, null=True, blank=True)
    created_by = models.CharField(max_length=10, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=now)
    active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "commissions_logs"

    def __str__(self):
        return f"Commission {self.id} - {self.od_percentage}% / {self.net_percentage}%"
        
 
class UsersManager(BaseUserManager):
    def create_user(self,email,phone=None,password=None,**extra_fields):
        # create and return a user with a email phone and password
        if not email:
            raise ValueError("The email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(email=email,phone=phone,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
        
    def create_super_user(self,email,phone=None,password=None,*extra_fields):
        # Creates and returns a superuser with an email, phone, and password.
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        return self.create_user(email,phone,password,**extra_fields)
    
class Users(AbstractBaseUser):
    user_gen_id = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    activation_status = models.CharField(max_length=10)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    email_otp = models.CharField(max_length=10, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone = models.BigIntegerField(null=True, blank=True)
    phone_otp = models.CharField(max_length=10, null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    gender = models.PositiveSmallIntegerField(null=True, blank=True) 
    pan_no = models.CharField(max_length=20, null=True, blank=True)
    exam_eligibility = models.PositiveSmallIntegerField(null=True, blank=True, default=0) 
    exam_attempt = models.PositiveSmallIntegerField(null=True, blank=True, default=0) 
    exam_pass = models.PositiveSmallIntegerField(null=True, blank=True, default=0) 
    exam_last_attempted_on = models.DateTimeField(null=True)
    dob = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    pincode = models.CharField(max_length=255)
    address = models.CharField(max_length=400)

    role = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True)
    role_name = models.CharField(max_length=255)
    branch_id = models.CharField(max_length=20, null=True, blank=True)
    department_id = models.CharField(max_length=20, null=True, blank=True)
    senior_id = models.CharField(max_length=20, null=True, blank=True)
    status = models.IntegerField(default=1)
    activation_status_updated_at = models.DateTimeField(null=True, blank=True)
    user_active_updated_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    password = models.CharField(max_length=255, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    user_active = models.BooleanField(default=True)
    is_login_available = models.BooleanField(default=False)
    is_reset_pass_available = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    
    objects = UsersManager()
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['user_name']
    class Meta:
        db_table = 'users'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def role_names(self):
        if self.role:
            return self.role.roleName
        return self.role_name

    def status_type(self):
        if self.status == 1:
            return 'Active'
        elif self.status == 2:
            return 'Inactive'
        else :
            return 'N/A'

class Franchises(models.Model):
    name = models.CharField(max_length=255, verbose_name="Franchise Name")
    contact_person = models.CharField(max_length=255, verbose_name="Contact Person")
    mobile = models.CharField(max_length=15, verbose_name="Mobile")
    email = models.EmailField(max_length=255, unique=True, verbose_name="Email")
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="City")
    state = models.CharField(max_length=100, null=True, blank=True, verbose_name="State")
    pincode = models.CharField(max_length=10, null=True, blank=True, verbose_name="Pincode")
    gst_number = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="GST Number")
    pan_number = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="PAN Number")
    registration_no = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Registration Number")
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active', verbose_name="Status")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'franchises'
        verbose_name = "Franchise"
        verbose_name_plural = "Franchises"

    def __str__(self):
        return self.name

    def status_type(self):
        return "Active" if self.status == "Active" else "Inactive"

from django.db import models
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name="Department Name")
    department_code = models.CharField(max_length=20, unique=True, verbose_name="Department Code")  # New Field
    head = models.CharField(max_length=255, verbose_name="Head of Department")
    head_of_department = models.CharField(max_length=255, verbose_name="Head of Department Name")  # New Field
    contact_person = models.CharField(max_length=255, verbose_name="Contact Person")  # New Field
    contact_number = models.CharField(max_length=15, verbose_name="Contact Number")
    email = models.EmailField(max_length=255, unique=True, verbose_name="Email")
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="City")
    state = models.CharField(max_length=100, null=True, blank=True, verbose_name="State")
    pincode = models.CharField(max_length=10, null=True, blank=True, verbose_name="Pincode")
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active', verbose_name="Status")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'departments'
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name

    def status_type(self):
        return "Active" if self.status == "Active" else "Inactive"


class Branch(models.Model):
    franchise_id = models.IntegerField(null=True, blank=True, verbose_name="Franchise ID")
    branch_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Branch Name")
    contact_person = models.CharField(max_length=255, null=True, blank=True, verbose_name="Contact Person")
    mobile = models.CharField(max_length=15, null=True, blank=True, verbose_name="Mobile")
    email = models.EmailField(max_length=255, null=True, blank=True, verbose_name="Email")

    address = models.TextField(null=True, blank=True, verbose_name="Address")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="City")
    state = models.CharField(max_length=100, null=True, blank=True, verbose_name="State")
    pincode = models.CharField(max_length=10, null=True, blank=True, verbose_name="Pincode")

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True, default='Active', verbose_name="Status")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'branches'
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.branch_name if self.branch_name else 'Unnamed Branch'}"

    def status_type(self):
        return "Active" if self.status == "Active" else "Inactive"

class UserFiles(models.Model):
    user = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='files')
    file_url = models.CharField(max_length=255, null=True, blank=True)  
    file_type = models.CharField(max_length=50, null=True, blank=True)  
    file_updated_time = models.DateTimeField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"Files for {self.user.user_name}"

    class Meta:
        db_table = 'user_files'



    # class Meta:
    #     db_table = "commissions"

    # def __str__(self):
    #     return f"Commission {self.id} - Insurer {self.member_id}"
    

class DocumentUpload(models.Model):
    user_id = models.IntegerField()  # Reference to user
    aadhaar_number = models.CharField(max_length=12, unique=True)
    aadhaar_card_front = models.FileField(upload_to='documents/')
    aadhaar_card_front_updated_at = models.DateTimeField(null=True, blank=True)
    aadhaar_card_front_status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending',
        null=True,
        blank=True
    )
    aadhaar_card_front_reject_note = models.CharField(max_length=255, null=True, blank=True)
    aadhaar_card_back = models.FileField(upload_to='documents/')
    aadhaar_card_back_updated_at = models.DateTimeField(null=True, blank=True)
    aadhaar_card_back_status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending',
        null=True,
        blank=True
    )
    aadhaar_card_back_reject_note = models.CharField(max_length=255, null=True, blank=True)
    pan_number = models.CharField(max_length=10, unique=True)
    upload_pan = models.FileField(upload_to='documents/')
    upload_pan_updated_at = models.DateTimeField(null=True, blank=True)
    upload_pan_status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending',
        null=True,
        blank=True
    )
    upload_pan_reject_note = models.CharField(max_length=255, null=True, blank=True)
    cheque_number = models.CharField(max_length=20, unique=True)
    upload_cheque = models.FileField(upload_to='documents/')
    upload_cheque_updated_at = models.DateTimeField(null=True, blank=True)
    upload_cheque_status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending',
        null=True,
        blank=True
    )
    upload_cheque_reject_note = models.CharField(max_length=255, null=True, blank=True)
    role_no = models.CharField(max_length=20, null=True, blank=True)
    tenth_marksheet = models.FileField(upload_to='documents/')
    tenth_marksheet_updated_at = models.DateTimeField(null=True, blank=True)
    tenth_marksheet_status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending',
        null=True,
        blank=True
    )
    tenth_marksheet_reject_note = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Documents for User {self.user_id}"

    class Meta:
        db_table = 'documents_upload'

class UnprocessedPolicyFiles(models.Model):
    policy_document = models.CharField(max_length=255)
    bulk_log_id = models.IntegerField()
    file_path = models.CharField(max_length=255)
    doc_name = models.CharField(max_length=255)
    error_message = models.TextField()
    status = models.CharField(max_length=50, choices=[("Pending", "Pending"), ("Reprocessed", "Reprocessed")], default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def created_date(self):
        return self.created_at.strftime("%d-%m-%Y %H:%M:%S") if self.created_at else None

    class Meta:
        db_table = 'unprocessed_policy_files'


class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    exam_eligibility = models.FloatField(null=True, blank=True, help_text="Eligibility score for the exam")
    exam_question_count = models.IntegerField(null=True, blank=True, help_text="Total number of questions in the exam")
    duration = models.IntegerField(help_text="Duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'exam'
        verbose_name = "Exam"
        verbose_name_plural = "Exams"
        

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text
    
    class Meta:
        db_table = 'question'
        verbose_name = "Question"
        verbose_name_plural = "Questions"

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)  # True for the correct option

    def __str__(self):
        return self.option_text
    
    class Meta:
        db_table = 'option'
        verbose_name = "Option"
        verbose_name_plural = "Options"


class UserAnswer(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def is_correct(self):
        return self.selected_option.is_correct if self.selected_option else False

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text}"
    
    class Meta:
        db_table = 'user_answer'
        verbose_name = "user_answers"
        verbose_name_plural = "User_answers"
        

# Exam Results Model (Stores Scores)
class ExamResult(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    total_questions = models.IntegerField(default=0)
    total_attempted_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=10, choices=[('passed', 'Passed'), ('failed', 'Failed')], default='failed')
    created_at = models.DateTimeField(auto_now_add=True)
    exam_submitted = models.IntegerField(default=1, help_text="1->start, 2->submitted")

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - {self.status}"

    class Meta:
        db_table = 'exam_result'
        verbose_name = "Exam_result"
        verbose_name_plural = "Exam_results"
        

class IrdaiAgentApiLogs(models.Model):
    url = models.URLField(null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    request_payload = models.TextField(null=True, blank=True)
    request_headers = models.TextField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id} - {self.url} ({self.response_status})"
    
    class Meta:
        db_table = 'irdai_agent_api_logs'
        

# class UploadedZip(models.Model):
#     file = models.FileField(upload_to='zips/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     campaign_name = models.CharField(max_length=255)
#     rm_id = models.CharField(max_length=100, null=True, blank=True)
#     rm_name = models.CharField(max_length=255, null=True, blank=True)
#     is_processed = models.BooleanField(default=False)
    
#     class Meta:
#         db_table = 'uploaded_zip'


class BulkPolicyLog(models.Model):
    camp_name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=255)
    count_total_files = models.IntegerField(default=0)
    count_not_pdf = models.IntegerField(default=0)
    count_pdf_files = models.IntegerField(default=0)
    count_error_pdf_files = models.IntegerField(default=0)
    count_error_process_pdf_files = models.IntegerField(default=0)
    count_uploaded_files = models.IntegerField(default=0)
    count_duplicate_files = models.IntegerField(default=0)
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.IntegerField()
    rm_id = models.IntegerField()
    def created_date(self):
        return self.created_at.strftime("%d-%m-%Y %H:%M:%S") if self.created_at else None
    
    class Meta:
        db_table = 'bulk_policy_log'
       
       
class UploadedZip(models.Model):
    file = models.FileField(upload_to='zips/')
    file_name = models.CharField(max_length=255, blank=True)
    file_url = models.URLField(blank=True)
    total_files = models.IntegerField(default=0)
    pdf_files_count = models.IntegerField(default=0)
    non_pdf_files_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    campaign_name = models.CharField(max_length=255)
    rm_id = models.CharField(max_length=100, null=True, blank=True)
    rm_name = models.CharField(max_length=255, null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    bulk_log = models.ForeignKey(BulkPolicyLog, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'uploaded_zip'

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_url = self.file.url  # Make sure MEDIA_URL is properly set
        super().save(*args, **kwargs)

    def __str__(self):
        return self.file_name or f"Uploaded Zip #{self.pk}"
    
class ExtractedFile(models.Model):
    zip_ref = models.ForeignKey(UploadedZip, on_delete=models.CASCADE)
    file_path = models.FileField(upload_to='pdf_files/')
    filename = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    is_extracted = models.BooleanField(default=False)
    extracted_at = models.DateTimeField(auto_now_add=True)
    policy = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE)
    file_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.filename
    
    class Meta:
        db_table = 'extracted_file'
        
class FileAnalysis(models.Model):
    zip = models.ForeignKey(UploadedZip, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    extracted_text = models.TextField()
    extracted_file = models.ForeignKey(ExtractedFile, on_delete=models.CASCADE)
    policy = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE)
    gpt_response = models.JSONField()
    status = models.CharField(max_length=50, default="pending")
    
    class Meta:
        db_table = 'file_analysis'
        
class ChatGPTLog(models.Model):
    prompt = models.TextField()
    response = models.TextField(blank=True, null=True)
    status_code = models.IntegerField(null=True, blank=True)
    is_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatGPT Log - {self.created_at}"
    
    class Meta:
        db_table = 'chatgptlog'
        managed = True
        verbose_name = 'ChatGPTLog'
        verbose_name_plural = 'ChatGPTLogs'