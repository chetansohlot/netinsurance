import sys
from django.apps import AppConfig
import empPortal.helpers

class EmpportalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empPortal'

    def ready(self):
        sys.modules['helpers'] = empPortal.helpers  # Global alias
