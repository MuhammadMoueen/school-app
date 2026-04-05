# School Management System

A comprehensive Django-based School Management System with a modern admin panel.

## Features   

### Admin Panel
- **Student Management**: Create, edit, delete student accounts
- **Teacher Management**: Create, edit, delete teacher accounts
- **Course Management**: Full CRUD operations for courses
- **Bulk Import**: CSV-based bulk student import
- **Statistics Dashboard**: Charts and analytics
- **Audit Logs**: Track all admin actions
- **Global Search**: Search users across the system

### Authentication
- Email-based authentication
- Role-based access (Admin, Teacher, Student)
- Profile editing with image cropping
- Default passwords: `Teacher@123` and `Student@123`

### Student Features
- View enrolled courses
- Submit marks reports
- View transcripts
- Edit profile

### Teacher Features
- Manage courses
- Create and manage enrollments
- Create and edit transcripts
- View student reports

## Tech Stack

- **Backend**: Django 6.0.3
- **Frontend**: Bootstrap 5.3.0, Font Awesome 6.4.0
- **Charts**: Chart.js 4.4.4
- **Database**: SQLite (development)
- **Python**: 3.14.3

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MuhammadMoueen/school-app.git
   cd school-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install django==6.0.3 pillow
   ```

4. **Run migrations**
   ```bash
   cd school_management
   python manage.py migrate
   ```

5. **Create superuser (Admin)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/panel/

## Quick Push to GitHub

### Option 1: Double-click Quick Push (Windows)
- Simply double-click `quick-push.bat` in the project root
- Enter your commit message when prompted
- Changes will be automatically committed and pushed

### Option 2: PowerShell Script
```powershell
.\auto-push.ps1 -commitMessage "Your commit message"
```

### Option 3: Manual Git Commands
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

## Project Structure

```
school-app/
├── school_management/
│   ├── main/               # Main application
│   │   ├── models.py       # Database models
│   │   ├── views.py        # View functions
│   │   ├── forms.py        # Django forms
│   │   ├── urls.py         # URL routing
│   │   └── context_processors.py  # Template context
│   ├── templates/          # HTML templates
│   │   ├── admin/          # Admin templates
│   │   ├── teacher/        # Teacher templates
│   │   ├── student/        # Student templates
│   │   └── shared/         # Shared templates
│   ├── static/             # Static files (CSS, JS, images)
│   └── media/              # User uploads
├── venv/                   # Virtual environment
├── auto-push.ps1           # Auto-push PowerShell script
├── quick-push.bat          # Quick push batch script
└── README.md               # This file
```

## Default Credentials

After creating accounts through admin panel:
- **Teachers**: Email + `Teacher@123`
- **Students**: Email + `Student@123`

## CSV Bulk Import Format

For bulk student import, use this CSV format:

```csv
full_name,email,student_class,section,roll_number
John Doe,john.doe@school.edu,Grade 10,A,001
Jane Smith,jane.smith@school.edu,Grade 10,B,002
```

## Context Processors

The project includes custom context processors that add:
- `notification_count`: Unread notification count
- `recent_notifications`: Recent 5 notifications
- `site_name`: School name
- `site_short_name`: Short name
- `current_year`: Academic year

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is for educational purposes.

## Author

**Muhammad Moueen**
- GitHub: [@MuhammadMoueen](https://github.com/MuhammadMoueen)
- Email: mmoueen123@gmail.com

## Acknowledgments

- Bootstrap for the UI framework
- Chart.js for data visualization
- Django framework for rapid development
