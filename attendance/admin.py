from django.contrib import admin
from .models import Attendance, Class, Student, Subject

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'student_name', 'total_classes_attended', 'total_sessions', 'attendance_percentage')
    search_fields = ('student_name', 'roll_no')
    list_filter = ('student_name',)
    
    def attendance_percentage(self, obj):
        return f"{obj.attendance_percentage:.2f}%"

class ClassAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class StudentAdmin(admin.ModelAdmin):
    list_display = ('rollno', 'full_name', 'student_class')
    search_fields = ('full_name', 'rollno')
    list_filter = ('student_class',)

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Subject, SubjectAdmin)
