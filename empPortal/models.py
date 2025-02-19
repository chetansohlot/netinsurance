from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from datetime import datetime

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
    tp_precent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_precent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.filename    
    
    # commission = models.ForeignKey(Commission, to_field="rm_name", on_delete=models.SET_NULL, null=True, blank=True)

    def commission(self):
        return Commission.objects.filter(rm_name=self.rm_name).first()

    @property

    def start_date(self):
        return self.policy_start_date.strftime("%d-%m-%Y") if self.policy_start_date else None
    
    def issue_date(self):
        return self.policy_issue_date.strftime("%d-%m-%Y") if self.policy_issue_date else None
    
    def expiry_date(self):
        return self.policy_expiry_date.strftime("%d-%m-%Y") if self.policy_expiry_date else None

    class Meta:
        db_table = 'policydocument'
        
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
    phone = models.BigIntegerField(null=True, blank=True)
    gender = models.PositiveSmallIntegerField(null=True, blank=True) 
    
    dob = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    pincode = models.CharField(max_length=255)
    address = models.CharField(max_length=400)

    role = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True)
    role_name = models.CharField(max_length=255)
    status = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    password = models.CharField(max_length=255, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
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


class UnprocessedPolicyFiles(models.Model):
    policy_document = models.CharField(max_length=255)
    bulk_log_id = models.IntegerField()
    file_path = models.CharField(max_length=255)
    doc_name = models.CharField(max_length=255)
    error_message = models.TextField()
    status = models.CharField(max_length=50, choices=[("Pending", "Pending"), ("Reprocessed", "Reprocessed")], default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'unprocessed_policy_files'
