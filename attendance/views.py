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
    if request.method == 'POST':
        username = request.POST['username']
        fullname = request.POST['fullname']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        role = request.POST['role']
        secret_code = request.POST.get('secret_code', '')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if role == 'hod' and secret_code != 'cvrcoe':
            messages.error(request, 'Invalid secret code for HoD.')
            return redirect('register')

        user = User.objects.create_user(username, email, password)
        user.profile.fullname = fullname
        user.profile.role = role
        user.save()
        messages.success(request, 'Registration successful.')
        return redirect('login')
    
    return render(request, 'attendance/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    
    return render(request, 'attendance/register.html')





@login_required(login_url='/login/')
@hod_required
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            # Check if the subject with the same code or name (case-insensitive) already exists
            code = form.cleaned_data['code']
            name = form.cleaned_data['name']
            if Subject.objects.filter(code__iexact=code).exists() or Subject.objects.filter(name__iexact=name).exists():
                messages.error(request, 'Subject with the same name already exists.')
            else:
                form.save()
                return redirect('subject_list')  # assuming we have a subject list view
    else:
        form = SubjectForm()
    return render(request, 'attendance/add_subject.html', {'form': form})


@login_required(login_url='/login/')
@hod_required
def add_class(request):
    if request.method == 'POST':
        name = request.POST['name']
        subjects = request.POST.getlist('subjects')

        # Check if class with the same name already exists
        if Class.objects.filter(name__iexact=name).exists():
            messages.error(request, 'A class with the same name already exists.')
            return redirect('add_class')

        new_class = Class.objects.create(name=name)
        new_class.subjects.set(subjects)
        new_class.save()

        messages.success(request, 'Class added successfully.')
        return redirect('classes_list')

    subjects = Subject.objects.all()
    return render(request, 'attendance/add_class.html', {'subjects': subjects})


@login_required(login_url='/login/')
@hod_required
def add_student(request):
    classes = Class.objects.all()
    error_message = None
    if request.method == 'POST':
        # Process form submission
        rollno = request.POST.get('rollno')
        full_name = request.POST.get('full_name')
        student_class_id = request.POST.get('student_class')
        student_class = Class.objects.get(id=student_class_id)
        
        # Check if roll number already exists
        if Student.objects.filter(rollno=rollno).exists():
            error_message = "Roll number already exists."
        else:
            # Create a new Student instance
            Student.objects.create(
                rollno=rollno,
                full_name=full_name,
                student_class=student_class
            )
            # Redirect to student list page or wherever you want
            return redirect('student_list')
    
    # Render the form page with classes list and error message
    return render(request, 'attendance/add_student.html', {'classes': classes, 'error_message': error_message})




@login_required(login_url='/login/')
def student_list(request):
    classes = Class.objects.all()
    selected_class_id = request.GET.get('class_id')

    if selected_class_id:
        students = Student.objects.filter(student_class_id=selected_class_id).order_by('rollno')
    else:
        students = Student.objects.none()

    return render(request, 'attendance/student_list.html', {
        'classes': classes,
        'students': students,
        'selected_class_id': selected_class_id,
    })




@login_required(login_url='/login/')
@hod_required
def update_student(request, student_id):
    classes = Class.objects.all()
    error = None
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student details updated successfully.')
            return redirect('student_list')
        else:
            error = "Form is not valid. Please check the entered data."
    
    return render(request, 'attendance/update_student.html', {'error': error, 'student': student, 'classes': classes})



#delete krishna from the project

@login_required(login_url='/login/')
@hod_required
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.delete()
        return redirect('student_list')
    return render(request, 'attendance/student_confirm_delete.html', {'student': student})





@login_required(login_url='/login/')
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'attendance/subject_list.html', {'subjects': subjects})



@login_required(login_url='/login/')
@hod_required
def subject_edit(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'attendance/subject_edit.html', {'form': form})



