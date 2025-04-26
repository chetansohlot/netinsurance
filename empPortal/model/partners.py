from django.db import models

class Partner(models.Model):
    STATUS_CHOICES = [
        ('0', 'Requested'),
        ('1', 'Document Verification'),
        ('2', 'In-Training'),
        ('3', 'In-Exam'),
        ('4', 'Activated'),
        ('5', 'Inactive'),
        ('6', 'Rejected'),
    ]

    user_id = models.IntegerField(null=True, blank=True)
    pan_no = models.CharField(max_length=20, blank=True, null=True)
    aadhaar_no = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    name = models.CharField(max_length=100)
    partner_status = models.CharField(
        max_length=1,  # since it's a single-digit string
        choices=STATUS_CHOICES,
        default='0',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'partners'

    @property
    def user(self):
        from ..models import Users  # Lazy import inside the method to avoid circular import
        try:
            return Users.objects.get(id=self.user_id)
        except Users.DoesNotExist:
            return None
