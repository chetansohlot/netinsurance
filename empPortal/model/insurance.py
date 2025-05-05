from django.db import models

class Insurance(models.Model):
    ACTIVE_CHOICES = [
        ('0', 'Inactive'),
        ('1', 'Active'),
    ]

    insurance_company = models.CharField(max_length=255)
    active = models.CharField(max_length=1, choices=ACTIVE_CHOICES, default='1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.insurance_company


    class Meta:
        db_table = 'insurance'
