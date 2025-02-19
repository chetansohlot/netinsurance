from django.urls import path
from . import views,export
from . import views
from . import authenticationView
from .controller import commissions, profile, members

urlpatterns = [
    path("login", authenticationView.login_view, name="login"),
    path("register", authenticationView.register_view, name="register"),
    path("verify-otp", authenticationView.verify_otp_view, name="verify-otp"),
    path("resend-otp", authenticationView.verify_otp_view, name="resend-otp"),
    
    path('user-and-roles/', views.userAndRoles, name='user-and-roles'),
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('my-account/', profile.myAccount, name='my-account'),
    path('store-bank-data/', profile.storeOrUpdateBankDetails, name='store-bank-data'),
    path('update-user-details/', profile.update_user_details, name='update-user-details'),

    path('members/', members.members, name='members'),
    path('/member/member-view/<str:user_id>',members.memberView, name='member-view'),
    path('/member/activate-user/<str:user_id>',members.activateUser, name='activate-user'),
    path('update-commission/', commissions.update_commission, name='update-commission'),

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