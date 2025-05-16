# attendance/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('export-report/', views.export_report, name='export_report'),
    
    # Class URLs
    path('classes/', views.class_list, name='class_list'),
    path('add_class/', views.add_class, name='add_class'),
    path('classes/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('classes/<int:class_id>/delete/', views.delete_class, name='delete_class'),
    
    # Subject URLs
    path('subjects/', views.subject_list, name='subject_list'),
    path('add_subject/', views.add_subject, name='add_subject'),
    path('subjects/<int:subject_id>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:subject_id>/delete/', views.subject_delete, name='delete_subject'),
    
    # Student URLs
    path('students/', views.student_list, name='student_list'),
    path('add_student/', views.add_student, name='add_student'),
    path('students/<int:student_id>/edit/', views.update_student, name='update_student'),
    path('students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    
    # Attendance URLs
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('take_attendance/', views.take_attendance, name='take_attendance'),
    path('attendance/<int:attendance_id>/edit/', views.edit_attendance, name='edit_attendance'),
    path('attendance/<int:attendance_id>/delete/', views.delete_attendance, name='delete_attendance'),
    
    # Reports
    path('reports/', views.reports, name='reports'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # API endpoints
    path('get_subjects_by_class/<int:class_id>/', views.get_subjects_by_class, name='get_subjects_by_class'),
    path('get_students_by_class/<int:class_id>/', views.get_students_by_class, name='get_students_by_class'),
    path('attendance_success/', views.attendance_success, name='attendance_success'),
    
    # Attendance report URLs
    path('attendance_report/', views.attendance_report, name='attendance_report'),
    path('attendance_report/export/<int:class_id>/', views.export_attendance_report, name='export_attendance_report'),

    # Modify attendance URLs
    path('modify_attendance/', views.modify_attendance, name='modify_attendance'),
    path('save_attendance/', views.save_attendance, name='save_attendance'),

    path('get_attendance_data/', views.get_attendance_data, name='get_attendance_data'),
    path('get_attendance_data/<int:class_id>/', views.get_attendance_data, name='get_attendance_data'),
]
