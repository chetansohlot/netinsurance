from django.http import JsonResponse
from empPortal.model import Referral
from empPortal.model import Partner
from django.conf import settings
from ..models import Users  


def get_referrals(request):
    referrals = Referral.objects.filter(active=True).values('id', 'name')
    return JsonResponse(list(referrals), safe=False)

def get_posp(request):
    valid_user_ids = Users.objects.values_list('id', flat=True)
    partners = Partner.objects.filter(
        partner_status='4',  # 'Activated'
        user_id__in=valid_user_ids
    ).values('user_id', 'name')
    return JsonResponse(list(partners), safe=False)

def get_branch_sales_manager(request):
    branch_id = request.POST.get('branch_id')
    managers = Users.objects.filter(
        role_id='5',
        branch_id = branch_id,
        department_id = 1,
        is_active = True
    ).values('id', 'first_name','last_name')
    return JsonResponse(list(managers), safe=False)

def get_sales_team_leader(request):
    assigned_manager = request.POST.get('assigned_manager')
    branch_id = request.POST.get('branch_id')
    
    team_leaders = Users.objects.filter(
        branch_id = branch_id,
        senior_id = assigned_manager,
        department_id = 1,
        is_active = True
    ).values('id', 'first_name','last_name')
    return JsonResponse(list(team_leaders), safe=False)

def get_sales_relation_manager(request):
    assigned_teamleader = request.POST.get('assigned_teamleader')
    branch_id = request.POST.get('branch_id')
    
    relation_managers = Users.objects.filter(
        branch_id = branch_id,
        senior_id = assigned_teamleader,
        department_id = 1,
        is_active = True
    ).values('id', 'first_name','last_name')
    return JsonResponse(list(relation_managers), safe=False)
