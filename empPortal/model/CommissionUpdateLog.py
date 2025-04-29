from django.db import models

class CommissionUpdateLog(models.Model):
    COMMISSION_TYPE_CHOICES = [
        ('agent', 'Agent'),
        ('franchise', 'Franchise'),
        ('insurer', 'Insurer'),
    ]

    commission_type = models.CharField(max_length=20, choices=COMMISSION_TYPE_CHOICES)
    policy_id = models.IntegerField()
    policy_number = models.CharField(max_length=100)
    updated_by_id = models.IntegerField(null=True, blank=True)  # No FK
    updated_from = models.CharField(max_length=100)  # e.g. 'agent-commission'
    updated_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.commission_type} - {self.policy_number} - {self.updated_by_id}"

    class Meta:
        db_table = 'commission_update_log'