from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect
from django.contrib import messages
from django.template import loader
from ..models import Commission,Users
from django.contrib.auth import authenticate, login ,logout
from django.core.files.storage import FileSystemStorage
import re
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
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import connection

from pprint import pprint 

OPENAI_API_KEY = settings.OPENAI_API_KEY

app = FastAPI()


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def commissions(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        query = """
            SELECT c.*, u.first_name, u.last_name 
            FROM commissions c
            INNER JOIN users u ON c.sub_broker_id = u.id
            WHERE c.sub_broker_id = %s
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [user_id])
            commissions_list = dictfetchall(cursor)
        
        # Define insurers and products arrays
        insurers = [
            {'id': 1, 'name': 'ABC'},
            {'id': 2, 'name': 'DEF'},
            {'id': 3, 'name': 'XYZ'},
            {'id': 4, 'name': 'PQY'}
        ]
        products = [
            {'id': 1, 'name': 'Motor'},
            {'id': 2, 'name': 'Health'},
            {'id': 3, 'name': 'Product 3'},
            {'id': 4, 'name': 'Product 4'}
        ]

        # Create dictionaries for fast lookup
        insurer_dict = {insurer['id']: insurer['name'] for insurer in insurers}
        product_dict = {product['id']: product['name'] for product in products}

        # Map the names to the commissions list
        for commission in commissions_list:
            commission['insurer_name'] = insurer_dict.get(commission['insurer_id'], 'Unknown')
            commission['product_name'] = product_dict.get(commission['product_id'], 'Unknown')

        return render(request, 'commissions/commissions.html', {'commissions': commissions_list})
    else:
        return redirect('login')
    
def create(request):
    if request.user.is_authenticated:

        products = [
            {'id': 1, 'name': 'Motor'},
            {'id': 2, 'name': 'Health'},
            {'id': 3, 'name': 'Product 3'},
            {'id': 4, 'name': 'Product 4'}
        ]
        insurers = [
            {'id': 1, 'name': 'ABC'},
            {'id': 2, 'name': 'DEF'},
            {'id': 3, 'name': 'XYZ'},
            {'id': 4, 'name': 'PQY'}
        ]
        return render(request, 'commissions/create.html', {'products': products, 'insurers': insurers})
    else:
        return redirect('login')
   
def store(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST":
        insurer_id = request.POST.get('insurer', '').strip()
        product_id = request.POST.get('product', '').strip()
        tp_percentage = request.POST.get('tp_percentage', '').strip()
        od_percentage = request.POST.get('od_percentage', '').strip()
        net_percentage = request.POST.get('net_percentage', '').strip()

        # Validations
        if not insurer_id:
            messages.error(request, "Insurer is required.")
        if not product_id:
            messages.error(request, "Product is required.")
        if not tp_percentage or not tp_percentage.replace('.', '', 1).isdigit():
            messages.error(request, "Valid TP percentage is required.")
        if not od_percentage or not od_percentage.replace('.', '', 1).isdigit():
            messages.error(request, "Valid OD percentage is required.")
        if not net_percentage or not net_percentage.replace('.', '', 1).isdigit():
            messages.error(request, "Valid Net percentage is required.")

        # Check if this sub-broker already has a commission for the selected insurer
        if Commission.objects.filter(insurer_id=insurer_id, product_id=product_id, sub_broker_id=request.user.id).exists():
            messages.error(request, "You already have a commission for this insurer & product.")

        # If any errors, redirect back to the 'add-commission' page
        if messages.get_messages(request):
            return redirect('add-commission')

        # Save to database
        Commission.objects.create(
            product_id=product_id,
            insurer_id=insurer_id,
            tp_percentage=float(tp_percentage),
            od_percentage=float(od_percentage),
            net_percentage=float(net_percentage),
            sub_broker_id=request.user.id,
            created_by=request.user.id
        )

        messages.success(request, "Commission added successfully.")
        return redirect('commissions')

    else:
        messages.error(request, "Invalid request.")
        return redirect('add-commission')
