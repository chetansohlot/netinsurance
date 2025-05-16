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
