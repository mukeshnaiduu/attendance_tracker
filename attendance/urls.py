# attendance/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('',views.dashboard,name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),



    path('add_subject/', views.add_subject, name='add_subject'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/<int:subject_id>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:subject_id>/delete/', views.subject_delete, name='subject_delete'),



    path('add_class/', views.add_class, name='add_class'),
    path('classes/', views.classes_list, name='classes_list'),
    path('classes/<int:class_id>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:class_id>/delete/', views.delete_class, name='delete_class'),



    path('add_student/', views.add_student, name='add_student'),
    path('students/', views.student_list, name='student_list'),
    path('update_student/', views.update_student, name='update_student'),
    path('delete_student/<int:student_id>/', views.delete_student, name='delete_student'),


    path('take_attendance/', views.take_attendance, name='take_attendance'),
    path('get_subjects_by_class/<int:class_id>/', views.get_subjects_by_class, name='get_subjects_by_class'),
    path('get_students_by_class/<int:class_id>/', views.get_students_by_class, name='get_students_by_class'),
    path('attendance_success/', views.attendance_success, name='attendance_success'),
    path('attendance_report/', views.attendance_report, name='attendance_report'),
    path('export_attendance_report/<int:class_id>/', views.export_attendance_report, name='export_attendance_report'),

    path('modify_attendance/', views.modify_attendance, name='modify_attendance'),
    path('save_attendance/', views.save_attendance, name='save_attendance'),


    path('dashboard/', views.dashboard, name='dashboard'),
    path('get_attendance_data/', views.get_attendance_data, name='get_attendance_data'),
    path('get_attendance_data/<int:class_id>', views.get_attendance_data, name='get_attendance_data'),


    
    path('logout/', views.logout_view, name='logout'),

    
    # Add more paths here
]
