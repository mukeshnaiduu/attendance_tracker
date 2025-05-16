# Attendance Management System

## Project Overview

The Attendance Management System is a web-based application designed to simplify and automate the process of tracking student attendance in educational institutions. It provides a user-friendly interface for both Heads of Department (HoD) and Faculty members to manage classes, subjects, students, and attendance records efficiently.

## Key Features

- **Role-Based Access Control:**

  - Separate dashboards and permissions for HoD and Faculty users.
  - Secure registration and login system with role selection.

- **Class & Subject Management:**

  - Add, edit, and delete classes and subjects.
  - Assign subjects to classes and teachers to subjects.

- **Student Management:**

  - Add, update, and remove student records.
  - Assign students to specific classes.

- **Attendance Tracking:**

  - Mark daily attendance for each class and subject.
  - Modify attendance records as needed.
  - Subject-wise attendance tracking for detailed analysis.

- **Reporting & Analytics:**

  - Generate attendance reports by class, subject, or student.
  - View attendance percentages and summary statistics.
  - Export reports for record-keeping.

- **User Experience:**
  - Responsive design for use on desktops and mobile devices.
  - Real-time feedback and error handling with Django messages.
  - Clean, modern UI using Bootstrap and Font Awesome.

## Technologies Used

**Frontend:**

- HTML5, CSS3, Bootstrap 5 for responsive design.
- JavaScript for interactive UI elements.

**Backend:**

- Django (Python) as the main web framework.
- PostgreSQL as the primary database.

**Other Tools & Libraries:**

- `django-crispy-forms` for enhanced form rendering.
- `reportlab` for generating PDF attendance reports.
- `python-dotenv` for environment variable management.
- `psycopg2-binary` for PostgreSQL database connectivity.
- Gunicorn as a WSGI server (for production).
- Whitenoise for serving static files in production.

## Getting Started

1. **Clone the repository:**

   ```sh
   git clone https://github.com/mukeshnaiduu/attendance_tracker.git
   cd attendance_tracker
   ```

2. **Create and activate a virtual environment:**

   ```sh
   python -m venv venv
   venv\Scripts\activate   # On Windows
   ```

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   - Copy `.env.example` to `.env` and update with your settings (if provided).

5. **Apply database migrations:**

   ```sh
   python manage.py migrate
   ```

6. **Create a superuser (for admin access):**

   ```sh
   python manage.py createsuperuser
   ```

7. **Run the development server:**

   ```sh
   python manage.py runserver
   ```

8. **Access the application:**
   - Open your browser and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Folder Structure

- `attendance/` - Main Django app containing models, views, forms, templates, and static files.
- `attendance_tracker/` - Project configuration files and settings.
- `templates/` - HTML templates for all pages.
- `static/` - Static files (CSS, JS, images).

## License

This project is for educational purposes. Please check the repository for license details.

---
