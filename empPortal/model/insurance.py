from django.db import models
from empPortal.model.StateCity import State,City

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
    pincode = models.IntegerField(null=True, blank=True, db_column='insurance_type_pincode')
    address = models.TextField(null=True, blank=True, db_column='insurance_type_address')
    commencement_date = models.DateField(null=True, blank=True, db_column='insurance_type_commencement_date')
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, db_column='insurance_type_state')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, db_column='insurance_type_city')


    def __str__(self):
        return self.insurance_company
    class Meta:
        db_table = 'insurance_companies'
