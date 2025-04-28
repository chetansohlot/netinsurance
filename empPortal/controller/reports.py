from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from ..models import PolicyDocument,Users
from empPortal.export import export_commission_data_v1

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
    
    if role_id != 1:
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
