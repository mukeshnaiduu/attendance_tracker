from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from attendance.models import Subject, Class, Student, Attendance
from datetime import datetime, timedelta
import random
from django.db import transaction

class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        try:
            with transaction.atomic():
                # Create HOD user
                hod_user, created = User.objects.get_or_create(
                    username='hod',
                    email='hod@example.com',
                    defaults={'is_staff': True}
                )
                if created:
                    hod_user.set_password('hod@123')
                    hod_user.save()
                    hod_user.profile.fullname = 'Head of Department'
                    hod_user.profile.role = 'hod'
                    hod_user.profile.save()
                    self.stdout.write(self.style.SUCCESS('Created HOD user'))

                # Create faculty user
                faculty_user, created = User.objects.get_or_create(
                    username='faculty',
                    email='faculty@example.com'
                )
                if created:
                    faculty_user.set_password('faculty@123')
                    faculty_user.save()
                    faculty_user.profile.fullname = 'Faculty Member'
                    faculty_user.profile.role = 'faculty'
                    faculty_user.profile.save()
                    self.stdout.write(self.style.SUCCESS('Created faculty user'))

                # Create subjects
                subjects_data = [
                    {'name': 'Mathematics', 'code': 'MATH101', 'teacher': faculty_user},
                    {'name': 'Physics', 'code': 'PHY101', 'teacher': faculty_user},
                    {'name': 'Chemistry', 'code': 'CHEM101', 'teacher': faculty_user},
                    {'name': 'Computer Science', 'code': 'CS101', 'teacher': faculty_user},
                    {'name': 'English', 'code': 'ENG101', 'teacher': faculty_user},
                ]

                subjects = []
                for subject_data in subjects_data:
                    subject, created = Subject.objects.get_or_create(
                        code=subject_data['code'],
                        defaults={
                            'name': subject_data['name'],
                            'teacher': subject_data['teacher'],
                            'default_classes_per_session': 2
                        }
                    )
                    subjects.append(subject)
                    if created:
                        self.stdout.write(f'Created subject: {subject.name}')

                # Create classes
                classes_data = [
                    {'name': 'CSE', 'section': 'A'},
                    {'name': 'CSE', 'section': 'B'},
                    {'name': 'ECE', 'section': 'A'},
                ]

                classes = []
                for class_data in classes_data:
                    class_obj, created = Class.objects.get_or_create(
                        name=class_data['name'],
                        defaults={'section': class_data['section']}
                    )
                    if created:
                        class_obj.subjects.add(*subjects)
                        self.stdout.write(f'Created class: {class_obj.name}')
                    classes.append(class_obj)

                # Create students
                student_names = [
                    'John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis',
                    'Eva Wilson', 'Frank Thomas', 'Grace Miller', 'Henry Clark', 'Ivy Anderson'
                ]

                for class_obj in classes:
                    for i, name in enumerate(student_names, 1):
                        roll_no = f"{class_obj.name[:3]}{str(i).zfill(2)}"
                        student, created = Student.objects.get_or_create(
                            roll_no=roll_no,
                            defaults={
                                'name': name,
                                'class_name': class_obj
                            }
                        )
                        if created:
                            self.stdout.write(f'Created student: {student.name} in {class_obj.name}')

                # Create attendance records for the last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            current_date = start_date

            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday to Friday only
                    for class_obj in classes:
                        students = list(Student.objects.filter(class_name=class_obj))
                        total_students = len(students)

                        # Divide students into groups for attendance categories
                        group_low = students[:total_students // 3]                 # < 65%
                        group_mid = students[total_students // 3: 2 * total_students // 3]  # 65%–75%
                        group_high = students[2 * total_students // 3:]            # > 75%

                        for subject in subjects[:2]:  # First two subjects only
                            for student in group_low:
                                is_present = random.random() < 0.5  # ~50% attendance
                                Attendance.objects.get_or_create(
                                    student=student,
                                    subject=subject,
                                    date=current_date,
                                    defaults={
                                        'status': is_present,
                                        'remarks': 'Sample attendance record',
                                        'created_by': faculty_user
                                    }
                                )

                            for student in group_mid:
                                is_present = random.random() < 0.7  # ~70% attendance
                                Attendance.objects.get_or_create(
                                    student=student,
                                    subject=subject,
                                    date=current_date,
                                    defaults={
                                        'status': is_present,
                                        'remarks': 'Sample attendance record',
                                        'created_by': faculty_user
                                    }
                                )

                            for student in group_high:
                                is_present = random.random() < 0.9  # ~90% attendance
                                Attendance.objects.get_or_create(
                                    student=student,
                                    subject=subject,
                                    date=current_date,
                                    defaults={
                                        'status': is_present,
                                        'remarks': 'Sample attendance record',
                                        'created_by': faculty_user
                                    }
                                )
                current_date += timedelta(days=1)


                self.stdout.write(self.style.SUCCESS('Successfully created sample data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample data: {str(e)}')) 