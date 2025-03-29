from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from datetime import datetime
from django.utils.timezone import now

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

    class Meta:
        db_table = "quotation_customers"

    def __str__(self):
        return f"QuotationCustomer {self.customer_id} - {self.name_as_per_pan}"

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


class VehicleInfo(models.Model):
    customer_id = models.CharField(max_length=20, null=True, blank=True)  # Nullable as per SQL table
    registration_number = models.CharField(max_length=20, null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)  # Added registration_date
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)
    make = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    variant = models.CharField(max_length=50, null=True, blank=True)
    year_of_manufacture = models.IntegerField(null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
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
    active = models.BooleanField(default=True)  # 1 for active, 0 for inactive
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quotation_vehicle_info"

    def __str__(self):
        return f"VehicleInfo {self.registration_number} - {self.customer_id}"




class PolicyDocument(models.Model):
    filename = models.CharField(max_length=255)
    insurance_provider = models.CharField(max_length=255)
    policy_number = models.CharField(max_length=255)
    policy_issue_date = models.DateTimeField()
    policy_expiry_date = models.DateTimeField()
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
    policy_start_date = models.DateTimeField()
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
        return self.policy_start_date.strftime("%d-%m-%Y") if self.policy_start_date else None
    
    def issue_date(self):
        return self.policy_issue_date.strftime("%d-%m-%Y") if self.policy_issue_date else None
    
    def expiry_date(self):
        return self.policy_expiry_date.strftime("%d-%m-%Y") if self.policy_expiry_date else None

    class Meta:
        db_table = 'policydocument'

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
    
    dob = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    pincode = models.CharField(max_length=255)
    address = models.CharField(max_length=400)

    role = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True)
    role_name = models.CharField(max_length=255)
    branch_id = models.CharField(max_length=20, null=True, blank=True)
    senior_id = models.CharField(max_length=20, null=True, blank=True)
    status = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    password = models.CharField(max_length=255, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
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
