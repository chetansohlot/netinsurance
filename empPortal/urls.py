from django.urls import path, include
from . import views,export
from . import views
from . import authenticationView
from .controller import commissions, profile, Franchises, Branches, members, customers, quoteManagement, healthQuoteManagement, homeManagement
from django.conf import settings
from django.conf.urls.static import static

motor_patterns = [
    path('quote-management/', quoteManagement.index, name='quote-management'),
    path('fetch-customer/', quoteManagement.fetch_customer, name='fetch-customer'),
    path('fetch-vehicle-info/', quoteManagement.fetch_vehicle_info, name='fetch-vehicle-info'),
    path('download-quotation-pdf/<str:cus_id>/', quoteManagement.downloadQuotationPdf, name='download-quotation-pdf'),
    path('quote-management/create-quote', quoteManagement.create_or_edit, name='quote-management-create'),
    path('quote-management/<str:customer_id>/', quoteManagement.create_or_edit, name='quote-management-edit'),
    path('quote-management/create-quote-vehicle-info/<str:cus_id>/', quoteManagement.createVehicleInfo, name='create-vehicle-info'),
    path('quote-management/show-quotation-info/<str:cus_id>/', quoteManagement.showQuotation, name='show-quotation-info'),
]

health_patterns = [
    path('quote-management/', healthQuoteManagement.index, name='health-quote-management'),
    path('fetch-customer/', healthQuoteManagement.fetch_customer, name='health-fetch-customer'),
    path('fetch-vehicle-info/', healthQuoteManagement.fetch_vehicle_info, name='health-fetch-vehicle-info'),
    path('download-quotation-pdf/<str:cus_id>/', healthQuoteManagement.downloadQuotationPdf, name='health-download-quotation-pdf'),
    path('quote-management/create-quote', healthQuoteManagement.create_or_edit, name='health-quote-management-create'),
    path('quote-management/<str:customer_id>/', healthQuoteManagement.create_or_edit, name='health-quote-management-edit'),
    path('quote-management/create-quote-vehicle-info/<str:cus_id>/', healthQuoteManagement.createVehicleInfo, name='health-create-vehicle-info'),
    path('quote-management/show-quotation-info/<str:cus_id>/', healthQuoteManagement.showQuotation, name='health-show-quotation-info'),
]

