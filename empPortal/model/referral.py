from django.db import models

class Referral(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    mobile = models.CharField(max_length=15, unique=True, blank=True, null=True)
    referral_code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    ####  new add fields -----parth ####
    dob = models.DateField(null=True, blank=True)
    date_of_anniversary = models.DateField(null=True, blank=True)
    pan_card_number = models.CharField(max_length=10, null=True, blank=True)
    aadhar_no = models.CharField(max_length=15,null=True, blank=True)

    ####  new add fields -----parth ####

    user_role = models.CharField(max_length=100, null=True, blank=True)
    branch = models.CharField(max_length=100, null=True, blank=True)
    sales = models.CharField(max_length=100, null=True, blank=True)
    supervisor = models.CharField(max_length=100, null=True, blank=True)
    franchise = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)




    def __str__(self):
        return f"{self.name} - {self.referral_code}"

    class Meta:
        db_table = 'referrals'  # 👈 This tells Django to use your existing table
