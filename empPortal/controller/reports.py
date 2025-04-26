from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from ..models import PolicyDocument,Users

def commission_report(request):
    if not request.user.is_authenticated and request.user.is_active != 1:
        messages.error(request, "Please Login First")
        return redirect('login')
    
    # Get filter values from GET parameters
    policy_no = request.GET.get("policy_no", None)
    insurer_name = request.GET.get("insurer_name", None)
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
        policies = policies.filter(insurance_provider__icontains=insurer_name)

    policies = policies.order_by('-id')
    
    paginator = Paginator(policies, per_page)
    page_obj = paginator.get_page(page_number)
    
    policy_data = []
    for policy in page_obj:  # Iterate only over paginated data
        # Convert values safely
        od_premium = float(policy.od_premium.replace(',', '')) if policy.od_premium else 0.0
        tp_premium = float(policy.tp_premium.replace(',', '')) if policy.tp_premium else 0.0
        net_premium = float(policy.policy_premium.replace(',', '')) if policy.policy_premium else 0.0

        commission = policy.commission()
        if commission:
            od_percentage = float(policy.od_percent) if policy.od_percent else 0
            tp_percentage = float(policy.tp_percent	) if policy.tp_percent	 else 0
            net_percentage = float(policy.net_percent) if policy.net_percent else 0
        else:
            od_percentage = 0
            tp_percentage = 0
            net_percentage = 0

        # Calculate commission amounts
        od_commission_amount = (od_premium * od_percentage) / 100
        tp_commission_amount = (tp_premium * tp_percentage) / 100
        net_commission_amount = (net_premium * net_percentage) / 100

        policy_infos = policy.policy_info.first() 
        policy_vehicle_info = policy.policy_vehicle_info.first() 
        policy_agent_info = policy.policy_agent_info.first() 
        policy_franchise_info = policy.policy_franchise_info.first() 
        
        policy_data.append({
            'policy': policy,
            'policy_infos': policy_infos,
            'policy_vehicle_info': policy_vehicle_info,
            'policy_agent_info': policy_agent_info,
            'policy_franchise_info': policy_franchise_info,
            'od_commission_amount': od_commission_amount,
            'tp_commission_amount': tp_commission_amount,
            'net_commission_amount': net_commission_amount
        })

    return render(request, 'reports/commission-report.html', {
        'policy_data': policy_data,
        'page_obj': page_obj  # Pass paginated object to template
    })
