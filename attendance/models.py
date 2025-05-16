import django
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import JSONField
from django.core.validators import MinValueValidator, RegexValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_role(value):
    valid_roles = ['faculty', 'hod']
    if value not in valid_roles:
        raise ValidationError(f'{value} is not a valid role. Must be one of {", ".join(valid_roles)}')

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='Name can only contain letters and spaces'
            )
        ]
    )
    role = models.CharField(
        max_length=10,
        choices=[('faculty', 'Faculty'), ('hod', 'HoD')],
        validators=[validate_role]
    )

    class Meta:
        ordering = ['fullname']
        indexes = [
            models.Index(fields=['fullname']),
        ]

    def __str__(self):
        return self.fullname

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        unique=True,
        help_text="Enter the subject name (e.g., Mathematics, Physics)"
    )
    code = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9]+$',
                message='Code must contain only uppercase letters and numbers'
            )
        ],
        unique=True,
        help_text="Enter a unique subject code (e.g., MATH101)"
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='taught_subjects',
        help_text="Select the teacher for this subject"
    )
    default_classes_per_session = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Default number of classes per session"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def get_attendance_percentage(self):
        """Calculate the average attendance percentage for this subject."""
        attendance_records = self.attendance_records.all()
        if not attendance_records.exists():
            return 0
        
        total_present = attendance_records.filter(status=True).count()
        total_records = attendance_records.count()
        
        return round((total_present / total_records) * 100, 1) if total_records > 0 else 0

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']

class Class(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Enter the class name (e.g., Grade 10, First Year)"
    )
    section = models.CharField(
        max_length=10,
        help_text="Enter the section (e.g., A, B, C)"
    )
    subjects = models.ManyToManyField(
        Subject,
        related_name='classes',
        help_text="Select subjects for this class"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def get_attendance_percentage(self):
        """Calculate the average attendance percentage for this class."""
        total_attendance = 0
        total_students = self.students.count()
        
        if total_students == 0:
            return 0
        
        for student in self.students.all():
            attendance_records = student.attendance_records.all()
            if attendance_records.exists():
                student_attendance = attendance_records.filter(status=True).count()
                total_sessions = attendance_records.count()
                if total_sessions > 0:
                    total_attendance += (student_attendance / total_sessions) * 100
        
        return round(total_attendance / total_students, 1)

    @property
    def display_name(self):
        """Return the class name with section for display purposes"""
        return f"{self.name} - {self.section}"

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['name', 'section']
        unique_together = ['name', 'section']

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]

    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Enter the student's full name"
    )
    roll_no = models.CharField(
        max_length=20,
        help_text="Enter the student's roll number"
    )
    class_name = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='students',
        help_text="Select the student's class"
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        help_text="Select the student's gender"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def rollno(self):
        return self.roll_no

    @property
    def full_name(self):
        return self.name

    @property
    def student_class(self):
        return self.class_name

    def __str__(self):
        return f"{self.name} ({self.roll_no}) - {self.class_name}"

    class Meta:
        ordering = ['class_name', 'roll_no']
        unique_together = ['roll_no', 'class_name']

class Attendance(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(default=timezone.now)
    status = models.BooleanField(
        default=True,
        help_text="Check if the student was present"
    )
    remarks = models.TextField(
        blank=True,
        null=True,
        help_text="Any additional remarks about the attendance"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_attendance_records'
    )

    def total_classes_attended(self):
        """Return the total number of classes attended."""
        return self.student.attendance_records.filter(status=True).count()

    def total_sessions(self):
        """Return the total number of sessions."""
        return self.student.attendance_records.count()

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date}"

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ['student', 'subject', 'date']
        verbose_name_plural = "Attendance records"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set created_by on creation
            self.created_by = kwargs.pop('user', None)
        super().save(*args, **kwargs)
