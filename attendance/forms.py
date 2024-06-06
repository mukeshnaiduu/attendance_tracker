# attendance/forms.py

from django import forms
from .models import Subject,Student,Class

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'default_classes_per_session']



class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['rollno', 'full_name', 'student_class']




class ClassForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Class
        fields = ['name', 'subjects']