@login_required(login_url='/login/')
@hod_required
def subject_delete(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')
    return render(request, 'attendance/subject_confirm_delete.html', {'subject': subject})

# attendance/views.py

# Existing imports and code...

@login_required(login_url='/login/')
def classes_list(request):
    classes = Class.objects.all()
    return render(request, 'attendance/class_list.html', {'classes': classes})



@login_required(login_url='/login/')
@hod_required
def class_edit(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_instance)
        if form.is_valid():
            form.save()
            return redirect('classes_list')
    else:
        form = ClassForm(instance=class_instance)
    return render(request, 'attendance/class_edit.html', {'form': form, 'class': class_instance})



@login_required(login_url='/login/')
@hod_required
def delete_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        class_instance.delete()
        return redirect('classes_list')
    return render(request, 'attendance/class_confirm_delete.html', {'class_instance': class_instance})






@login_required(login_url='/login/')
def take_attendance(request):
    classes = Class.objects.all()

    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        subject_id = request.POST.get('subject_id')

        selected_class = get_object_or_404(Class, id=class_id)
        selected_subject = get_object_or_404(Subject, id=subject_id)
        students = Student.objects.filter(student_class=selected_class)

        for student in students:
            attendance, created = Attendance.objects.get_or_create(
                roll_no=student.rollno,
                student_name=student.full_name,
                defaults={'subject_attendance': {}, 'subject_sessions': {}}
            )

            # Update subject sessions
            subject_sessions = attendance.subject_sessions or {}
            if str(subject_id) in subject_sessions:
                subject_sessions[str(subject_id)] += selected_subject.default_classes_per_session
            else:
                subject_sessions[str(subject_id)] = selected_subject.default_classes_per_session
            attendance.subject_sessions = subject_sessions

            # Update subject attendance if student is present
            subject_attendance = attendance.subject_attendance or {}
            if request.POST.get(f'attendance_{student.id}'):
                if str(subject_id) in subject_attendance:
                    subject_attendance[str(subject_id)] += selected_subject.default_classes_per_session
                else:
                    subject_attendance[str(subject_id)] = selected_subject.default_classes_per_session
            attendance.subject_attendance = subject_attendance

            attendance.save()

        messages.success(request, 'Attendance has been recorded successfully.')
        return redirect('attendance_success')

    return render(request, 'attendance/take_attendance.html', {'classes': classes})

def get_subjects_by_class(request, class_id):
    selected_class = get_object_or_404(Class, id=class_id)
    subjects = selected_class.subjects.all()
    data = {'subjects': [{'id': subject.id, 'name': subject.name} for subject in subjects]}
    return JsonResponse(data)

def get_students_by_class(request, class_id):
    selected_class = get_object_or_404(Class, id=class_id)
    students = Student.objects.filter(student_class=selected_class)
    data = {'students': [{'id': student.id, 'rollno': student.rollno, 'fullname': student.full_name} for student in students]}
    return JsonResponse(data)





@login_required(login_url='/login/')
def attendance_success(request):
    return render(request, 'attendance/attendance_success.html')





@login_required(login_url='/login/')
def attendance_report(request):
    classes = Class.objects.all()
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    subjects = []
    students = []
    attendance_data = []
    subject_sessions = {}
    total_subject_sessions = 0

    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id)
        subjects = selected_class.subjects.all()
        students = Student.objects.filter(student_class=selected_class).order_by('rollno')

        # Initialize subject sessions
        for subject in subjects:
            subject_sessions[str(subject.id)] = 0

        for student in students:
            attendance = Attendance.objects.filter(roll_no=student.rollno).first()
            if attendance:
                student_attendance = {
                    'rollno': student.rollno,
                    'fullname': student.full_name,
                    'subject_attendance': {},
                    'total_classes_attended': 0,
                    'total_sessions': attendance.total_sessions,
                    'percentage': attendance.attendance_percentage
                }

                for subject in subjects:
                    subject_id_str = str(subject.id)
                    attendance_count = attendance.subject_attendance.get(subject_id_str, 0)
                    student_attendance['subject_attendance'][subject_id_str] = attendance_count
                    student_attendance['total_classes_attended'] += attendance_count

                    # Update subject sessions
                    subject_sessions[subject_id_str] = attendance.subject_sessions.get(subject_id_str, 0)

                attendance_data.append(student_attendance)

        # Calculate total subject sessions
        total_subject_sessions = sum(subject_sessions.values())

        # Handle filtering
        filter_value = request.GET.get('filter')
        if filter_value:
            filtered_students = []
            for student in attendance_data:
                percentage = student['percentage']
                if filter_value == "below75" and percentage < 75:
                    filtered_students.append(student)
                elif filter_value == "below65" and percentage < 65:
                    filtered_students.append(student)
                elif filter_value == "65-75" and 65 <= percentage <= 75:
                    filtered_students.append(student)
                elif filter_value == "above75" and percentage > 75:
                    filtered_students.append(student)
            attendance_data = filtered_students

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': selected_class_id,
        'subjects': subjects,
        'attendance_data': attendance_data,
        'subject_sessions': subject_sessions,
        'total_subject_sessions': total_subject_sessions
    }
    return render(request, 'attendance/attendance_report.html', context)









@login_required(login_url='/login/')
def export_attendance_report(request, class_id):
    student_class = get_object_or_404(Class, id=class_id)
    subjects = student_class.subjects.all()
    students = Student.objects.filter(student_class=student_class)
    attendances = Attendance.objects.filter(roll_no__in=[student.rollno for student in students])

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{student_class.name}_attendance_report.csv"'

    writer = csv.writer(response)
    # Write the header row
    header = ['Roll No', 'Student Name']
    for subject in subjects:
        header.append(subject.name)
    header.extend(['Total Classes Attended', 'Total Classes Held', 'Percentage'])
    writer.writerow(header)

    # Create a dictionary for quick attendance lookup
    attendance_dict = {attendance.roll_no: attendance for attendance in attendances}

    for student in students:
        row = [student.rollno, student.full_name]
        total_attended = 0
        total_classes_held = 0
        percentage = 0

        attendance = attendance_dict.get(student.rollno)
        if attendance:
            for subject in subjects:
                attendance_count = attendance.subject_attendance.get(str(subject.id), 0)
                row.append(attendance_count)
                total_attended += attendance_count

            total_classes_held = attendance.total_sessions
            percentage = attendance.attendance_percentage
        else:
            row.extend([0] * len(subjects))

        row.extend([total_attended, total_classes_held, f"{percentage:.2f}%"])
        writer.writerow(row)

    return response



