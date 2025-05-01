from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from datetime import datetime
from empPortal.model import Referral

from ..models import PolicyDocument,Users, Branch
from empPortal.export import export_commission_data_v1

import json

def commission_report(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    # Get filter values from GET parameters
    policy_no = request.GET.get("policy_no", None)
    insurer_name = request.GET.get("insurer_name", None)
    service_provider = request.GET.get("service_provider", None)
    insurance_company = request.GET.get("insurance_company", None)
    policy_type = request.GET.get("policy_type", None)
    vehicle_type = request.GET.get("vehicle_type", None)
    referral_name = request.GET.get("referral_name", None)
    vehicle_reg_no = request.GET.get("vehicle_reg_no", None)
    policy_start_date = request.GET.get("policy_start_date", None)
    policy_end_date = request.GET.get("policy_end_date", None)
    per_page = request.GET.get("per_page", 20)  # Default: 20 records per page
    page_number = request.GET.get('page',1)

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    
    user_id  = request.user.id
    role_id = request.user.role_id
    
    if role_id != 1 and str(request.user.department_id) not in ["3", "5"]:
        policies = PolicyDocument.objects.filter(status=6,rm_id=user_id).exclude(rm_id__isnull=True).all()
    else:
        policies = PolicyDocument.objects.filter(status=6).exclude(rm_id__isnull=True).all()

    if policy_no:
        policies = policies.filter(policy_number__icontains=policy_no)
    
    if insurer_name:
        policies = policies.filter(policy_info__insurance_company__icontains=insurer_name)  # <-- yeh policy_info vali table se data check krega
    
    if service_provider:
        policies = policies.filter(policy_info__service_provider__icontains=service_provider)  # <-- yeh policy_info vali table se data check krega
        
    if insurance_company:
        policies = policies.filter(policy_info__insurance_company__icontains=insurance_company)  # <-- yeh policy_info vali table se data check krega
    
    if policy_type:
        policies = policies.filter(policy_info__policy_type__icontains=policy_type)  # <-- yeh policy_info vali table se data check krega
        
    if vehicle_type:
        policies = policies.filter(policy_vehicle_info__vehicle_type__icontains=vehicle_type)  # <-- yeh policy_vehicle_info vali table se data check krega
    
    if referral_name:
        policies = policies.filter(policy_agent_info__referral__name__icontains=referral_name)  # <-- yeh agent_payment_details vali table se data check krega

    if vehicle_reg_no:
        policies = policies.filter(policy_vehicle_info__registration_number__icontains=vehicle_reg_no)  # <-- yeh policy_vehicle_info vali table se data check krega

    if policy_start_date:
        policies = policies.filter(policy_info__policy_start_date__icontains=policy_start_date)  # <-- yeh policy_info vali table se data check krega

    if policy_end_date:
        policies = policies.filter(policy_info__policy_end_date__icontains=policy_end_date)  # <-- yeh policy_info vali table se data check krega


    policies = policies.order_by('-id')
    
    paginator = Paginator(policies, per_page)
    page_obj = paginator.get_page(page_number)
    
    policy_data = []
    for policy in page_obj:  # Iterate only over paginated data
        
        policy_infos = policy.policy_info.first() 
        policy_vehicle_info = policy.policy_vehicle_info.first() 
        policy_agent_info = policy.policy_agent_info.first() 
        policy_franchise_info = policy.policy_franchise_info.first() 
        policy_insurer_info = policy.policy_insurer_info.first() 
        
        policy_data.append({
            'policy': policy,
            'policy_infos': policy_infos,
            'policy_vehicle_info': policy_vehicle_info,
            'policy_agent_info': policy_agent_info,
            'policy_franchise_info': policy_franchise_info,
            'policy_insurer_info': policy_insurer_info
        })

    return render(request, 'reports/commission-report.html', {
        'policy_data': policy_data,
        'page_obj': page_obj  # Pass paginated object to template
    })

def pending_insurer_commission_report(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request,'Please Login')
        return redirect('login')
    
    user_id = request.user.id
    role_id = request.user.role_id
    
    branch_name = request.GET.get('branch_name', '').strip()
    referred_by = request.GET.get('referred_by', '').strip()
    
    # make filters firstly
    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if role_id != 1 and str(request.user.department_id) not in ["3", "5"]:
        filters_q &= Q(rm_id=user_id)

    
    branch = Branch.objects.filter(branch_name__iexact=branch_name).first()
    referral = Referral.objects.filter(name__iexact=referred_by).first()
    
    if branch:
        filters_q &= Q(policy_info__branch_name=str(branch.id))
    if referral:
        filters_q &= Q(policy_agent_info__referral_id=str(referral.id))
        
        
    exclude_q = Q(policy_insurer_info__insurer_od_comm__isnull=False) | \
                Q(policy_insurer_info__insurer_net_comm__isnull=False) | \
                Q(policy_insurer_info__insurer_tp_comm__isnull=False) | \
                Q(policy_insurer_info__insurer_incentive_amount__isnull=False) | \
                Q(policy_insurer_info__insurer_tds__isnull=False) | \
                Q(policy_insurer_info__isnull=False)

    policy_qs = PolicyDocument.objects.filter(filters_q).exclude(exclude_q)

    filters = {
        'policy_number': request.GET.get('policy_number', '').strip().lower(),
        'vehicle_number': request.GET.get('vehicle_number', '').strip().lower(),
        'engine_number': request.GET.get('engine_number', '').strip().lower(),
        'chassis_number': request.GET.get('chassis_number', '').strip().lower(),
        'vehicle_type': request.GET.get('vehicle_type', '').strip().lower(),
        'policy_holder_name': request.GET.get('policy_holder_name', '').strip().lower(),
        'mobile_number': request.GET.get('mobile_number', '').strip().lower(),
        'insurance_provider': request.GET.get('insurance_provider', '').strip().lower(),
        'insurance_company': request.GET.get('insurance_company', '').strip().lower(),
        'start_date': request.GET.get('start_date', '').strip(),
        'end_date': request.GET.get('end_date', '').strip(),
        'manufacturing_year_from': request.GET.get('manufacturing_year_from', '').strip(),
        'manufacturing_year_to': request.GET.get('manufacturing_year_to', '').strip(),
        'fuel_type': request.GET.get('fuel_type', '').strip().lower(),
        'gvw_from': request.GET.get('gvw_from', '').strip(),
    }

    filtered = []
    
    for obj in policy_qs.only('id', 'policy_number', 'vehicle_number', 'holder_name', 'insurance_provider', 'extracted_text', 'vehicle_type').order_by('-id'):
        data = obj.extracted_text or {}
        if not isinstance(data, dict):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                continue

        if not data:
            continue
        
        
        match = True
        for key, val in filters.items():
            if val:
                if key == 'policy_number' and val not in (obj.policy_number or '').lower():
                    match = False
                    break
                elif key == 'vehicle_number' and val not in (obj.vehicle_number or '').lower():
                    match = False
                    break
                elif key == 'vehicle_type' and val != (obj.vehicle_type or '').lower():
                    match = False
                    break
                elif key == 'policy_holder_name' and val not in (obj.holder_name or '').lower():
                    match = False
                    break
                elif key == 'insurance_provider' and val not in (obj.insurance_provider or '').lower():
                    match = False
                    break
                elif key == 'insurance_company' and val not in data.get('insurance_company', '').lower():
                    match = False
                    break
                elif key == 'mobile_number' and val not in data.get('mobile_number', '').lower():
                    match = False
                    break
                elif key == 'engine_number' and val not in data.get('engine_number', '').lower():
                    match = False
                    break
                elif key == 'chassis_number' and val not in data.get('chassis_number', '').lower():
                    match = False
                    break
                elif key == 'fuel_type' and val not in data.get('fuel_type', '').lower():
                    match = False
                    break
                elif key == 'gvw_from':
                    try:
                        if int(data.get('gvw', '0')) < int(val):
                            match = False
                            break
                    except:
                        match = False
                        break
                elif key == 'manufacturing_year_from':
                    try:
                        if int(data.get('manufacturing_year', '0')) < int(val):
                            match = False
                            break
                    except:
                        match = False
                        break
                elif key == 'manufacturing_year_to':
                    try:
                        if int(data.get('manufacturing_year', '0')) > int(val):
                            match = False
                            break
                    except:
                        match = False
                        break
                elif key == 'start_date' and val:
                    try:
                        start_dt = datetime.strptime(val, '%Y-%m-%d')
                        if obj.created_at.date() < start_dt.date():
                            match = False
                            break
                    except ValueError:
                        match = False
                        break
                elif key == 'end_date' and val:
                    try:
                        end_dt = datetime.strptime(val, '%Y-%m-%d')
                        if obj.created_at.date() > end_dt.date():
                            match = False
                            break
                    except ValueError:
                        match = False
                        break

        if match:
            obj.json_data = data
            obj.policy_infos = obj.policy_info.first()
            obj.policy_vehicle_infos = obj.policy_vehicle_info.first()
            obj.policy_agent_infos = obj.policy_agent_info.first()
            obj.policy_franchise_infos = obj.policy_franchise_info.first()
            obj.policy_insurer_infos = obj.policy_insurer_info.first()

            filtered.append(obj)

            
    per_page = request.GET.get('per_page', 20)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 20

    paginator = Paginator(filtered, per_page)
    page_number = request.GET.get('page',20)
    page_obj = paginator.get_page(page_number)


    return render(request,'reports/pending-insurer-commission-reports.html',{
        "page_obj": page_obj,
        "per_page": per_page,
        'filters': {k: request.GET.get(k, '') for k in filters},
        'filtered_policy_ids': [obj.id for obj in filtered],
        'filtered_count': len(filtered),
    })
    
def pending_agent_commission_report(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request,'Please Login')
        return redirect('login')
    
    user_id = request.user.id
    role_id = request.user.role_id
    
    branch_name = request.GET.get('branch_name', '').strip()
    referred_by = request.GET.get('referred_by', '').strip()
    
    # make filters firstly
    filters_q = Q(status=6) & Q(policy_number__isnull=False) & ~Q(policy_number='')

    if role_id != 1 and str(request.user.department_id) not in ["3", "5"]:
        filters_q &= Q(rm_id=user_id)

    
    branch = Branch.objects.filter(branch_name__iexact=branch_name).first()
    referral = Referral.objects.filter(name__iexact=referred_by).first()
    
    if branch:
        filters_q &= Q(policy_info__branch_name=str(branch.id))
    if referral:
        filters_q &= Q(policy_agent_info__referral_id=str(referral.id))
        
        
    exclude_q = Q(policy_agent_info__agent_od_comm__isnull=False) | \
                Q(policy_agent_info__agent_net_comm__isnull=False) | \
                Q(policy_agent_info__agent_tp_comm__isnull=False) | \
                Q(policy_agent_info__agent_incentive_amount__isnull=False) | \
                Q(policy_agent_info__agent_tds__isnull=False) | \
                Q(policy_agent_info__isnull=False)

    policy_qs = PolicyDocument.objects.filter(filters_q).exclude(exclude_q)

    filters = {
        'policy_number': request.GET.get('policy_number', '').strip().lower(),
        'vehicle_number': request.GET.get('vehicle_number', '').strip().lower(),
        'engine_number': request.GET.get('engine_number', '').strip().lower(),
        'chassis_number': request.GET.get('chassis_number', '').strip().lower(),
        'vehicle_type': request.GET.get('vehicle_type', '').strip().lower(),
        'policy_holder_name': request.GET.get('policy_holder_name', '').strip().lower(),
        'mobile_number': request.GET.get('mobile_number', '').strip().lower(),
        'insurance_provider': request.GET.get('insurance_provider', '').strip().lower(),
        'insurance_company': request.GET.get('insurance_company', '').strip().lower(),
        'start_date': request.GET.get('start_date', '').strip(),
        'end_date': request.GET.get('end_date', '').strip(),
        'manufacturing_year_from': request.GET.get('manufacturing_year_from', '').strip(),
        'manufacturing_year_to': request.GET.get('manufacturing_year_to', '').strip(),
        'fuel_type': request.GET.get('fuel_type', '').strip().lower(),
        'gvw_from': request.GET.get('gvw_from', '').strip(),
    }

    filtered = []
    
    for obj in policy_qs.only('id', 'policy_number', 'vehicle_number', 'holder_name', 'insurance_provider', 'extracted_text', 'vehicle_type').order_by('-id'):
        data = obj.extracted_text or {}
        if not isinstance(data, dict):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                continue

        if not data:
            continue
        
        
        match = True
        for key, val in filters.items():
            if val:
                if key == 'policy_number' and val not in (obj.policy_number or '').lower():
                    match = False
                    break
                elif key == 'vehicle_number' and val not in (obj.vehicle_number or '').lower():
                    match = False
                    break
                elif key == 'vehicle_type' and val != (obj.vehicle_type or '').lower():
                    match = False
                    break
                elif key == 'policy_holder_name' and val not in (obj.holder_name or '').lower():
                    match = False
                    break
                elif key == 'insurance_provider' and val not in (obj.insurance_provider or '').lower():
                    match = False
                    break
                elif key == 'insurance_company' and val not in data.get('insurance_company', '').lower():
                    match = False
                    break
                elif key == 'mobile_number' and val not in data.get('mobile_number', '').lower():
                    match = False
                    break
                elif key == 'engine_number' and val not in data.get('engine_number', '').lower():
                    match = False
                    break
                elif key == 'chassis_number' and val not in data.get('chassis_number', '').lower():
                    match = False
                    break
                elif key == 'fuel_type' and val not in data.get('fuel_type', '').lower():
                    match = False
                    break
                elif key == 'gvw_from':
                    try:
                        if int(data.get('gvw', '0')) < int(val):
                            match = False
                            break
                    except:
                        match = False
                        break
                elif key == 'manufacturing_year_from':
                    try:
                        if int(data.get('manufacturing_year', '0')) < int(val):
                            match = False
                            break
                    except:
                        match = False
                        break
                elif key == 'manufacturing_year_to':
                    try:
                        if int(data.get('manufacturing_year', '0')) > int(val):
                            match = False
                            break
                    except:
                        match = False
                        break
                elif key == 'start_date' and val:
                    try:
                        start_dt = datetime.strptime(val, '%Y-%m-%d')
                        if obj.created_at.date() < start_dt.date():
                            match = False
                            break
                    except ValueError:
                        match = False
                        break
                elif key == 'end_date' and val:
                    try:
                        end_dt = datetime.strptime(val, '%Y-%m-%d')
                        if obj.created_at.date() > end_dt.date():
                            match = False
                            break
                    except ValueError:
                        match = False
                        break

        if match:
            obj.json_data = data
            obj.policy_infos = obj.policy_info.first()
            obj.policy_vehicle_infos = obj.policy_vehicle_info.first()
            obj.policy_agent_infos = obj.policy_agent_info.first()
            obj.policy_franchise_infos = obj.policy_franchise_info.first()
            obj.policy_insurer_infos = obj.policy_insurer_info.first()

            filtered.append(obj)

            
    per_page = request.GET.get('per_page', 20)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 20

    paginator = Paginator(filtered, per_page)
    page_number = request.GET.get('page',20)
    page_obj = paginator.get_page(page_number)


    return render(request,'reports/pending-agent-commission-reports.html',{
        "page_obj": page_obj,
        "per_page": per_page,
        'filters': {k: request.GET.get(k, '') for k in filters},
        'filtered_policy_ids': [obj.id for obj in filtered],
        'filtered_count': len(filtered),
    })
    