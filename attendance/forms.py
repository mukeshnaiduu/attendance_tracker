# attendance/forms.py

from django import forms
from django.core.validators import RegexValidator, MinValueValidator
from .models import Subject, Student, Class, Attendance
from django.core.exceptions import ValidationError
from django.db.models import Q

class SubjectForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-_]*$',
                message='Subject name can only contain letters, numbers, spaces, hyphens and underscores'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter subject name'
        })
    )
    
    code = forms.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9\-_]*$',
                message='Subject code can only contain uppercase letters, numbers, hyphens and underscores'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter subject code'
        })
    )
    
    default_classes_per_session = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter number of classes per session'
        })
    )

    teacher = forms.ModelChoiceField(
        queryset=None,
        empty_label='Select a teacher',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Subject
        fields = ['name', 'code', 'teacher', 'default_classes_per_session']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        # Get only users who are faculty (excluding HODs)
        self.fields['teacher'].queryset = User.objects.filter(
            profile__role='faculty'
        ).order_by('profile__fullname')

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            exists = Subject.objects.filter(code__iexact=code)
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise ValidationError('A subject with this code already exists.')
        return code.upper()

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            exists = Subject.objects.filter(name__iexact=name)
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise ValidationError('A subject with this name already exists.')
        return name.title()

class StudentForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='Name can only contain letters and spaces'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student name'
        })
    )
    
    roll_no = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter roll number'
        })
    )
    
    class_name = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('name', 'section'),
        empty_label='Select a class',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    gender = forms.ChoiceField(
        choices=Student.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Student
        fields = ['name', 'roll_no', 'class_name', 'gender']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the class_name field to use display_name for choices
        self.fields['class_name'].label_from_instance = lambda obj: obj.display_name

    def clean_roll_no(self):
        roll_no = self.cleaned_data.get('roll_no')
        class_name = self.cleaned_data.get('class_name')
        
        if roll_no and class_name:
            exists = Student.objects.filter(
                roll_no=roll_no,
                class_name=class_name
            )
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise ValidationError('A student with this roll number already exists in this class.')
        return roll_no

    def clean_name(self):
        name = self.cleaned_data.get('name')
        return name.title() if name else name

class ClassForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter class name'
        })
    )
    
    section = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter section (e.g., A, B, C)'
        })
    )
    
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Class
        fields = ['name', 'section', 'subjects']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        section = cleaned_data.get('section')

        if name and section:
            exists = Class.objects.filter(
                Q(name__iexact=name) & 
                Q(section__iexact=section)
            )
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise ValidationError('A class with this name and section already exists.')

        if section:
            cleaned_data['section'] = section.upper()

        return cleaned_data

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'subject', 'date', 'status', 'remarks']
        help_texts = {
            'student': 'Select the student',
            'subject': 'Select the subject',
            'date': 'Select the date (YYYY-MM-DD)',
            'status': 'Select attendance status',
            'remarks': 'Optional: Add any remarks about the attendance'
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter any remarks'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        subject = cleaned_data.get('subject')
        date = cleaned_data.get('date')

        if student and subject and date:
            exists = Attendance.objects.filter(
                student=student,
                subject=subject,
                date=date
            )
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise ValidationError('Attendance record already exists for this student, subject and date.')