@login_required(login_url='/login/')
def dashboard(request):
    classes = Class.objects.all()
    return render(request, 'attendance/dashboard.html', {'classes': classes})




@login_required(login_url='/login/')
def get_attendance_data(request):
    class_id = request.GET.get('class_id')
    response_data = {}
    
    if class_id:
        selected_class = Class.objects.get(id=class_id)
        students = Student.objects.filter(student_class=selected_class)
        total_sessions = sum(subject.default_classes_per_session for subject in selected_class.subjects.all())
        
        subject_avg_attendance = {}
        for subject in selected_class.subjects.all():
            subject_attendance = []
            for student in students:
                attendance_record = Attendance.objects.filter(roll_no=student.rollno).first()
                if attendance_record and subject.id in attendance_record.subject_attendance:
                    subject_attendance.append(attendance_record.subject_attendance[subject.id])
            subject_avg_attendance[subject.name] = (sum(subject_attendance) / len(subject_attendance)) if subject_attendance else 0
        
        # Group data by attendance percentage
        below_65 = 0
        between_65_75 = 0
        above_75 = 0
        for student in students:
            attendance_record = Attendance.objects.filter(roll_no=student.rollno).first()
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
            students = Student.objects.filter(student_class=class_obj)
            total_sessions = sum(subject.default_classes_per_session for subject in class_obj.subjects.all())
            total_attendance = 0
            total_students = len(students)
    
            if total_students == 0:
                class_avg_attendance[class_obj.name] = 0
                continue
    
            for student in students:
                attendance_records = Attendance.objects.filter(roll_no=student.rollno)
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
    class_id = request.GET.get('class_id')
    if not class_id:
        classes = Class.objects.all()
        return render(request, 'attendance/modify_attendance.html', {'classes': classes})

    selected_class = get_object_or_404(Class, id=class_id)
    subjects = selected_class.subjects.all()
    students = Student.objects.filter(student_class=selected_class).order_by('rollno')

    attendance_data = []
    subject_sessions = {}
    for student in students:
        attendance = Attendance.objects.filter(roll_no=student.rollno).first()
        if attendance:
            student_data = {
                'rollno': student.rollno,
                'fullname': student.full_name,
                'subject_attendance': {},
                'total_classes_attended': attendance.total_classes_attended,
                'total_sessions': attendance.total_sessions,
                'percentage': attendance.attendance_percentage
            }

            for subject in subjects:
                subject_id_str = str(subject.id)
                student_data['subject_attendance'][subject_id_str] = attendance.subject_attendance.get(subject_id_str, 0)
                subject_sessions[subject_id_str] = attendance.subject_sessions.get(subject_id_str, 0)

            attendance_data.append(student_data)

    context = {
        'selected_class': selected_class,
        'subjects': subjects,
        'attendance_data': attendance_data ,
        'subject_sessions': subject_sessions,
    }

    return render(request, 'attendance/modify_attendance.html', context)








@login_required(login_url='/login/')
def save_attendance(request):
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        selected_class = get_object_or_404(Class, id=class_id)
        students = Student.objects.filter(student_class=selected_class)
        error_flag = False

        for student in students:
            attendance = Attendance.objects.filter(roll_no=student.rollno).first()
            if attendance:
                for subject in selected_class.subjects.all():
                    subject_id_str = str(subject.id)
                    attendance_key = f'attendance_{student.rollno}_{subject_id_str}'
                    if attendance_key in request.POST:
                        new_attendance_count = int(request.POST[attendance_key])
                        attendance.subject_attendance[subject_id_str] = new_attendance_count

                        # Check if the subject session exists
                        subject_sessions_count = attendance.subject_sessions.get(subject_id_str, 0)
                        if new_attendance_count > subject_sessions_count:
                            messages.error(request, f'Subject attendance for {student.full_name} in {subject} is greater than total sessions held for that subject.')
                            error_flag = True
                
                # Update total_classes_attended and attendance percentage only if no errors occurred
                if not error_flag:
                    attendance.total_classes_attended = sum(attendance.subject_attendance.values())
                    attendance.save()
        
        if error_flag:
            messages.error(request, ' ')
        
        return redirect('modify_attendance')  # Redirect to the same page or another as needed

    return redirect('modify_attendance')

