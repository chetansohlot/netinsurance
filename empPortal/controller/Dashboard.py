from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect
from django.contrib import messages
from django.template import loader
from ..models import Roles,Users, Department,PolicyDocument,BulkPolicyLog, PolicyInfo, Branch, UserFiles,UnprocessedPolicyFiles, Commission, Branch, FileAnalysis, ExtractedFile, ChatGPTLog
from django.contrib.auth import authenticate, login ,logout
from django.core.files.storage import FileSystemStorage
import re, logging
import requests
from fastapi import FastAPI, File, UploadFile
import fitz
import openai
import time
import json
from django.http import JsonResponse
import os
import zipfile
from django.conf import settings
from datetime import datetime
from io import BytesIO
from django.db.models import Q
from ..models import UploadedZip
from django.core.files.base import ContentFile
from ..tasks import process_zip_file
from django_q.tasks import async_task
from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import now
from empPortal.model import Referral
from urllib.parse import urljoin
from collections import Counter
from django.core.paginator import Paginator


OPENAI_API_KEY = settings.OPENAI_API_KEY
logging.getLogger('faker').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI()

from django.db.models import Count, Sum, F
from django.db.models.functions import Cast
from django.db.models import FloatField, Sum

def dashboard(request):
    if request.user.is_authenticated:
        user = request.user

        # Base queryset depending on role
        if request.user.role_id != 1 and str(request.user.department_id) not in ["3", "5", "2"]:
            base_qs = PolicyDocument.objects.filter(status=6, rm_id=user.id)
        else:
            base_qs = PolicyDocument.objects.filter(status=6)

        # Group by insurance_provider
        provider_summary = (
            base_qs.values('insurance_provider')
            .annotate(
                policies_sold=Count('id'),
                policy_income=Sum(
                    # convert policy_premium to float before aggregation
                    Cast('policy_premium', output_field=FloatField())
                )
            )
            .order_by('-policy_income')
        )

        total_policies = base_qs.count()
        total_revenue = base_qs.aggregate(
            total=Sum(Cast('policy_premium', output_field=FloatField()))
        )['total'] or 0

        return render(request, 'dashboard.html', {
            'user': user,
            'provider_summary': provider_summary,
            'policy_count': total_policies,
            'total_revenue': total_revenue,
        })
    else:
        return redirect('login')
