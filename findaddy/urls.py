from django.urls import path, re_path

# added manually
from django.conf import settings
from django.views.static import serve
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),

    # Login Pages
    path('login/', views.login, name='login'),
    path('signIn/', views.signIn, name='signIn'),
    path('pricing/', views.pricing, name='pricing'),
    path('register/', views.register, name='register'),
    path('signUp/', views.signUp, name='signUp'),
    path('resetPassword/', views.reset, name='resetPassword'),
    path('postReset/', views.postReset, name='postReset'),
    path('logout/', views.logout, name='logout'),

    # Admin Pages
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_view_users/', views.admin_view_users, name='admin_view_users'),
    path('admin_view_users_ajax/', views.admin_view_users_ajax,
         name='admin_view_users_ajax'),
    path('admin_view_reports/', views.admin_view_reports,
         name='admin_view_reports'),
    path('admin_view_reports_ajax/', views.admin_view_reports_ajax,
         name='admin_view_reports_ajax'),
    path('admin_report_data/', views.admin_report_data, name='admin_report_data'),
    path('admin_report_data_ajax/', views.admin_report_data_ajax,
         name='admin_report_data_ajax'),

    # User Pages
    path('dashboard/', views.landing, name='dashboard'),
    path('createReport/', views.createReport, name='createReport'),
    path('create_report_ajax/', views.create_report_ajax,
         name='create_report_ajax'),
    path('viewReport/', views.viewReport, name='viewReport'),
    path('reports_ajax/', views.reports_ajax, name='reports_ajax'),
    path('showReport/', views.showReport, name='showReport'),


    # static and media files
    re_path(r'static/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_ROOT}),
    re_path(r'media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT}),

]
