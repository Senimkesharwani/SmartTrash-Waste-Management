from django.urls import path
from . import views

urlpatterns = [
    # ---------------- USER ROUTES ----------------
    path('', views.index, name='index'),

    path('signup/', views.get_signup_page, name='signup'),
    path('signup_process/', views.signup_process, name='signup_process'),

    path('login/', views.get_login_page, name='login'),
    path('login_process/', views.login_process, name='login_process'),

    path('home/', views.get_user_dashboard, name='user_dashboard'),
    path('logout/', views.logout_user, name='logout'),

    path('raise-a-request/', views.get_raise_request_page, name='raise_request'),
    path('submit_request/', views.submit_request, name='submit_request'),
    path('my-requests/', views.get_my_requests, name='my_requests'),


    # ---------------- ADMIN ROUTES ----------------
    path('admin/', views.admin_root, name='admin_root'),
    path('admin/login/', views.admin_login_page, name='admin_login'),
    path('admin/login_process/', views.admin_login_process, name='admin_login_process'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('admin/all-requests/', views.admin_all_requests, name='admin_all_requests'),
    path('admin/assign-driver/', views.assign_driver, name='admin_assign_driver'),
    path('admin/unassign-driver/', views.unassign_driver, name='unassign-driver'),
    path('admin/reject-request/', views.reject_request, name='admin_reject_request'),


    path('admin/create-driver/', views.admin_create_driver_page, name='admin_create_driver_page'),
    path('admin/create-driver/process/', views.admin_create_driver, name='admin_create_driver'),

    path('admin/all-drivers/', views.admin_all_drivers, name='admin_all_drivers'),
    path('admin/delete-driver/<str:id>/', views.admin_delete_driver, name='admin_delete_driver'),

    path('admin/logout/', views.admin_logout, name='admin_logout'),


    # ---------------- DRIVER ROUTES ----------------
    path('driver/', views.driver_root, name='driver_root'),
    path('driver/login/', views.driver_login_page, name='driver_login'),
    path('driver/login_process/', views.driver_login_process, name='driver_login_process'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),

  
    path('driver/pending-requests/', views.driver_pending_requests, name='driver_pending_requests'),

    path('driver/resolve-request/', views.driver_resolve_request, name='driver_resolve'),
    path('driver/reject-request/', views.driver_reject_request, name='driver_reject'),
    path('driver/history/', views.driver_history, name='driver_history'),
    path('driver/logout/', views.driver_logout, name='driver_logout'),

    path('contact/', views.contact_page, name='contact'),
    path('contact_submit/', views.contact_submit, name='contact_submit'),
    path('report-bug/', views.report_bug_page, name='report_bug'),
    path('report_bug_submit/', views.report_bug_submit, name='report_bug_submit'),

]
