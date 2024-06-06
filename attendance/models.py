import django
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import JSONField

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=[('faculty', 'Faculty'), ('hod', 'HoD')])

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()



class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    default_classes_per_session = models.IntegerField(default=1)

    def __str__(self):
        return self.name

class Class(models.Model):
    name = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject)  # Keeps track of the total number of sessions

    def __str__(self):
        return self.name

class Student(models.Model):
    rollno = models.IntegerField(unique=True)  # Renamed field
    full_name = models.CharField(max_length=100,default=None)
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE)

    def __str__(self):
        return self.full_name




class Attendance(models.Model):
    roll_no = models.IntegerField()
    student_name = models.CharField(max_length=100)
    subject_attendance = JSONField(default=dict)
    subject_sessions = JSONField(default=dict)  # Track the sessions for each subject
    total_classes_attended = models.IntegerField(default=0)  # Total classes attended by the student
    total_sessions = models.IntegerField(default=0)  # Total sessions for the class

    def calculate_total_classes_attended(self):
        total_attendance = sum(self.subject_attendance.values())
        self.total_classes_attended = total_attendance

    def calculate_total_sessions(self):
        total_sessions = sum(self.subject_sessions.values())
        self.total_sessions = total_sessions

    def calculate_percentage(self):
        if self.total_sessions > 0:
            return (self.total_classes_attended / self.total_sessions) * 100
        else:
            return 0

    def save(self, *args, **kwargs):
        self.calculate_total_classes_attended()
        self.calculate_total_sessions()
        super().save(*args, **kwargs)

    @property
    def attendance_percentage(self):
        return self.calculate_percentage()

    def __str__(self):
        return f"{self.roll_no} - {self.student_name}"
