from django.contrib import admin
from .models import Profile, Subject, Class, Student, Attendance

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'role', 'user')
    list_filter = ('role',)
    search_fields = ('fullname', 'user__username')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'teacher', 'default_classes_per_session')
    list_filter = ('teacher',)
    search_fields = ('name', 'code')

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'section')
    list_filter = ('subjects',)
    search_fields = ('name', 'section')
    filter_horizontal = ('subjects',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_no', 'class_name', 'gender')
    list_filter = ('class_name', 'gender')
    search_fields = ('name', 'roll_no')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'date', 'status', 'created_by')
    list_filter = ('status', 'date', 'subject', 'student__class_name')
    search_fields = ('student__name', 'subject__name')
    date_hierarchy = 'date'