urlpatterns = [
    path("login", authenticationView.login_view, name="login"),
    path("login-mobile", authenticationView.login_mobile_view, name="login-mobile"),
    path("check-email/", authenticationView.check_email, name="check-email"),
    path("check-mobile/", authenticationView.check_mobile, name="check-mobile"),
    path("register", authenticationView.register_view, name="register"),
    path("verify-otp", authenticationView.verify_otp_view, name="verify-otp"),
    path("re-send-otp-mobile-login", authenticationView.reSendOtp_View, name="re-send-otp-mobile-login"),
    path("mobile-verify-otp", authenticationView.mobile_verify_otp_view, name="mobile-verify-otp"),
    path("forget-password", authenticationView.forget_pass_view, name="forget-password"),
    path("reset-password", authenticationView.reset_pass_view, name="reset-password"),
    path("email-verify-otp", authenticationView.email_verify_otp, name="email-verify-otp"),
    path("resend-otp", authenticationView.verify_otp_view, name="resend-otp"),
    
    path('user-and-roles/', views.userAndRoles, name='user-and-roles'),
    path('', homeManagement.index, name='home-index'),
    path('dashboard/', views.dashboard, name='dashboard'),


    path('franchise-management/', Franchises.index, name='franchise-management'),
    path('franchise-management/create-franchise', Franchises.create_or_edit, name='franchise-management-create'),
    path('franchise-management/<str:franchise_id>/', Franchises.create_or_edit, name='franchise-management-edit'),

    path('branch-management/', Branches.index, name='branch-management'),
    path('branch-management/create-branch', Branches.create_or_edit, name='branch-management-create'),
    path('branch-management/<str:branch_id>/', Branches.create_or_edit, name='branch-management-edit'),

    path('my-account/', profile.myAccount, name='my-account'),
    path('upload-documents/', profile.upload_documents, name='upload_documents'),
    path("update-document/", profile.update_document, name="update_document"),
    path("update-document-id/", profile.update_document_id, name="update_document_id"),
    path('store-bank-data/', profile.storeOrUpdateBankDetails, name='store-bank-data'),
    path("check-account-number/", profile.check_account_number, name="check-account-number"),

    path('update-user-details/', profile.update_user_details, name='update-user-details'),

    path("update-doc-status/", members.update_doc_status, name="update-doc-status"),  
    path('members/', members.members, name='members'),
    path('/member/member-view/<str:user_id>',members.memberView, name='member-view'),
    path('/member/activate-user/<str:user_id>',members.activateUser, name='activate-user'),
    path('update-commission/', commissions.update_commission, name='update-commission'),

    path('customers/', customers.customers, name='customers'),
    path('add-customer/', customers.create, name='add-customer'),
    path('store-customer/', customers.store, name='store-customer'),

    path('motor/', include(motor_patterns)),
    path('health/', include(health_patterns)),
    
    path('commissions/', commissions.commissions, name='commissions'),
    path('add-commission/', commissions.create, name='add-commission'),
    path('store-commission/', commissions.store, name='store-commission'),

    path('billings/', views.billings, name='billings'),
    path('claim-tracker/', views.claimTracker, name='claim-tracker'),
    path('checkout/', views.checkout, name='checkout'),
    path('add-members/', views.addMember, name='add-members'),
    path('new-role/', views.newRole, name='new-role'),
    path('insert-role/', views.insertRole, name='insert-role'),
    path('create-user/', views.createUser, name='create-user'),
    path('insert-user/', views.insertUser, name='insert-user'),
    path('role/edit/<str:id>',views.editRole, name='edit-role'),
    path('users/edit-user/<str:id>',views.editUser, name='edit-user'),
    path('users/edit-user-status',views.updateUserStatus, name='edit-user-status'),
    path('update-role/', views.updateRole, name='update-role'),
    path('update-user/', views.updateUser, name='update-user'),
    
    path('policy-mgt/', views.policyMgt, name='policy-mgt'),
    path('bulk-policy-mgt/', views.bulkPolicyMgt, name='bulk-policy-mgt'),
    path('browser-policy/', views.browsePolicy, name='browser-policy'),
    path('policy-upload-view/<str:id>', views.policyUploadView, name='policy-upload-view'),
    path('bulk-browser-policy/', views.bulkBrowsePolicy, name='bulk-browser-policy'),
    path('policy-data/', views.policyData, name='policy-data'),
    path('edit-policy-data/<str:id>', views.editPolicy, name='edit-policy'),
    path('update-policy/', views.updatePolicy, name='update-policy'),
    path('reprocess-bulk-policies',views.reprocessBulkPolicies,name="reprocess-bulk-policies"),
    path('bulk-upload-logs/',views.bulkUploadLogs,name='bulk-upload-logs'),
    
    path('change-password/',views.changePassword,name='change-password'),
    path('update-password',views.updatePassword,name='update-password'),
    path("logout/", views.userLogout, name="logout"),
    #  for creating of the export functionality 
    #  path('export-policy/', views.exportPolicies, name='update-policy'),
      path('export-policy/', export.exportPolicies, name='export-policy'),   
    #   path('check-relations/', export.check_related_policies, name='check-relation'),   

    
    #  for creating of the export functionality 
    #  path('export-policy/', views.exportPolicies, name='update-policy'),
    path('export-policy/', export.exportPolicies, name='export-policy'),   
    path('save-policy-data/', export.download_policy_data, name='save-policy-data'),
    path('commission-report/', export.commission_report, name='commission-report'),

] 


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)