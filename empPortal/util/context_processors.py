from django.conf import settings


def company_constants(request):
    return {
        'GLOBAL_BIG_LOGO': settings.GLOBAL_BIG_LOGO,
        'SIDEBAR_LOGO': settings.SIDEBAR_LOGO,
        'SIDEBAR_MINI_LOGO': settings.SIDEBAR_MINI_LOGO,
        'FAVICON_LOGO': settings.FAVICON_LOGO,
        
        'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
        'COMPANY_EMAIL': settings.COMPANY_EMAIL,
        'COMPANY_TEL': settings.COMPANY_TEL,
        'SUPPORT_PARTNER_PHONE': settings.SUPPORT_PARTNER_PHONE,
        'SUPPORT_PHONE': settings.SUPPORT_PHONE,
        
        'HEAD_SIGNATURE': settings.HEAD_SIGNATURE,
        'DEFAULT_IMAGE_POS': settings.DEFAULT_IMAGE_POS,
        'SIGNATURE_POS': settings.SIGNATURE_POS,

        'EMP_PORTAL_PATH': settings.EMP_PORTAL_PATH,
        
        'COMPANY_ADDRESS': settings.COMPANY_ADDRESS,
        'COMPANY_NAME': settings.COMPANY_NAME,
        'COMPANY_SHORT_NAME': settings.COMPANY_SHORT_NAME,
        'COMPANY_FIRST_NAME': settings.COMPANY_FIRST_NAME,
        'CIN_NO': settings.CIN_NO,
        'IRDAI_LICENSE_NO': settings.IRDAI_LICENSE_NO,
        'VALID_TILL': settings.VALID_TILL,
        'COMPANY_REGISTRATION_NO': settings.COMPANY_REGISTRATION_NO,
        'COMPANY_REGISTRATION_CODE_NO': settings.COMPANY_REGISTRATION_CODE_NO,
        'PRINCIPAL_OFFICER': settings.PRINCIPAL_OFFICER,
        'LICENSE_CATEGORY': settings.LICENSE_CATEGORY,
    }
