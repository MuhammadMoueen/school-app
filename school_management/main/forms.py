from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, PreassignedEmail, Course, Enrollment, Transcript, MarksReport, ReportReply, AuditLog, Lecture, Attendance, Quiz, Question, QuizAttempt, QuizAnswer, LectureProgress, DiscussionThread, DiscussionReply
from django.utils import timezone
import csv
import io
import random


class TeacherSignupForm(UserCreationForm):
    """Form for teacher registration"""
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your full name',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'class': 'form-control'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password (minimum 8 characters)',
            'class': 'form-control'
        }),
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'password1', 'password2']
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        return password2
    
    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        full_name = self.cleaned_data.get('full_name')
        
        # Split full name into first and last name
        name_parts = full_name.strip().split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user.email = self.cleaned_data.get('email')
        user.role = 'teacher'
        
        if commit:
            user.save()
        return user


class StudentSignupForm(forms.ModelForm):
    """Form for student registration with pre-assigned email validation and auto-password"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your assigned Gmail/Email address',
            'class': 'form-control'
        }),
        label='Assigned Email Address',
        help_text='Enter the email address assigned to you by the admin'
    )
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your full name',
            'class': 'form-control'
        }),
        label='Full Name'
    )
    
    class Meta:
        model = User
        fields = ['email', 'full_name']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Check if email is pre-assigned and not yet used
        try:
            preassigned = PreassignedEmail.objects.get(email=email, is_used=False)
            # Email exists and is available
        except PreassignedEmail.DoesNotExist:
            # Check if email already exists as registered user
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    'This email is already registered. Please contact the coordinator if you believe this is an error.'
                )
            else:
                raise forms.ValidationError(
                    'This email has not been assigned by the Admin/Coordinator. '
                    'Please contact the coordinator to get an assigned email address.'
                )
        
        return email
    
    def save(self, commit=True):
        email = self.cleaned_data.get('email')
        
        # Get preassigned email to generate username
        preassigned = PreassignedEmail.objects.get(email=email, is_used=False)
        generated_username = preassigned.generate_username()
        
        # Ensure username is unique
        username = generated_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{generated_username}{counter}"
            counter += 1
        
        # Create new User object
        user = super().save(commit=False)
        user.username = username
        user.email = email
        user.role = 'student'
        user.is_active = True
        
        # Set full name
        full_name = self.cleaned_data.get('full_name')
        name_parts = full_name.strip().split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Set default password: Student@123
        user.set_password('Student@123')
        
        if commit:
            user.save()
            
            # Mark preassigned email as used
            preassigned.is_used = True
            preassigned.used_at = timezone.now()
            preassigned.save()
        
        return user


class CustomLoginForm(forms.Form):
    """Custom login form with styled widgets - supports username or email"""
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'placeholder': 'Username or Email',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-control'
        })
    )


# Forms for Teacher Dashboard Operations

class AssignEmailForm(forms.ModelForm):
    """Form to assign email to students"""
    class Meta:
        model = PreassignedEmail
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter student Gmail/Email address',
                'class': 'form-control'
            })
        }


class CourseForm(forms.ModelForm):
    """Form to create/edit subjects"""
    class Meta:
        model = Course
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Subject Name (e.g., Biology)',
                'class': 'form-control'
            }),
            'code': forms.TextInput(attrs={
                'placeholder': 'Subject Code (e.g., BIO101)',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Subject description',
                'class': 'form-control',
                'rows': 3
            })
        }
        labels = {
            'name': 'Subject Name',
            'code': 'Subject Code',
            'description': 'Description'
        }


class EnrollmentForm(forms.ModelForm):
    """Form to enroll students in subjects"""
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Student'
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Subject'
    )
    
    class Meta:
        model = Enrollment
        fields = ['student', 'course']


class TranscriptForm(forms.ModelForm):
    """Form to create/edit transcripts"""
    class Meta:
        model = Transcript
        fields = ['marks_obtained', 'total_marks', 'grade', 'remarks']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={
                'placeholder': 'Marks obtained',
                'class': 'form-control',
                'step': '0.01',
                'id': 'id_marks_obtained'
            }),
            'total_marks': forms.NumberInput(attrs={
                'placeholder': 'Total marks',
                'class': 'form-control',
                'step': '0.01',
                'id': 'id_total_marks'
            }),
            'grade': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'id': 'id_grade',
                'style': 'background-color: #f5f5f5; cursor: not-allowed;'
            }),
            'remarks': forms.Textarea(attrs={
                'placeholder': 'Additional remarks',
                'class': 'form-control',
                'rows': 3
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make grade field not required since it's auto-calculated
        self.fields['grade'].required = False


# Forms for Student Dashboard Operations

class MarksReportForm(forms.ModelForm):
    """Form for students to report marks issues"""
    class Meta:
        model = MarksReport
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'placeholder': 'Describe the issue with your marks...',
                'class': 'form-control',
                'rows': 4
            })
        }


class ReportReplyForm(forms.ModelForm):
    """Form for replying to marks reports"""
    class Meta:
        model = ReportReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'placeholder': 'Type your reply...',
                'class': 'form-control',
                'rows': 3
            })
        }


# Forms for Admin/Coordinator Operations

class AdminCreateStudentForm(forms.ModelForm):
    """Form for admin to create student account directly - no signup needed"""
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter student full name (e.g., M Moueen)',
            'class': 'form-control'
        }),
        label='Student Full Name',
        help_text='Email will be auto-generated from name (e.g., M Moueen → mmoueen123@school.edu.pk)'
    )
    
    class Meta:
        model = User
        fields = []
    
    def save(self, commit=True):
        full_name = self.cleaned_data.get('full_name').strip()
        
        # Parse name: first letter + last name
        name_parts = full_name.split()
        if len(name_parts) < 2:
            # If only one name, use it as both first and last
            first_letter = name_parts[0][0].lower()
            last_name = name_parts[0].lower()
        else:
            first_letter = name_parts[0][0].lower()
            last_name = name_parts[-1].lower()  # Use last part as last name
        
        # Generate base email with random 4-digit code
        random_code = random.randint(1000, 9999)
        base_email = f"{first_letter}{last_name}{random_code}@school.edu.pk"
        email = base_email
        
        # Ensure email is unique - if exists, generate new random code
        while User.objects.filter(email=email).exists():
            random_code = random.randint(1000, 9999)
            email = f"{first_letter}{last_name}{random_code}@school.edu.pk"
        
        # Generate username from email
        base_username = email.split('@')[0].lower()
        username = base_username
        counter = 1
        
        # Ensure username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user instance directly
        user = User()
        user.username = username
        user.email = email
        user.role = 'student'
        user.is_active = True
        
        # Set default password: Student@123
        user.set_password('Student@123')
        
        # Set full name
        name_parts = full_name.strip().split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if commit:
            user.save()
        return user


# Profile Edit Form for Teachers and Students
class ProfileEditForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your full name',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your phone number',
            'class': 'form-control'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter your address',
            'class': 'form-control',
            'rows': 3
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Upload a profile picture (JPG, PNG, GIF)'
    )
    
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'address', 'profile_picture']
    
    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        # Pre-populate full_name from first_name and last_name
        if self.instance:
            self.fields['full_name'].initial = self.instance.get_full_name()
    
    def clean_profile_picture(self):
        """Validate profile picture file type and size"""
        picture = self.cleaned_data.get('profile_picture')
        
        if picture:
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            file_extension = picture.name.lower().split('.')[-1]
            if f'.{file_extension}' not in valid_extensions:
                raise forms.ValidationError('Only JPG, PNG, and GIF images are allowed.')
            
            # Check file size (2MB max)
            max_size = 2 * 1024 * 1024  # 2MB in bytes
            if picture.size > max_size:
                raise forms.ValidationError('Image file size must be less than 2MB.')
        
        return picture
    
    def save(self, commit=True):
        user = super(ProfileEditForm, self).save(commit=False)
        full_name = self.cleaned_data.get('full_name', '')
        
        # Split full name into first and last name
        name_parts = full_name.strip().split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if commit:
            user.save()
        return user


# ==================== COMPREHENSIVE ADMIN FORMS ====================

class AdminCreateTeacherForm(forms.ModelForm):
    """Form for admin to create teacher accounts - simplified version"""
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter teacher full name (e.g., M Nouman)',
            'class': 'form-control'
        }),
        label='Teacher Full Name',
        help_text='Email will be auto-generated from name (e.g., M Nouman → mnouman123@teacher.edu.pk)'
    )
    
    class Meta:
        model = User
        fields = []
    
    def save(self, commit=True):
        full_name = self.cleaned_data.get('full_name', '').strip()
        
        # Parse name: first letter + last name
        name_parts = full_name.split()
        if len(name_parts) < 2:
            # If only one name, use it as both first and last
            first_letter = name_parts[0][0].lower()
            last_name = name_parts[0].lower()
        else:
            first_letter = name_parts[0][0].lower()
            last_name = name_parts[-1].lower()  # Use last part as last name
        
        # Generate base email with random 4-digit code
        random_code = random.randint(1000, 9999)
        base_email = f"{first_letter}{last_name}{random_code}@teacher.edu.pk"
        email = base_email
        
        # Ensure email is unique - if exists, generate new random code
        while User.objects.filter(email=email).exists():
            random_code = random.randint(1000, 9999)
            email = f"{first_letter}{last_name}{random_code}@teacher.edu.pk"
        
        # Generate username from email
        base_username = email.split('@')[0].lower()
        username = base_username
        counter = 1
        
        # Ensure username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user instance
        user = User()
        user.username = username
        user.email = email
        user.role = 'teacher'
        user.is_active = True
        
        # Set default password: Teacher@123
        user.set_password('Teacher@123')
        
        # Set full name
        name_parts = full_name.strip().split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if commit:
            user.save()
        return user


class AdminEditUserForm(forms.ModelForm):
    """Form for admin to edit user (student/teacher) details"""
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter full name',
            'class': 'form-control'
        }),
        label='Full Name'
    )
    
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'address', 'department', 'student_class', 'section', 'roll_number']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address', 'rows': 3}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department (for teachers)'}),
            'student_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class (for students)'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Section (for students)'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roll Number (for students)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate full_name
        if self.instance:
            self.fields['full_name'].initial = self.instance.get_full_name()
            
            # Show/hide fields based on role
            if self.instance.role == 'teacher':
                self.fields.pop('student_class', None)
                self.fields.pop('section', None)
                self.fields.pop('roll_number', None)
            elif self.instance.role == 'student':
                self.fields.pop('department', None)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '')
        
        # Split full name
        name_parts = full_name.strip().split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if commit:
            user.save()
        return user



class BulkStudentImportForm(forms.Form):
    """Form for bulk importing students via CSV"""
    csv_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        label='CSV File',
        help_text='Upload a CSV file with columns: full_name, email, student_class, section, roll_number'
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file.name.endswith('.csv'):
            raise ValidationError('File must be a CSV file.')
        
        # Validate CSV structure
        try:
            file_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_data))
            
            required_fields = ['full_name', 'email']
            headers = csv_reader.fieldnames
            
            for field in required_fields:
                if field not in headers:
                    raise ValidationError(f'CSV must contain "{field}" column.')
            
            # Reset file pointer
            csv_file.seek(0)
            
        except Exception as e:
            raise ValidationError(f'Error reading CSV file: {str(e)}')
        
        return csv_file


class AdminCourseForm(forms.ModelForm):
    """Form for admin to create/manage courses"""
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(role='teacher'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Assign Teacher',
        required=True
    )
    
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'teacher']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Course Name',
                'class': 'form-control'
            }),
            'code': forms.TextInput(attrs={
                'placeholder': 'Course Code (e.g., CS101)',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Course Description',
                'class': 'form-control',
                'rows': 3
            })
        }


# ==================== LECTURE/MATERIAL UPLOAD FORMS ====================

class LectureForm(forms.ModelForm):
    """Form for teachers to upload course materials/lectures"""
    
    class Meta:
        model = Lecture
        fields = ['course', 'title', 'description', 'file', 'order', 'is_published']
        widgets = {
            'course': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Lecture Title (e.g., Introduction to Python)',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe the lecture content (optional)',
                'class': 'form-control',
                'rows': 4
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*,audio/*,image/*,.pdf,.doc,.docx'
            }),
            'order': forms.NumberInput(attrs={
                'placeholder': 'Display Order (e.g., 1, 2, 3...)',
                'class': 'form-control',
                'min': 0
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter courses to only show courses taught by this teacher
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)
        # Set order field default value
        self.fields['order'].initial = 0
        # is_published default to True
        self.fields['is_published'].initial = True
    
    def clean_file(self):
        """Validate uploaded file size and type"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (50MB max for videos, 10MB for others)
            max_size = 50 * 1024 * 1024  # 50MB in bytes
            
            # Get file extension
            file_extension = file.name.lower().split('.')[-1]
            
            # Allowed extensions
            video_exts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm']
            audio_exts = ['mp3', 'wav', 'ogg', 'm4a', 'flac']
            doc_exts = ['pdf', 'doc', 'docx', 'txt', 'rtf']
            image_exts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
            
            all_allowed = video_exts + audio_exts + doc_exts + image_exts
            
            if file_extension not in all_allowed:
                raise forms.ValidationError(
                    f'File type .{file_extension} is not supported. '
                    f'Allowed types: video, audio, document (PDF, DOC), and image files.'
                )
            
            # Set size limit based on file type
            if file_extension in video_exts:
                max_size = 50 * 1024 * 1024  # 50MB for videos
            else:
                max_size = 10 * 1024 * 1024  # 10MB for others
            
            if file.size > max_size:
                max_size_mb = max_size / (1024 * 1024)
                raise forms.ValidationError(
                    f'File size must be less than {max_size_mb:.0f}MB.'
                )
        
        return file
    
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'teacher']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 3}),
        }


