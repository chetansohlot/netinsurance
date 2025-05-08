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
import calendar
from django.db.models.functions import ExtractMonth, ExtractYear


OPENAI_API_KEY = settings.OPENAI_API_KEY
logging.getLogger('faker').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI()

from django.db.models import Count, Sum, F
from django.db.models.functions import Cast
from django.db.models import FloatField, Sum

from django.utils.timezone import make_naive
from django.db import connection
def dashboard(request):
    if request.user.is_authenticated:
        user = request.user

        # Base queryset depending on role
        if request.user.role_id != 1 and str(request.user.department_id) not in ["3", "5", "2"]:
            base_qs = PolicyDocument.objects.filter(status=6, rm_id=user.id)
        else:
            base_qs = PolicyDocument.objects.filter(status=6)

        base_qs = base_qs.prefetch_related('policy_info')    

        # Group by insurance_provider
        provider_summary = (
            base_qs.values('insurance_provider')
            .annotate(
                policies_sold=Count('id'),
                policy_income=Sum(
                    # convert policy_premium to float before aggregation
                    Cast('policy_premium', output_field=FloatField())),
                total_net_premium=Sum(
                    # convert policy_net_premium to float before aggregation
                    Cast('policy_info__net_premium', FloatField())),
                total_gross_premium=Sum(
                    # convert policy_gross_premium to float before aggregation
                    Cast('policy_info__gross_premium', FloatField())),
            )
            .order_by('-policy_income','-policies_sold')[:4]
        )

        total_policies = base_qs.count()
        total_revenue = base_qs.aggregate(
            total=Sum(Cast('policy_premium', output_field=FloatField()))
        )['total'] or 0

        total_net_premium = base_qs.aggregate(
            total=Sum(Cast('policy_info__net_premium', FloatField()))
        )['total'] or 0

        total_gross_premium = base_qs.aggregate(
            total=Sum(Cast('policy_info__gross_premium', FloatField()))
        )['total'] or 0
        
        current_year = datetime.now().year

        # Raw SQL query to get document count for the last 6 months
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH RECURSIVE month_series AS (
                    SELECT DATE_FORMAT(CURDATE() - INTERVAL 5 MONTH, '%Y-%m-01') AS month_start
                    UNION ALL
                    SELECT DATE_FORMAT(DATE_ADD(month_start, INTERVAL 1 MONTH), '%Y-%m-01')
                    FROM month_series
                    WHERE month_start < DATE_FORMAT(CURDATE(), '%Y-%m-01')
                )
                SELECT 
                    DATE_FORMAT(ms.month_start, '%b') AS month_name,  -- 3-letter month name
                    COUNT(pd.id) AS document_count
                FROM 
                    month_series ms
                LEFT JOIN 
                    policydocument pd 
                    ON DATE_FORMAT(pd.created_at, '%Y-%m') = DATE_FORMAT(ms.month_start, '%Y-%m')
                    AND pd.created_at >= CURDATE() - INTERVAL 6 MONTH
                GROUP BY 
                    ms.month_start
                ORDER BY 
                    ms.month_start;
            """)
            result = cursor.fetchall()

        print(result)


        # Prepare the results for rendering
        monthly_data = [(row[0], row[1]) for row in result]  # Format as (month_name, document_count)
        
        # The last 6 months' labels
        consolidated_month_labels = [row[0] for row in monthly_data]
        consolidated_month_counts = [row[1] for row in monthly_data]

        # Extracting data for chart
        provider_labels = [entry['insurance_provider'] for entry in provider_summary]
        motor_counts = [entry['policies_sold'] for entry in provider_summary]  
        insurer_motor_counts, insurer_provider_labels = business_summary_insurer_chart(request)
        return render(request, 'dashboard.html', {
            'user': user,
            'provider_summary': provider_summary,
            'consolidated_month_labels': consolidated_month_labels,
            'consolidated_month_counts': consolidated_month_counts,
            'insurer_motor_counts': insurer_motor_counts,
            'insurer_provider_labels': insurer_provider_labels,
            'provider_labels': provider_labels,
            'motor_counts': motor_counts,
            'policy_count': total_policies,
            'total_revenue': total_revenue,
            'total_net_premium': total_net_premium,
            'total_gross_premium': total_gross_premium,
        })
    else:
        return redirect('login')
    print(result)
    

def business_summary_insurer_chart(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT insurance_provider, COUNT(*) AS policies_sold
            FROM policydocument
            WHERE status = 6
            GROUP BY insurance_provider
            ORDER BY policies_sold DESC
            LIMIT 4;
        """)
        result = cursor.fetchall()


    provider_summary = []
    insurer_motor_counts = []
    insurer_provider_labels = []
    for row in result:
        insurance_provider = row[0]
        policies_sold = row[1]
        initials = ''.join(word[0] for word in insurance_provider.split() if word).upper() if insurance_provider else ''

        provider_summary.append({
            'insurance_provider': insurance_provider,
            'policies_sold': policies_sold,
            'initials': initials
        })

        insurer_motor_counts.append(policies_sold)
        insurer_provider_labels.append(insurance_provider)
    return insurer_motor_counts, insurer_provider_labels

def get_chart_data(request):
    # Fetch data
    base_qs = PolicyDocument.objects.filter(status=6).select_related('policy_info')
    
    # Monthly data calculation
    monthly_data = base_qs.annotate(
        month=ExtractMonth('created_at'),
        year=ExtractYear('created_at')
    )

    # Initialize chart data
    labels = [calendar.month_abbr[i] for i in range(1, 13)]
    motor_data = [0] * 12
    health_data = [0] * 12
    term_data = [0] * 12

# Aggregate data by month and category
    for row in monthly_data:
        if row.month:
            idx = row.month - 1
            motor_data[idx] += row.policy_info.motor if row.policy_info.motor is not None else 0
            health_data[idx] += row.policy_info.health if row.policy_info.health is not None else 0
            term_data[idx] += row.policy_info.term if row.policy_info.term is not None else 0

    # Prepare and return chart data in JSON format
    chart_data = {
        'labels': labels,
        'motor_data': motor_data,
        'health_data': health_data,
        'term_data': term_data
    }

    return JsonResponse(chart_data)    
