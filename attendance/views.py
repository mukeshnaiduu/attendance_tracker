import csv
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from .models import Attendance, Subject, Class, Student, Attendance
from .forms import ClassForm, StudentForm, SubjectForm
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
import json

# Configure logging
logger = logging.getLogger(__name__)




def hod_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.role == 'hod':
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("You don't have permission to access this page.")
    return _wrapped_view

def faculty_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.role == 'faculty':
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("You don't have permission to access this page.")
    return _wrapped_view



def register(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST['username']
        fullname = request.POST['fullname']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        role = request.POST['role']
        secret_code = request.POST.get('secret_code', '')

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('register')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return redirect('register')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken.')
            return redirect('register')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if role == 'hod' and secret_code != 'hod':
            messages.error(request, 'Invalid secret code for HoD.')
            return redirect('register')

        try:
            with transaction.atomic():
                user = User.objects.create_user(username, email, password)
                user.profile.fullname = fullname
                user.profile.role = role
                user.save()
                messages.success(request, 'Registration successful.')
                return redirect('login')
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            messages.error(request, 'An error occurred during registration. Please try again.')
            return redirect('register')
    
    return render(request, 'attendance/register.html')

def login_view(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return redirect('login')
            
        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
                return redirect('login')
        except Exception as e:
            logger.error(f"Error during login: {e}")
            messages.error(request, 'An error occurred during login. Please try again.')
            return redirect('login')
    
    return render(request, 'attendance/login.html')





@login_required(login_url='/login/')
@hod_required
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            try:
                subject = form.save()
                messages.success(request, f'Subject {subject.name} added successfully.')
                return redirect('subject_list')
            except Exception as e:
                messages.error(request, f'Error adding subject: {str(e)}')
    else:
        form = SubjectForm()
    
    return render(request, 'attendance/add_subject.html', {
        'form': form,
        'title': 'Add Subject'
    })


@login_required(login_url='/login/')
@hod_required
def add_class(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            try:
                class_obj = form.save()
                messages.success(request, f'Class {class_obj.name} - {class_obj.section} added successfully.')
                return redirect('class_list')
            except Exception as e:
                messages.error(request, f'Error adding class: {str(e)}')
    else:
        form = ClassForm()
    
    return render(request, 'attendance/add_class.html', {
        'form': form,
        'title': 'Add Class'
    })


@login_required(login_url='/login/')
@hod_required
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                student = form.save()
                messages.success(request, f'Student {student.name} added successfully.')
                return redirect('student_list')
            except Exception as e:
                messages.error(request, f'Error adding student: {str(e)}')
    else:
        form = StudentForm()
    
    return render(request, 'attendance/add_student.html', {
        'form': form,
        'title': 'Add Student'
    })




@login_required(login_url='/login/')
def student_list(request):
    # Get class filter from query parameters
    selected_class_id = request.GET.get('class_id')

    # Get all classes for the filter dropdown
    classes = Class.objects.all().order_by('name')
    
    # Filter students based on selected class
    students = Student.objects.all().order_by('roll_no')
    if selected_class_id:
        students = students.filter(class_name_id=selected_class_id)
    
    context = {
        'students': students,
        'classes': classes,
        'selected_class_id': selected_class_id
    }
    
    return render(request, 'attendance/student_list.html', context)




@login_required(login_url='/login/')
@hod_required
def update_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.save()
                    messages.success(request, f'Student {student.name} updated successfully.')
                return redirect('student_list')
            except Exception as e:
                messages.error(request, f'Error updating student: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'attendance/edit_student.html', {
        'form': form,
        'student': student
    })





@login_required(login_url='/login/')
@hod_required
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    try:
        student.delete()
        messages.success(request, f'Student {student.name} deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting student: {str(e)}')
        return redirect('student_list')





@login_required(login_url='/login/')
def subject_list(request):
    subjects = Subject.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        subjects = subjects.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(subjects, 10)
    page = request.GET.get('page')
    try:
        subjects = paginator.page(page)
    except PageNotAnInteger:
        subjects = paginator.page(1)
    except EmptyPage:
        subjects = paginator.page(paginator.num_pages)
    
    return render(request, 'attendance/subject_list.html', {'subjects': subjects})



@login_required(login_url='/login/')
@hod_required
def subject_edit(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            try:
                subject = form.save()
                messages.success(request, f'Subject {subject.name} ({subject.code}) updated successfully.')
                return redirect('subject_list')
            except Exception as e:
                messages.error(request, f'Error updating subject: {str(e)}')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'attendance/edit_subject.html', {
        'form': form,
        'subject': subject,
        'title': f'Edit Subject - {subject.name}'
    })



@login_required(login_url='/login/')
@hod_required
def subject_delete(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    try:
        subject.delete()
        messages.success(request, f'Subject {subject.name} ({subject.code}) deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting subject: {str(e)}')
        return redirect('subject_list')

# attendance/views.py

# Existing imports and code...

@login_required(login_url='/login/')
def class_list(request):
    classes = Class.objects.all().order_by('name', 'section')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        classes = classes.filter(
            Q(name__icontains=search_query) |
            Q(section__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(classes, 10)
    page = request.GET.get('page')
    try:
        classes = paginator.page(page)
    except PageNotAnInteger:
        classes = paginator.page(1)
    except EmptyPage:
        classes = paginator.page(paginator.num_pages)
    
    return render(request, 'attendance/class_list.html', {'classes': classes})



@login_required(login_url='/login/')
@hod_required
def edit_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            try:
                class_obj = form.save()
                messages.success(request, f'Class {class_obj.name} - {class_obj.section} updated successfully.')
                return redirect('class_list')
            except Exception as e:
                messages.error(request, f'Error updating class: {str(e)}')
    else:
        form = ClassForm(instance=class_obj)
    
    return render(request, 'attendance/edit_class.html', {
        'form': form,
        'class': class_obj
    })



@login_required(login_url='/login/')
@hod_required
def delete_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    try:
        class_obj.delete()
        messages.success(request, f'Class {class_obj.name} - {class_obj.section} deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting class: {str(e)}')
    return redirect('class_list')






@login_required(login_url='/login/')
def attendance_list(request):
    attendance_records = Attendance.objects.select_related(
        'student', 'subject'
    ).order_by('-date', '-created_at')
    
    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__range=[start_date, end_date])
        except ValueError:
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
    
    # Filter by class if provided
    class_id = request.GET.get('class_id')
    if class_id:
        attendance_records = attendance_records.filter(student__class_name_id=class_id)
    
    # Filter by subject if provided
    subject_id = request.GET.get('subject_id')
    if subject_id:
        attendance_records = attendance_records.filter(subject_id=subject_id)
    
    # Pagination
    paginator = Paginator(attendance_records, 20)  # Show 20 records per page
    page = request.GET.get('page')
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)
    
    context = {
        'attendance_records': records,
        'classes': Class.objects.all(),
        'subjects': Subject.objects.all(),
    }
    
    return render(request, 'attendance/attendance_list.html', context)

@login_required(login_url='/login/')
def take_attendance(request):
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        subject_id = request.POST.get('subject_id')
        date = request.POST.get('date')
        students = request.POST.getlist('students[]')
        remarks = request.POST.getlist('remarks[]')
        
        try:
            # Validate the date
            attendance_date = datetime.strptime(date, '%Y-%m-%d').date()
            current_date = timezone.now().date()

            if attendance_date > current_date:
                messages.error(request, 'Cannot mark attendance for future dates.')
                return redirect('take_attendance')

            with transaction.atomic():
                class_obj = Class.objects.get(id=class_id)
                subject = Subject.objects.get(id=subject_id)
                
                # Delete any existing attendance records for this class, subject and date
                Attendance.objects.filter(
                    student__class_name=class_obj,
                    subject=subject,
                    date=attendance_date
                ).delete()
                
                # Create new attendance records
                for student_id, remark in zip(students, remarks):
                    student = Student.objects.get(id=student_id)
                    status = request.POST.get(f'status_{student_id}') == 'present'
                    
                    Attendance.objects.create(
                        student=student,
                        subject=subject,
                        date=attendance_date,
                        status=status,
                        remarks=remark,
                        created_by=request.user
                    )
                
                messages.success(request, 'Attendance recorded successfully!')
                return redirect('attendance_list')
                
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('take_attendance')
        except Exception as e:
            messages.error(request, f'Error recording attendance: {str(e)}')
            return redirect('take_attendance')
    
    context = {
        'classes': Class.objects.all(),
        'today': timezone.now().date()
    }
    return render(request, 'attendance/take_attendance.html', context)

@login_required(login_url='/login/')
def edit_attendance(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    if request.method == 'POST':
        try:
            status = request.POST.get('status') == 'present'
            remarks = request.POST.get('remarks')
            
            attendance.status = status
            attendance.remarks = remarks
            attendance.save()

            messages.success(request, 'Attendance record updated successfully!')
            return redirect('attendance_list')
            
        except Exception as e:
            messages.error(request, f'Error updating attendance: {str(e)}')
    
    context = {
        'attendance': attendance
    }
    return render(request, 'attendance/edit_attendance.html', context)

@login_required(login_url='/login/')
def delete_attendance(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    try:
        attendance.delete()
        messages.success(request, 'Attendance record deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting attendance: {str(e)}')
    
    return redirect('attendance_list')

def get_subjects_by_class(request, class_id):
    try:
        class_obj = Class.objects.get(id=class_id)
        subjects = class_obj.subjects.all()
        data = [{'id': subject.id, 'name': subject.name} for subject in subjects]
        return JsonResponse({'subjects': data})
    except Class.DoesNotExist:
        return JsonResponse({'error': 'Class not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_students_by_class(request, class_id):
    try:
        students = Student.objects.filter(class_name_id=class_id)
        data = [{'id': student.id, 'fullname': student.name, 'rollno': student.roll_no} 
                for student in students]
        return JsonResponse({'students': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)





@login_required(login_url='/login/')
def attendance_success(request):
    return render(request, 'attendance/attendance_success.html')





@login_required(login_url='/login/')
def attendance_report(request):
    classes = Class.objects.all()
    selected_class_id = request.GET.get('class_id')
    page = request.GET.get('page', 1)
    items_per_page = 10
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    selected_class = None
    subjects = []
    students = []
    attendance_data = []
    subject_sessions = {}
    subject_averages = {}
    total_subject_sessions = 0
    
    total_students = 0
    students_above_75 = 0
    students_65_75 = 0
    students_below_65 = 0

    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id)
        subjects = selected_class.subjects.all()
        students_query = Student.objects.filter(class_name=selected_class)
        
        # Apply search filter if provided
        if search_query:
            students_query = students_query.filter(
                Q(name__icontains=search_query) | 
                Q(roll_no__icontains=search_query)
            )
        
        students = students_query.order_by('roll_no')
        total_students = students.count()

        # Initialize subject sessions and averages
        for subject in subjects:
            subject_id = str(subject.id)
            subject_sessions[subject_id] = 0
            subject_averages[subject_id] = 0

        attendance_query = Attendance.objects.filter(
            student__in=students
        )

        # Apply date range filter if provided
        if start_date and end_date:
            attendance_query = attendance_query.filter(
                date__range=[start_date, end_date]
            )

        # Process attendance data
        for student in students:
            student_records = attendance_query.filter(student=student)
            total_attended = student_records.filter(status=True).count()
            total_sessions = student_records.count()

            if total_sessions > 0:
                attendance_percentage = (total_attended / total_sessions) * 100
                student_data = {
                    'rollno': student.roll_no,
                    'fullname': student.name,
                    'subject_attendance': {},
                    'total_classes_attended': total_attended,
                    'total_sessions': total_sessions,
                    'percentage': attendance_percentage
                }

                # Update statistics
                if attendance_percentage > 75:
                    students_above_75 += 1
                elif 65 <= attendance_percentage <= 75:
                    students_65_75 += 1
                else:
                    students_below_65 += 1

                # Calculate subject-wise attendance
                for subject in subjects:
                    subject_id = str(subject.id)
                    subject_records = student_records.filter(subject=subject)
                    attended = subject_records.filter(status=True).count()
                    sessions = subject_records.count()
                    student_data['subject_attendance'][subject_id] = {
                        'attended': attended,
                        'total': sessions
                    }
                    subject_sessions[subject_id] = max(subject_sessions[subject_id], sessions)
                    
                    if sessions > 0:
                        subject_averages[subject_id] += (attended / sessions) * 100

                attendance_data.append(student_data)

        # Calculate final subject averages
        for subject_id in subject_averages:
            if total_students > 0:
                subject_averages[subject_id] /= total_students

        # Handle attendance range filtering
        filter_value = request.GET.get('filter')
        if filter_value:
            filtered_students = []
            for student in attendance_data:
                percentage = student['percentage']
                if filter_value == "below65" and percentage < 65:
                    filtered_students.append(student)
                elif filter_value == "65-75" and 65 <= percentage <= 75:
                    filtered_students.append(student)
                elif filter_value == "above75" and percentage > 75:
                    filtered_students.append(student)
            attendance_data = filtered_students

        # Paginate the attendance data
        paginator = Paginator(attendance_data, items_per_page)
        try:
            paginated_attendance = paginator.page(page)
        except PageNotAnInteger:
            paginated_attendance = paginator.page(1)
        except EmptyPage:
            paginated_attendance = paginator.page(paginator.num_pages)
        
        attendance_data = paginated_attendance

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': selected_class_id,
        'subjects': subjects,
        'attendance_data': attendance_data,
        'subject_sessions': subject_sessions,
        'subject_averages': subject_averages,
        'total_subject_sessions': total_subject_sessions,
        'current_filter': request.GET.get('filter', ''),
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'total_students': total_students,
        'students_above_75': students_above_75,
        'students_65_75': students_65_75,
        'students_below_65': students_below_65,
        'today': timezone.now().date()
    }
    return render(request, 'attendance/attendance_report.html', context)









@login_required(login_url='/login/')
def export_attendance_report(request, class_id):
    student_class = get_object_or_404(Class, id=class_id)
    subjects = student_class.subjects.all()
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    filter_value = request.GET.get('filter')
    export_format = request.GET.get('format', 'csv')
    
    # Build student query
    students_query = Student.objects.filter(class_name=student_class)
    if search_query:
        students_query = students_query.filter(
            Q(name__icontains=search_query) | 
            Q(roll_no__icontains=search_query)
        )
    students = students_query.order_by('roll_no')
    
    # Initialize statistics
    total_students = students.count()
    students_above_75 = 0
    students_65_75 = 0
    students_below_65 = 0
    subject_averages = {str(subject.id): 0 for subject in subjects}
    
    # Build attendance query
    attendance_query = Attendance.objects.filter(student__in=students)
    if start_date and end_date:
        attendance_query = attendance_query.filter(date__range=[start_date, end_date])
    
    # Prepare data
    attendance_data = []
    for student in students:
        student_records = attendance_query.filter(student=student)
        total_attended = student_records.filter(status=True).count()
        total_sessions = student_records.count()
        
        if total_sessions > 0:
            attendance_percentage = (total_attended / total_sessions) * 100
            
            # Update statistics
            if attendance_percentage > 75:
                students_above_75 += 1
            elif 65 <= attendance_percentage <= 75:
                students_65_75 += 1
            else:
                students_below_65 += 1
            
            student_data = {
                'rollno': student.roll_no,
                'name': student.name,
                'subject_attendance': {},
                'total_attended': total_attended,
                'total_sessions': total_sessions,
                'percentage': attendance_percentage
            }
            
            # Calculate subject-wise attendance
            for subject in subjects:
                subject_id = str(subject.id)
                subject_records = student_records.filter(subject=subject)
                attended = subject_records.filter(status=True).count()
                sessions = subject_records.count()
                student_data['subject_attendance'][subject_id] = {
                    'attended': attended,
                    'total': sessions
                }
                
                # Update subject averages
                if sessions > 0:
                    subject_averages[subject_id] += (attended / sessions) * 100
            
            # Apply percentage filter if specified
            if filter_value:
                percentage = student_data['percentage']
                if (filter_value == "below65" and percentage >= 65) or \
                   (filter_value == "65-75" and (percentage < 65 or percentage > 75)) or \
                   (filter_value == "above75" and percentage <= 75):
                    continue
            
            attendance_data.append(student_data)
    
    # Calculate final subject averages
    for subject_id in subject_averages:
        if total_students > 0:
            subject_averages[subject_id] /= total_students
    
    if export_format == 'pdf':
        # Create PDF using reportlab
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{student_class.name}_attendance_report.pdf"'
        
        # Create the PDF document
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"Attendance Report - {student_class.name} {student_class.section}", title_style))
        
        # Add date range if specified
        if start_date and end_date:
            date_text = Paragraph(
                f"Period: {start_date} to {end_date}",
                ParagraphStyle('DateRange', parent=styles['Normal'], alignment=TA_CENTER)
            )
            elements.append(date_text)
            elements.append(Spacer(1, 20))
        
        # Add statistics summary
        stats_style = ParagraphStyle('Stats', parent=styles['Normal'], fontSize=12, spaceAfter=12)
        elements.append(Paragraph(f"Total Students: {total_students}", stats_style))
        elements.append(Paragraph(f"Students Above 75%: {students_above_75}", stats_style))
        elements.append(Paragraph(f"Students Between 65-75%: {students_65_75}", stats_style))
        elements.append(Paragraph(f"Students Below 65%: {students_below_65}", stats_style))
        elements.append(Spacer(1, 20))
        
        # Create attendance distribution pie chart
        if total_students > 0:
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 25
            pie.width = 150
            pie.height = 150
            pie.data = [students_above_75, students_65_75, students_below_65]
            pie.labels = ['Above 75%', '65-75%', 'Below 65%']
            pie.slices.strokeWidth = 0.5
            pie.slices[0].fillColor = colors.green
            pie.slices[1].fillColor = colors.orange
            pie.slices[2].fillColor = colors.red
            drawing.add(pie)
            elements.append(Paragraph("Attendance Distribution", ParagraphStyle('ChartTitle', parent=styles['Heading2'], alignment=TA_CENTER)))
            elements.append(drawing)
            elements.append(Spacer(1, 20))
        
        # Create subject-wise attendance bar chart
        if subjects:
            drawing = Drawing(400, 200)
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 125
            bc.width = 300
            bc.data = [[subject_averages[str(subject.id)] for subject in subjects]]
            bc.categoryAxis.categoryNames = [subject.name for subject in subjects]
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = 100
            bc.valueAxis.valueStep = 20
            bc.bars[0].fillColor = colors.blue
            drawing.add(bc)
            elements.append(Paragraph("Subject-wise Average Attendance", ParagraphStyle('ChartTitle', parent=styles['Heading2'], alignment=TA_CENTER)))
            elements.append(drawing)
            elements.append(Spacer(1, 20))
        
        # Create detailed attendance table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ])
        
        # Create table data
        table_data = [['Roll No', 'Name'] + [s.name for s in subjects] + ['Total', 'Percentage']]
        for student in attendance_data:
            row = [
                student['rollno'],
                student['name']
            ]
            for subject in subjects:
                subject_data = student['subject_attendance'].get(str(subject.id), {'attended': 0, 'total': 0})
                row.append(f"{subject_data['attended']}/{subject_data['total']}")
            row.extend([
                f"{student['total_attended']}/{student['total_sessions']}",
                f"{student['percentage']:.2f}%"
            ])
            table_data.append(row)
        
        # Add table to PDF
        elements.append(Paragraph("Detailed Attendance Report", ParagraphStyle('TableTitle', parent=styles['Heading2'], alignment=TA_CENTER)))
        elements.append(Spacer(1, 10))
        table = Table(table_data)
        table.setStyle(table_style)
        elements.append(table)
        
        # Build the PDF
        doc.build(elements)
        return response
    else:
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{student_class.name}_attendance_report.csv"'
        
        writer = csv.writer(response)
        header = ['Roll No', 'Student Name']
        for subject in subjects:
            header.append(f"{subject.name} (Attended/Total)")
        header.extend(['Total Classes Attended', 'Total Classes Held', 'Percentage'])
        writer.writerow(header)
        
        for student in attendance_data:
            row = [student['rollno'], student['name']]
            for subject in subjects:
                subject_data = student['subject_attendance'].get(str(subject.id), {'attended': 0, 'total': 0})
                row.append(f"{subject_data['attended']}/{subject_data['total']}")
            row.extend([
                student['total_attended'],
                student['total_sessions'],
                f"{student['percentage']:.2f}%"
            ])
            writer.writerow(row)
        
        return response



def dashboard(request):
    # if not request.user.is_authenticated:
    #     return redirect('register')
        
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    context = {
        'total_students': Student.objects.count(),
        'total_classes': Class.objects.count(),
        'total_subjects': Subject.objects.count(),
        'user_role': None  # Default to None
    }

    if request.user.is_authenticated:
        context['user_role'] = request.user.profile.role


    # Today's attendance statistics
    today_attendance = Attendance.objects.filter(date=today)
    today_present = today_attendance.filter(status=True).count()
    today_total = today_attendance.count()
    context['today_present_count'] = today_present
    context['today_total_count'] = today_total
    context['today_attendance_percentage'] = round((today_present / today_total * 100) if today_total > 0 else 0, 1)

    # Overall attendance (30 days)
    monthly_attendance = Attendance.objects.filter(date__gte=thirty_days_ago)
    monthly_present = monthly_attendance.filter(status=True).count()
    monthly_total = monthly_attendance.count()
    context['monthly_present_count'] = monthly_present
    context['monthly_total_count'] = monthly_total
    context['overall_attendance_percentage'] = round((monthly_present / monthly_total * 100) if monthly_total > 0 else 0, 1)

    # Weekly attendance trend data (4 weeks)
    four_weeks_ago = today - timedelta(weeks=4)
    classes = Class.objects.all()
    weekly_data = []
    weekly_labels = []

    # Create 4 weekly buckets
    for week in range(4):
        week_end = today - timedelta(weeks=week)
        week_start = week_end - timedelta(days=6)
        
        # Format week label (e.g., "May 1-7")
        week_label = f"{week_start.strftime('%b %d')}-{week_end.strftime('%d')}"
        weekly_labels.append(week_label)
        
        # Calculate overall attendance for this week
        week_attendance = Attendance.objects.filter(date__range=[week_start, week_end])
        week_present = week_attendance.filter(status=True).count()
        week_total = week_attendance.count()
        overall_percentage = round((week_present / week_total * 100) if week_total > 0 else 0, 1)
        
        # Calculate class-wise attendance
        class_data = []
        for class_obj in classes:
            class_attendance = week_attendance.filter(student__class_name=class_obj)
            class_present = class_attendance.filter(status=True).count()
            class_total = class_attendance.count()
            class_percentage = round((class_present / class_total * 100) if class_total > 0 else 0, 1)
            
            class_data.append({
                'class_name': f"{class_obj.name} - {class_obj.section}",
                'percentage': class_percentage
            })
        
        weekly_data.append({
            'week': week_label,
            'overall': overall_percentage,
            'class_wise': class_data
        })

    # Prepare class statistics
    class_stats = []
    for class_obj in classes:
        # Get all attendance records for this class in the last 30 days
        class_attendance = Attendance.objects.filter(
            student__class_name=class_obj,
            date__gte=thirty_days_ago
        )
        
        # Calculate attendance distribution
        total_students = Student.objects.filter(class_name=class_obj).count()
        above_75 = 0
        between_65_75 = 0
        below_65 = 0
        
        for student in Student.objects.filter(class_name=class_obj):
            student_attendance = class_attendance.filter(student=student)
            student_present = student_attendance.filter(status=True).count()
            student_total = student_attendance.count()
            
            if student_total > 0:
                attendance_percentage = (student_present / student_total) * 100
                if attendance_percentage > 75:
                    above_75 += 1
                elif 65 <= attendance_percentage <= 75:
                    between_65_75 += 1
                else:
                    below_65 += 1
        
        # Calculate subject-wise attendance
        subjects = class_obj.subjects.all()
        subject_data = []
        for subject in subjects:
            subject_attendance = class_attendance.filter(subject=subject)
            subject_present = subject_attendance.filter(status=True).count()
            subject_total = subject_attendance.count()
            subject_percentage = round((subject_present / subject_total * 100) if subject_total > 0 else 0, 1)
            
            subject_data.append({
                'name': subject.name,
                'percentage': subject_percentage
            })
        
        class_stats.append({
            'class': {
                'id': class_obj.id,
                'name': class_obj.name,
                'section': class_obj.section
            },
            'above_75': above_75,
            'between_65_75': between_65_75,
            'below_65': below_65,
            'total_students': total_students,
            'subjects': subject_data
        })

    # Prepare data for the template
    context.update({
        'weekly_labels': json.dumps(weekly_labels),
        'weekly_data': json.dumps(list(reversed(weekly_data))),  # Most recent week first
        'classes': classes,
        'class_stats': json.dumps(class_stats)
    })

    # Recent attendance records with detailed information
    recent_records = Attendance.objects.select_related(
        'student', 'subject', 'student__class_name'
    ).order_by('-date', '-created_at')[:5]
    
    recent_attendance = []
    for record in recent_records:
        student_attendance = Attendance.objects.filter(
            student=record.student,
            date__gte=thirty_days_ago
        )
        student_present = student_attendance.filter(status=True).count()
        student_total = student_attendance.count()
        attendance_percentage = round((student_present / student_total * 100) if student_total > 0 else 0, 1)
        
        recent_attendance.append({
            'record': record,
            'attendance_percentage': attendance_percentage,
            'total_classes_attended': student_present,
            'total_sessions': student_total
        })
    
    context['recent_attendance'] = recent_attendance

    return render(request, 'attendance/dashboard.html', context)




@login_required(login_url='/login/')
def get_attendance_data(request):
    class_id = request.GET.get('class_id')
    response_data = {}
    
    if class_id:
        selected_class = Class.objects.get(id=class_id)
        students = Student.objects.filter(class_name=selected_class)
        total_sessions = sum(subject.default_classes_per_session for subject in selected_class.subjects.all())
        
        subject_avg_attendance = {}
        for subject in selected_class.subjects.all():
            subject_attendance = []
            for student in students:
                attendance_record = Attendance.objects.filter(student=student).first()
                if attendance_record and str(subject.id) in attendance_record.subject_attendance:
                    subject_attendance.append(attendance_record.subject_attendance[str(subject.id)])
            subject_avg_attendance[subject.name] = (sum(subject_attendance) / len(subject_attendance)) if subject_attendance else 0
        
        # Group data by attendance percentage
        below_65 = 0
        between_65_75 = 0
        above_75 = 0
        for student in students:
            attendance_record = Attendance.objects.filter(student=student).first()
            if attendance_record:
                percentage = attendance_record.calculate_percentage()
                if percentage < 65:
                    below_65 += 1
                elif 65 <= percentage <= 75:
                    between_65_75 += 1
                else:
                    above_75 += 1
        
        response_data = {
            'subject_avg_attendance': subject_avg_attendance,
            'attendance_groups': {
                'below_65': below_65,
                'between_65_75': between_65_75,
                'above_75': above_75,
            }
        }
    else:
        classes = Class.objects.all()
        class_avg_attendance = {}
        for class_obj in classes:
            students = Student.objects.filter(class_name=class_obj)
            total_sessions = sum(subject.default_classes_per_session for subject in class_obj.subjects.all())
            total_attendance = 0
            total_students = len(students)
    
            if total_students == 0:
                class_avg_attendance[class_obj.name] = 0
                continue
    
            for student in students:
                attendance_records = Attendance.objects.filter(student=student)
                student_total_attendance = 0
                student_total_sessions = 0
        
                for record in attendance_records:
                    student_total_attendance += record.total_classes_attended
                    student_total_sessions += record.total_sessions
        
                if student_total_sessions > 0:
                    student_attendance_percentage = (student_total_attendance / student_total_sessions) * 100
                    total_attendance += student_attendance_percentage
    
            class_avg_attendance[class_obj.name] = total_attendance / total_students

        response_data = {
            'class_avg_attendance': class_avg_attendance
        }

    return JsonResponse(response_data)


@login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    return redirect(reverse('login'))






@login_required(login_url='/login/')
@hod_required
def modify_attendance(request):
    classes = Class.objects.all()
    today = timezone.now().date()
    
    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')
    date_str = request.GET.get('date')
    
    context = {
        'classes': classes,
        'today': today
    }
    
    if class_id:
        selected_class = get_object_or_404(Class, id=class_id)
        subjects = selected_class.subjects.all()
        context['subjects'] = subjects
        context['selected_class'] = selected_class
        
        if subject_id and date_str:
            try:
                selected_subject = get_object_or_404(Subject, id=subject_id)
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Get attendance records for the selected class, subject and date
                attendance_records = Attendance.objects.filter(
                    student__class_name=selected_class,
                    subject=selected_subject,
                    date=selected_date
                ).select_related('student').order_by('student__roll_no')
                
                # If no records exist, create them for all students
                if not attendance_records.exists():
                    students = Student.objects.filter(class_name=selected_class).order_by('roll_no')
                    new_records = []
                    for student in students:
                        new_records.append(Attendance(
                            student=student,
                            subject=selected_subject,
                            date=selected_date,
                            status=False,  # Default to absent
                            created_by=request.user
                        ))
                    Attendance.objects.bulk_create(new_records)
                    attendance_records = Attendance.objects.filter(
                        student__class_name=selected_class,
                        subject=selected_subject,
                        date=selected_date
                    ).select_related('student').order_by('student__roll_no')

                context.update({
                    'selected_subject': selected_subject,
                    'selected_date': selected_date,
                    'attendance_records': attendance_records
                })
                
            except (ValueError, Subject.DoesNotExist):
                messages.error(request, 'Invalid subject or date selected.')

    return render(request, 'attendance/modify_attendance.html', context)








@login_required(login_url='/login/')
def save_attendance(request):
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class_id')
            subject_id = request.POST.get('subject_id')
            date_str = request.POST.get('date')
            
            logger.info(f"Attempting to save attendance - Class: {class_id}, Subject: {subject_id}, Date: {date_str}")
            
            if not all([class_id, subject_id, date_str]):
                missing = []
                if not class_id: missing.append('class')
                if not subject_id: missing.append('subject')
                if not date_str: missing.append('date')
                error_msg = f"Missing required fields: {', '.join(missing)}"
                logger.error(error_msg)
                messages.error(request, error_msg)
                return redirect('modify_attendance')

            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            with transaction.atomic():
                updated_records = 0
                for key, value in request.POST.items():
                    if key.startswith('status_'):
                        attendance_id = key.split('_')[1]
                        attendance = get_object_or_404(Attendance, id=attendance_id)
                        
                        # Get new values
                        new_status = value == '1'
                        remarks_key = f'remarks_{attendance_id}'
                        new_remarks = request.POST.get(remarks_key, '')
                        
                        # Check if anything changed
                        if new_status != attendance.status or new_remarks != attendance.remarks:
                            attendance.status = new_status
                            attendance.remarks = new_remarks
                            attendance.save()
                            updated_records += 1
                            logger.info(f"Updated attendance record {attendance_id} - Status: {new_status}, Remarks: {new_remarks}")
                
                if updated_records > 0:
                    success_msg = f"Successfully updated {updated_records} attendance record(s)."
                    logger.info(success_msg)
                    messages.success(request, success_msg)
                else:
                    messages.info(request, 'No changes were made to attendance records.')
                
                return redirect(f'{reverse("modify_attendance")}?class_id={class_id}&subject_id={subject_id}&date={date_str}')
                
        except Attendance.DoesNotExist:
            error_msg = "Could not find the specified attendance record."
            logger.error(error_msg)
            messages.error(request, error_msg)
        except ValueError as e:
            error_msg = f"Invalid data format: {str(e)}"
            logger.error(error_msg)
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            logger.error(f"Error in save_attendance: {str(e)}")
            messages.error(request, error_msg)
    
    return redirect('modify_attendance')


@login_required
def export_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Get attendance data for the date range
            attendance_data = Attendance.objects.filter(
                date__range=[start_date, end_date]
            ).select_related('student', 'subject')
            
            # Create the response object
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{report_type}_attendance_report_{start_date}_to_{end_date}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Date', 'Student', 'Class', 'Subject', 'Status', 'Remarks'])
            
            for record in attendance_data:
                writer.writerow([
                    record.date,
                    record.student.name,
                    record.student.class_name,
                    record.subject.name,
                    'Present' if record.status else 'Absent',
                    record.remarks or ''
                ])

            messages.success(request, 'Report exported successfully!')
            return response

        except Exception as e:
            messages.error(request, f'Error exporting report: {str(e)}')
            return redirect('dashboard')
    
    return redirect('dashboard')

@login_required(login_url='/login/')
def reports(request):
    """View for generating and displaying various attendance reports."""
    classes = Class.objects.all()
    context = {
        'classes': classes,
        'start_date': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'end_date': timezone.now().strftime('%Y-%m-%d')
    }
    return render(request, 'attendance/reports.html', context)

