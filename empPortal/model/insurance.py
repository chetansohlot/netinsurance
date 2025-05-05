from django.db import models

class Insurance(models.Model):
    ACTIVE_CHOICES = [
        ('Inactive', 'Inactive'),
        ('Active', 'Active'),
    ]

    insurance_company = models.CharField(max_length=255)
    #active = models.CharField(max_length=1, choices=ACTIVE_CHOICES, default='1')
    active = models.CharField(max_length=8, choices=ACTIVE_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.insurance_company


    class Meta:
        db_table = 'insurance_companies'