class SearchFilterForm(forms.Form):
    """Form for searching and filtering users"""
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, username, email...',
            'class': 'form-control'
        }),
        label='Search'
    )
    role_filter = forms.ChoiceField(
        choices=[('all', 'All Roles'), ('student', 'Students'), ('teacher', 'Teachers')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Filter by Role'
    )
    department_filter = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Filter by department',
            'class': 'form-control'
        }),
        label='Department'
    )


# ==================== ATTENDANCE FORMS ====================

class AttendanceForm(forms.ModelForm):
    """Form for marking student attendance"""
    
    class Meta:
        model = Attendance
        fields = ['status', 'remarks']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional remarks'
            })
        }


class BulkAttendanceForm(forms.Form):
    """Form for marking multiple students' attendance at once"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Attendance Date'
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Course'
    )
    
    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)


# ==================== QUIZ FORMS ====================

class QuizForm(forms.ModelForm):
    """Form for creating/editing quizzes"""
    
    class Meta:
        model = Quiz
        fields = ['course', 'title', 'description', 'duration_minutes', 'total_marks', 'passing_marks', 'is_published']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quiz Title (e.g., Midterm Exam, Chapter 1 Quiz)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description and instructions for the quiz'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Duration in minutes'
            }),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Total marks'
            }),
            'passing_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Passing marks'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)


class QuestionForm(forms.ModelForm):
    """Form for adding/editing quiz questions"""
    
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'marks', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter the question'
            }),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'option_a': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option A'
            }),
            'option_b': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option B'
            }),
            'option_c': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option C (optional for True/False)'
            }),
            'option_d': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option D (optional for True/False)'
            }),
            'correct_answer': forms.Select(attrs={'class': 'form-control'}),
            'marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            })
        }


# ==================== DISCUSSION FORMS ====================

class DiscussionThreadForm(forms.ModelForm):
    """Form for creating discussion threads"""
    
    class Meta:
        model = DiscussionThread
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Discussion title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your question or discussion...'
            })
        }


class DiscussionReplyForm(forms.ModelForm):
    """Form for replying to discussion threads"""
    
    class Meta:
        model = DiscussionReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your reply...'
            })
        }

