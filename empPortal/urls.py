from django.urls import path, include
from . import views,export
from . import views
from . import authenticationView
from .controller import commissions, profile,policy,Dashboard, Referral, globalController, helpAndSupport, Employee, leads, sellMotor, sellHealth, sellTerm, Franchises, Department, Branches, members, customers, quoteManagement, healthQuoteManagement, homeManagement, exams,SourceMaster,BQP
from .controller import reports, PolicyCommission, PolicyPayment, insurance
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path



motor_patterns = [
    path('quote-management/', quoteManagement.index, name='quote-management'),
    path('fetch-customer/', quoteManagement.fetch_customer, name='fetch-customer'),
    path('fetch-vehicle-info/', quoteManagement.fetch_vehicle_info, name='fetch-vehicle-info'),
    path('download-quotation-pdf/<str:cus_id>/', quoteManagement.downloadQuotationPdf, name='download-quotation-pdf'),
    path('quote-management/create-quote', quoteManagement.create_or_edit, name='quote-management-create'),
    path('quote-management/<str:customer_id>/', quoteManagement.create_or_edit, name='quote-management-edit'),
    path('quote-management/create-quote-vehicle-info/<str:cus_id>/', quoteManagement.createVehicleInfo, name='create-vehicle-info'),
    path('quote-management/show-quotation-info/<str:cus_id>/', quoteManagement.showQuotation, name='show-quotation-info'),
    path('send-quotation-email/<str:cus_id>/', quoteManagement.sendQuotationPdfEmail, name='send-quotation-email'),
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
    # GLOBAL - SEARCH 
    path('global-search/', globalController.global_search, name='global_search'),
    # GLOBAL - SEARCH 


    path("login", authenticationView.login_view, name="login"),
    path("login-mobile", authenticationView.login_mobile_view, name="login-mobile"),
    path("check-email/", authenticationView.check_email, name="check-email"),
    path("check-mobile/", authenticationView.check_mobile, name="check-mobile"),
    path("register", authenticationView.register_view, name="register"),
    path("verify-otp", authenticationView.verify_otp_view, name="verify-otp"),
    path("register-verify-otp", authenticationView.register_verify_otp_view, name="register-verify-otp"),
    path("check-agent-existance/<str:uid>/", authenticationView.check_agent_existance, name="check-agent-existance"),
    path("verify-agent-existance", authenticationView.verify_agent_existance, name="verify-agent-existance"),
    path("re-send-otp-mobile-login", authenticationView.reSendOtp_View, name="re-send-otp-mobile-login"),
    path("mobile-verify-otp", authenticationView.mobile_verify_otp_view, name="mobile-verify-otp"),
    path("forget-password", authenticationView.forget_pass_view, name="forget-password"),
    path("reset-password", authenticationView.reset_pass_view, name="reset-password"),
    path("email-verify-otp", authenticationView.email_verify_otp, name="email-verify-otp"),
    path("resend-otp", authenticationView.verify_otp_view, name="resend-otp"),
    path("forget-resend-otp", authenticationView.forgetReSendOtp_View, name="forget-resend-otp"),
    path("register-resend-otp", authenticationView.registerReSendOtp_View, name="register-resend-otp"),
    
    path('user-and-roles/', views.userAndRoles, name='user-and-roles'),
    path('', homeManagement.index, name='home-index'),
    path('dashboard/', Dashboard.dashboard, name='dashboard'),


    path('franchise-management/', Franchises.index, name='franchise-management'),
    path('franchise-management/create-franchise', Franchises.create_or_edit, name='franchise-management-create'),
    path('franchise-management/<str:franchise_id>/', Franchises.create_or_edit, name='franchise-management-edit'),
    path("toggle-franchise-status/<int:franchise_id>/", Franchises.franchise_toggle_status, name="franchise-toggle-status"), #Anjali


    path('branch-management/', Branches.index, name='branch-management'),
    path("check-branch-email/", Branches.check_branch_email, name="check-branch-email"),
    path('branch-management/create-branch', Branches.create_or_edit, name='branch-management-create'),
    path('branch-management/<str:branch_id>/', Branches.create_or_edit, name='branch-management-edit'),
    path('branch/toggle-status/<int:branch_id>/', Branches.toggle_branch_status, name='branch-toggle-status'),  #Anjali


    path('department-management/', Department.index, name='department-management'),
    path('department-management/create-department', Department.create_or_edit, name='department-management-create'),
    path('department-management/<str:department_id>/', Department.create_or_edit, name='department-management-edit'),
    path('department/toggle-status/<int:department_id>/', Department.toggle_department_status, name='department-toggle-status'),  #Anjali


    path('employee-management/', Employee.index, name='employee-management'),
    path('employee-management/create-employee', Employee.create_or_edit, name='employee-management-create'),
    path('employee-management/<str:employee_id>/', Employee.create_or_edit, name='employee-management-edit'),
    path('employee-management/employee-allocation-employee/<str:employee_id>', Employee.create_or_edit_allocation, name='employee-allocation-update'),
     

    path('my-account/', profile.myAccount, name='my-account'),
    path('download-certificate-pdf/<str:cus_id>/', profile.downloadCertificatePdf, name='download-certificate'),

    path('upload-documents/', profile.upload_documents, name='upload_documents'),
    path("update-document/", profile.update_document, name="update_document"),
    path("update-document-id/", profile.update_document_id, name="update_document_id"),
    path('store-bank-data/', profile.storeOrUpdateBankDetails, name='store-bank-data'),
    path('store-allocation/', profile.storeAllocation, name='store-allocation'),
    
    path('get-branch-managers/', members.get_branch_managers, name='get_branch_managers'),
    path('get-sales-managers/', members.get_sales_managers, name='get_sales_managers'),
    path('get-rm-list/', members.get_rm_list, name='get_rm_list'),

    path("check-account-number/", profile.check_account_number, name="check-account-number"),

    path('update-user-details/', profile.update_user_details, name='update-user-details'),

    path("update-doc-status/", members.update_doc_status, name="update-doc-status"),  

    path('members/all-partner', members.members, name='members'),
    path('members/in-process', members.members_inprocess, name='members_inprocess'),
    path('members/member-requested', members.members_requested, name='members_requested'),
    path('members/in-training', members.members_intraining, name='members_intraining'),
    path('members/in-exam', members.members_inexam, name='members_inexam'),
    path('exam', exams.members_exam, name='members_exam'),
    path('start-exam', exams.start_exam, name='start_exam'),
    path('exam/MCQs', exams.members_exam_mcq, name='members_exam_mcq'),
    path('exam/submit', exams.submit_exam, name='submit-exam'),
    path('members/activated', members.members_activated, name='members_activated'),
    path('members/rejected', members.members_rejected, name='members_rejected'),
    path('members/inactive', members.members_inactive, name='members_inactive'), ## members_inactive ##

    path('member/member-view/<str:user_id>',members.memberView, name='member-view'),
    path('member/download-training-certificate/<str:user_id>',members.posTrainingCertificate, name='download-training-certificate'),
    path('member/download-certificate/<str:user_id>',members.posCertificate, name='download-certificate'),
    path('member/activate-user/<str:user_id>',members.activateUser, name='activate-user'),
    path('member/update-partner-status/<str:user_id>',members.updatePartnerStatus, name='update-partner-status'),
    path('member/login-activate-user/<str:user_id>',members.loginActivateUser, name='login-activate-user'),
    path('member/deactivate-user/<str:user_id>',members.deactivateUser, name='deactivate-user'),
    path('update-commission/', commissions.update_commission, name='update-commission'),
    path('add-partner/', members.add_partner, name='add-partner'),
    path('upload-partners/', members.upload_excel_users, name='upload-partners-excel'),

    
    # LEADS 
    path('lead-mgt/', leads.index, name='leads-mgt'),
    path('lead-mgt/create', leads.create_or_edit_lead, name='leads-mgt-create'),
    path('lead-mgt/<str:lead_id>/', leads.create_or_edit_lead, name='leads-mgt-edit'),
    path('lead-mgt/health-lead', leads.healthLead, name='health-lead'),
    path('lead-mgt/term-lead', leads.termlead, name='term-lead'),
    path('lead-mgt/lead-view/<int:lead_id>/', leads.viewlead, name='lead-view'),
    path('bulk-upload/', leads.bulk_upload_leads, name='bulk-upload-leads'),
    path('fetch-policy-details/', leads.fetch_policy_details, name='fetch-policy-details'),
    path('lead-mgt/export/', leads.export_leads_to_excel, name='lead_mgt_export'),
    path('get-cities/', leads.get_cities, name='get_cities'),


    #Insurance
    path('insurance/', insurance.insurance_list, name='insurance_index'),
    path('create-insurance/', insurance.insurance_create, name='create_insurance'),
    path('insurance/edit/<int:insurance_id>/', insurance.insurance_edit, name='insurance_edit'),
    path('toggle-insurance-status/<int:insurance_id>/', insurance.toggle_insurance_status, name='insurance-toggle-status'),  #Anjali

    # REFERRAL 
    path('referral-management/bulk-upload/', Referral.refBulkUpload, name='referral-bulk-upload'),
    path('referral-management/', Referral.index, name='referral-management'),
    path('referral-management/create-referral', Referral.create_or_edit, name='referral-management-create'),
    path('referral-management/<str:referral_id>/', Referral.create_or_edit, name='referral-management-edit'),
    path('referral/toggle-status/<int:referral_id>/', Referral.toggle_referral_status, name='referral-toggle-status'),
    
    # path('referral-management/bulk-upload/', Referral.ref_bulk_upload, name='referral-bulk-upload'),

    # SELL-ONLINE 
        # MOTOR
        path('sell/motor', sellMotor.index, name='sell-motor'),
        path('sell/motor/motor-insurance', sellMotor.createMotorInsurance, name='create-motor-insurance'),
        path('sell/motor/motor-details', sellMotor.createMotorDetails, name='create-motor'),
        path('sell/motor/motor-proposal-basic-details', sellMotor.createMotorProposalBasicDetails, name='create-motor-proposal-basic'),
        path('sell/motor/motor-quote', sellMotor.createMotorQuote, name='create-motor-quote'),
        path('sell/motor/motor-proposal-nominee-details', sellMotor.createMotorProposalNomineeDetails, name='create-motor-proposal-nominee'),
        path('sell/motor/motor-proposal-address-details', sellMotor.createMotorProposalAddressDetails, name='create-motor-proposal-address'),
        path('sell/motor/motor-proposal-vehicle-details', sellMotor.createMotorProposalVehicleDetails, name='create-motor-proposal-vehicle'),
        path('sell/motor/motor-proposal-summary', sellMotor.createMotorProposalSummary, name='create-motor-proposal-summary'),
        # MOTOR


        # MOTOR 4W
        path('motor/4w/motor-insurance', sellMotor.create4wMotorInsurance, name='create-4w-motor-insurance'),
        path('motor/4w/motor-details', sellMotor.create4wMotorDetails, name='create-4w-motor'),
        path('motor/4w/motor-proposal-basic-details', sellMotor.create4wMotorProposalBasicDetails, name='create-4w-motor-proposal-basic'),
        path('motor/4w/motor-quote', sellMotor.create4wMotorQuote, name='create-4w-motor-quote'),
        path('motor/4w/motor-proposal-nominee-details', sellMotor.create4wMotorProposalNomineeDetails, name='create-4w-motor-proposal-nominee'),
        path('motor/4w/motor-proposal-address-details', sellMotor.create4wMotorProposalAddressDetails, name='create-4w-motor-proposal-address'),
        path('motor/4w/motor-proposal-vehicle-details', sellMotor.create4wMotorProposalVehicleDetails, name='create-4w-motor-proposal-vehicle'),
        path('motor/4w/motor-proposal-summary', sellMotor.create4wMotorProposalSummary, name='create-4w-motor-proposal-summary'),
        # MOTOR 4W

    path('sell/health', sellHealth.index, name='sell-health'),
    # HEALTH JOURNEY 
        path('health/health-insurance', sellHealth.createHealthInsurance, name='create-health-insurance'),
        path('health/health-quotes', sellHealth.createHealthQuotes, name='create-health-quotes'),
        path('health/health-proposer', sellHealth.createHealthProposer, name='create-health-proposer'),
        path('health/health-insured', sellHealth.createHealthInsured, name='create-health-insured'),
        path('health/health-history', sellHealth.createHealthHistory, name='create-health-history'),
        path('health/health-summary', sellHealth.createHealthSummary, name='create-health-summary'),
    # HEALTH JOURNEY 

    path('sell/term', sellTerm.index, name='sell-term'),
    # SELL-ONLINE 

    # REPORTS 
    path('report/commission-report/', export.commission_report, name='commission-report-v0'),
    path('report/sm-business-report/', export.sales_manager_business_report, name='sales-manager-business-report'),
    path('report/a-business-report/', export.agent_business_report, name='agent-business-report'),
    path('report/f-business-report/', export.franchisees_business_report, name='franchisees-business-report'),
    path('report/i-business-report/', export.insurer_business_report, name='insurer-business-report'),
    
    path('report/v1/commission-report/', reports.commission_report, name='commission-report'),  
    path('report/pending-insurer-commission-report/', reports.pending_insurer_commission_report, name='pending-insurer-commission-report'),
    path('report/pending-agent-commission-report/', reports.pending_agent_commission_report, name='pending-agent-commission-report'),
    
    # REPORTS 
    
    # EXPORT
    path('export-commission-report/', export.export_commission_data, name='export-commission-report-v0'),
    path('v1/export-commission-report/', export.export_commission_data_v1, name='export-commission-report'),


    # POLICY-COMMISION 
    path('policy-commission/agent-commission/', PolicyCommission.agent_commission, name='agent-commission'),
    path('policy-commission/update-agent-commission/', PolicyCommission.update_agent_commission, name='update-agent-commission'),
    path('policy-commission/update-franchise-commission/', PolicyCommission.update_franchise_commission, name='update-franchise-commission'),
    path('policy-commission/franchisees-commission/', PolicyCommission.franchisees_commission, name='franchisees-commission'),
    path('policy-commission/insurer-commission/', PolicyCommission.insurer_commission, name='insurer-commission'),
    path('policy-commission/update-insurer-commission/', PolicyCommission.update_insurer_commission, name='update-insurer-commission'),
    # POLICY-COMMISION 

    # POLICY-PAYMENT 
    path('policy-payment/insurer-payment/', PolicyPayment.insurer_payment, name='insurer-payment'),
    path('policy-payment/get-campaign-log/', PolicyPayment.get_campaign_log, name='get-campaign-log'),
    path('policy-payment/view-payment-update-log/', PolicyPayment.view_payment_update_log, name='view-payment-update-log'),
    path("ajax/get-campaigns/", PolicyPayment.ajax_get_campaigns, name="ajax-get-campaigns"),
    # POLICY-PAYMENT 
    

    # HELP-SUPPORT 
    path('help-and-support', helpAndSupport.index, name='help'),
    # HELP-SUPPORT 

    # MY-ACCOUNT 
    # MY-ACCOUNT 

    path('customers/', customers.customers, name='customers'),
    path('store-customer/', customers.store, name='store-customer'),
    path('customers/create', customers.create_or_edit, name='quotation-customer-create'),
    path('customers/<str:customer_id>/', customers.create_or_edit, name='quotation-customer-edit'),
    path('toggle-customer-status/<int:customer_id>/', customers.toggle_customer_status, name='customer-toggle-status'),  #Anjali

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
    path('get-users-by-role/', views.get_users_by_role, name='get_users_by_role'),
    path('insert-user/', views.insertUser, name='insert-user'),
    path('role/edit/<str:id>',views.editRole, name='edit-role'),
    path('users/edit-user/<str:id>',views.editUser, name='edit-user'),
    path('users/edit-user-status',views.updateUserStatus, name='edit-user-status'),
    path('update-role/', views.updateRole, name='update-role'),
    path('update-user/', views.updateUser, name='update-user'),
    
    path('browser-policy/', policy.browsePolicy, name='browser-policy'),
    path('failed-policy-upload-view/<str:id>', views.failedPolicyUploadView, name='failed-policy-upload-view'),
    path('bulk-policies/<str:id>', policy.bulkPolicyView, name='bulk-policies'),
    # path('bulk-browser-policy/', views.bulkBrowsePolicy, name='bulk-browser-policy'),
    path('bulk-browser-policy/', policy.bulkBrowsePolicy, name='bulk-browser-policy'),
    path('policy-data/', policy.policyData, name='policy-data'),
    path('edit-policy-data/<str:id>', views.editPolicy, name='edit-policy'),
    path('delete-policy-data/<str:id>', policy.deletePolicy, name='delete-policy'),
    path('edit-policy/<str:policy_id>/', policy.edit_policy, name='edit-policy-data'),
    re_path(r'^edit-policy-vehicle-details/(?P<policy_id>.+)/$', policy.edit_vehicle_details, name='edit-policy-vehicle-details'),
    re_path(r'^edit-policy-docs/(?P<policy_id>.+)/$', policy.edit_policy_docs, name='edit-policy-docs'),
    re_path(r'^edit-agent-payment-info/(?P<policy_id>.+)/$', policy.edit_agent_payment_info, name='edit-agent-payment-info'),
    re_path(r'^edit-insurer-payment-info/(?P<policy_id>.+)/$', policy.edit_insurer_payment_info, name='edit-insurer-payment-info'),
    re_path(r'^edit-franchise-payment-info/(?P<policy_id>.+)/$', policy.edit_franchise_payment_info, name='edit-franchise-payment-info'),

    path('update-policy/', views.updatePolicy, name='update-policy'),
    path('edit-bulk-policy/', policy.editBulkPolicy, name='edit-bulk-policy'),
    path('update-bulk-policies/', policy.updateBulkPolicy, name='update-bulk-policies'),
    path('bulk-update-logs/', policy.viewBulkUpdates, name='bulk-update-logs'),
    path('single-policy-log/', policy.viewSinglePolicyLog, name='single-policy-log'),
    path('bulk-policy-mgt/', policy.bulkPolicyMgt, name='bulk-policy-mgt'),
    path('policy-mgt/', policy.policyMgt, name='policy-mgt'),
    
    
    path('reprocess-bulk-policies',views.reprocessBulkPolicies,name="reprocess-bulk-policies"),
    path('continue-bulk-policies',views.continueBulkPolicies,name="continue-bulk-policies"),
    path('bulk-upload-logs/',policy.bulkUploadLogs,name='bulk-upload-logs'),
    
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


    ####  source master ---- parth url  ####
    path('source/',SourceMaster.source_list, name='source_list'),
    path('source/create/', SourceMaster.source_create, name='source_create'),
    path('source/edit/<int:source_id>/', SourceMaster.source_edit, name='source_edit'),
    path('source/delete/<int:source_id>/', SourceMaster.source_delete, name='source_delete'),
    
    ## BQP Url ##
    path('bqp/', BQP.bqp_list, name='bqp_list'),
    path('bqp/create/', BQP.bqp_create, name='bqp_create'),
    path('bqp/edit/<int:bqp_id>/', BQP.bqp_edit, name='bqp_edit'),
    path('bqp/delete/<int:bqp_id>/', BQP.bqp_delete, name='bqp_delete'),
    
    path('get-pos-partners-by-bqp/', views.get_pos_partners_by_bqp,name="get-pos-partners-by-bqp")
] 


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)