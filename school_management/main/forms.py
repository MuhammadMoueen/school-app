from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, PreassignedEmail, Course, Enrollment, Transcript, MarksReport, ReportReply, AuditLog, Lecture, Attendance, Quiz, Question, QuizAttempt, QuizAnswer, LectureProgress, DiscussionThread, DiscussionReply, TeacherActivityResponse, Assignment, AssignmentSubmission
from django.utils import timezone
import csv
import io
import random
import re

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True



class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return single_file_clean(data, initial)


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
        fields = ['name', 'code', 'description', 'student_class', 'section']
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
            }),
            'student_class': forms.Select(attrs={
                'class': 'form-control'
            }),
            'section': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'name': 'Subject Name',
            'code': 'Subject Code',
            'description': 'Description',
            'student_class': 'Class',
            'section': 'Section'
        }


class EnrollmentForm(forms.Form):
    """Form to enroll one or more students in a subject"""
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': 8,
        }),
        label='Select Students'
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Subject'
    )

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher

        if teacher is not None:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher).order_by('code', 'name')
            self.fields['course'].label_from_instance = (
                lambda course: f"{course.code} - {course.name} - {course.student_class}{course.section}"
            )

        selected_course_id = self.data.get('course') or self.initial.get('course')
        if teacher is not None and selected_course_id:
            try:
                course = self.fields['course'].queryset.get(pk=selected_course_id)
                self.fields['students'].queryset = User.objects.filter(
                    role='student',
                    student_class=course.student_class,
                    section=course.section,
                ).order_by('first_name', 'last_name', 'username')
            except (Course.DoesNotExist, ValueError, TypeError):
                self.fields['students'].queryset = User.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        students = cleaned_data.get('students')

        if not course or not students:
            return cleaned_data

        invalid_students = [
            student.get_full_name() or student.username
            for student in students
            if student.student_class != course.student_class or student.section != course.section
        ]
        if invalid_students:
            raise forms.ValidationError(
                'Selected students must belong to the same class and section as the chosen subject.'
            )

        return cleaned_data

    def save(self):
        course = self.cleaned_data['course']
        students = self.cleaned_data['students']
        created_enrollments = []
        skipped_students = []

        for student in students:
            enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)
            if created:
                created_enrollments.append(enrollment)
            else:
                skipped_students.append(student)

        return created_enrollments, skipped_students


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


class TeacherActivityResponseForm(forms.ModelForm):
    """Form used by admin to message or question a teacher activity"""
    class Meta:
        model = TeacherActivityResponse
        fields = ['response_type', 'message']
        widgets = {
            'response_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Write your message or question to the teacher...',
                'class': 'form-control',
                'rows': 4
            })
        }


# Forms for Admin/Coordinator Operations

class AdminCreateStudentForm(forms.ModelForm):
    """Form for admin to create student account directly - no signup needed"""
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter student full name (e.g., Ali Khan)',
            'class': 'form-control'
        }),
        label='Student Full Name',
        help_text='First and last name'
    )
    
    student_class = forms.ChoiceField(
        required=True,
        choices=[('', '-- Select Class --')] + [
            ('Prep', 'Prep'),
            ('1', 'Class 1'),
            ('2', 'Class 2'),
            ('3', 'Class 3'),
            ('4', 'Class 4'),
            ('5', 'Class 5'),
            ('6', 'Class 6'),
            ('7', 'Class 7'),
            ('8', 'Class 8'),
            ('9', 'Class 9'),
            ('10', 'Class 10'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Class'
    )
    
    section = forms.ChoiceField(
        required=False,
        choices=[('', '-- Select Section (Optional for Prep) --'), ('A', 'A'), ('B', 'B'), ('C', 'C')],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Section'
    )
    
    class Meta:
        model = User
        fields = []
    
    def clean(self):
        cleaned_data = super().clean()
        student_class = cleaned_data.get('student_class')
        section = cleaned_data.get('section')
        
        # Prep class does not require section
        if student_class and student_class != 'Prep' and not section:
            raise forms.ValidationError('Section is required for Class 1-10.')
        
        return cleaned_data
    
    def save(self, commit=True):
        full_name = self.cleaned_data.get('full_name').strip()
        student_class = self.cleaned_data.get('student_class')
        section = self.cleaned_data.get('section', '')
        
        # Parse name: get first name and last name
        name_parts = full_name.split()
        if len(name_parts) < 2:
            # If only one name, use it as both first and last
            first_name = name_parts[0]
            last_name = name_parts[0]
        else:
            first_name = name_parts[0]
            last_name = name_parts[-1]
        
        # New format: <firstname><5 random digits>@student.edu.pk
        # Example: Ali Khan -> ali32635@student.edu.pk
        first_name_clean = re.sub(r'[^a-zA-Z]', '', first_name).lower() or 'student'

        while True:
            random_code = random.randint(10000, 99999)
            email_base = f"{first_name_clean}{random_code}"
            email = f"{email_base}@student.edu.pk"

            if not User.objects.filter(email=email).exists() and not User.objects.filter(username=email_base).exists():
                username = email_base
                break
        
        # Create user instance directly
        user = User()
        user.username = username
        user.email = email
        user.role = 'student'
        user.status = 'active'
        user.student_class = student_class
        user.section = section if section else ''
        user.is_active = True
        
        # Set default password: Student@123
        user.set_password('Student@123')
        
        # Set full name
        user.first_name = first_name
        user.last_name = last_name
        
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
        help_text='Email will be auto-generated from name (e.g., M Moueen -> mmoueen73@teacher.edu.pk)'
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
            first_letter = re.sub(r'[^a-zA-Z]', '', name_parts[0][:1]).lower() or 't'
            last_name = re.sub(r'[^a-zA-Z]', '', name_parts[0]).lower() or 'teacher'
        else:
            first_letter = re.sub(r'[^a-zA-Z]', '', name_parts[0][:1]).lower() or 't'
            last_name = re.sub(r'[^a-zA-Z]', '', name_parts[-1]).lower() or 'teacher'

        # New format: <first letter><lastname><2 random digits>@teacher.edu.pk
        # Example: M Moueen -> mmoueen73@teacher.edu.pk
        while True:
            random_code = random.randint(10, 99)
            email_base = f"{first_letter}{last_name}{random_code}"
            email = f"{email_base}@teacher.edu.pk"

            if not User.objects.filter(email=email).exists() and not User.objects.filter(username=email_base).exists():
                username = email_base
                break
        
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
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': '.mp4,.mp3,.pdf,.docx,.ppt,.pptx,.png,.jpg,.jpeg'
        }),
        help_text='Optional: upload multiple attachments (video, notes, slides, assignments).'
    )
    
    class Meta:
        model = Lecture
        fields = [
            'course',
            'title',
            'description',
            'file_type',
            'file',
            'external_link',
            'visibility_status',
            'lecture_date',
            'scheduled_publish_at',
            'order',
        ]
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
            'file_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.mp4,.mp3,.pdf,.docx,.ppt,.pptx,.png,.jpg,.jpeg'
            }),
            'external_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/lecture123'
            }),
            'visibility_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lecture_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'scheduled_publish_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'order': forms.NumberInput(attrs={
                'placeholder': 'Display Order (e.g., 1, 2, 3...)',
                'class': 'form-control',
                'min': 0
            })
        }
    
    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter courses to only show courses taught by this teacher
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)
            self.fields['course'].label_from_instance = (
                lambda c: f"{c.code} - {c.name} (Class {c.student_class}{c.section})"
            )
        # Set order field default value
        self.fields['order'].initial = 0
        self.fields['lecture_date'].initial = timezone.localdate()
        self.fields['visibility_status'].initial = 'publish_now'
        self.fields['scheduled_publish_at'].required = False
    
    def clean_file(self):
        """Validate uploaded file size and type"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (50MB max for videos, 10MB for others)
            max_size = 50 * 1024 * 1024  # 50MB in bytes
            
            # Get file extension
            file_extension = file.name.lower().split('.')[-1]
            
            # Allowed extensions
            video_exts = ['mp4']
            audio_exts = ['mp3']
            doc_exts = ['pdf', 'docx', 'ppt', 'pptx']
            image_exts = ['jpg', 'jpeg', 'png']
            
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

    def clean(self):
        cleaned_data = super().clean()
        lecture_type = cleaned_data.get('file_type')
        file = cleaned_data.get('file')
        external_link = cleaned_data.get('external_link')
        visibility = cleaned_data.get('visibility_status')
        scheduled_publish_at = cleaned_data.get('scheduled_publish_at')

        if lecture_type == 'link' and not external_link:
            self.add_error('external_link', 'External link is required when lecture type is External Link.')

        if lecture_type != 'link' and not file and not self.instance.pk:
            self.add_error('file', 'Upload a lecture file for this lecture type.')

        if visibility == 'schedule_later' and not scheduled_publish_at:
            self.add_error('scheduled_publish_at', 'Scheduled publish date/time is required for Schedule Later.')

        return cleaned_data


class AssignmentForm(forms.ModelForm):
    """Teacher assignment create/edit form."""
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': '.pdf,.docx,.ppt,.pptx,.png,.jpg,.jpeg'
        }),
        help_text='Optional: upload multiple assignment resources.'
    )

    class Meta:
        model = Assignment
        fields = [
            'course',
            'title',
            'instructions',
            'deadline',
            'status',
            'allow_resubmission',
            'max_attempts',
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assignment title'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Assignment instructions'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'allow_resubmission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher).order_by('code', 'name')
            self.fields['course'].label_from_instance = (
                lambda c: f"{c.code} - {c.name} (Class {c.student_class}{c.section})"
            )

        if self.instance.pk and self.instance.deadline:
            self.initial['deadline'] = self.instance.deadline.strftime('%Y-%m-%dT%H:%M')

        self.fields['status'].initial = self.fields['status'].initial or 'draft'

    def clean_attachments(self):
        files = self.files.getlist('attachments')
        allowed_exts = {'pdf', 'docx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg'}
        max_size = 15 * 1024 * 1024
        for file_obj in files:
            ext = file_obj.name.lower().split('.')[-1]
            if ext not in allowed_exts:
                raise ValidationError('Only PDF, DOCX, PPT/PPTX, PNG, JPG, and JPEG files are allowed.')
            if file_obj.size > max_size:
                raise ValidationError('Each attachment must be less than 15MB.')
        return files

    def clean(self):
        cleaned_data = super().clean()
        allow_resubmission = cleaned_data.get('allow_resubmission')
        max_attempts = cleaned_data.get('max_attempts')
        deadline = cleaned_data.get('deadline')

        if not allow_resubmission:
            cleaned_data['max_attempts'] = 1
        elif max_attempts is not None and max_attempts < 2:
            self.add_error('max_attempts', 'Set attempts to at least 2 when resubmission is enabled.')

        if deadline and deadline.year < 2000:
            self.add_error('deadline', 'Please provide a valid deadline date/time.')

        return cleaned_data


class AssignmentSubmissionForm(forms.ModelForm):
    """Student assignment submission form."""
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_file', 'comment']
        widgets = {
            'submission_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.png,.jpg,.jpeg,.zip'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional message to your teacher'
            })
        }

    def clean_submission_file(self):
        file_obj = self.cleaned_data.get('submission_file')
        if not file_obj:
            return file_obj

        allowed_exts = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'zip'}
        ext = file_obj.name.lower().split('.')[-1]
        if ext not in allowed_exts:
            raise ValidationError('Only PDF, DOC/DOCX, PNG/JPG/JPEG, and ZIP files are supported.')

        if file_obj.size > 30 * 1024 * 1024:
            raise ValidationError('Submission file must be less than 30MB.')

        return file_obj


class AssignmentGradingForm(forms.ModelForm):
    """Teacher grading form for assignment submissions."""
    class Meta:
        model = AssignmentSubmission
        fields = ['score', 'feedback']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0,
                'placeholder': 'Score (e.g., 8 or 8.5)'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Feedback for student'
            })
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
        fields = [
            'course',
            'quiz_type',
            'question_source',
            'title',
            'description',
            'duration_minutes',
            'start_time',
            'end_time',
            'allow_late_submission',
            'question_display_mode',
            'auto_submit_on_timeout',
            'total_marks_mode',
            'total_marks',
            'passing_marks',
            'paper_file',
            'omr_source_file',
            'answer_key_text',
            'answer_key_file',
            'is_published',
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'quiz_type': forms.Select(attrs={'class': 'form-control'}),
            'question_source': forms.Select(attrs={'class': 'form-control'}),
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
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
            'allow_late_submission': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'question_display_mode': forms.Select(attrs={'class': 'form-control'}),
            'auto_submit_on_timeout': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'total_marks_mode': forms.Select(attrs={'class': 'form-control'}),
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
            'paper_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.png,.jpg,.jpeg,.docx,.xlsx'
            }),
            'omr_source_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.png,.jpg,.jpeg,.docx'
            }),
            'answer_key_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Q1: A\nQ2: C\nQ3: B'
            }),
            'answer_key_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.txt,.csv,.docx'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)

        # Accept multiple datetime formats for flexibility
        datetime_formats = [
            '%Y-%m-%dT%H:%M',           # ISO format from datetime-local input
            '%Y-%m-%d %H:%M',           # Standard format
            '%d/%m/%Y %H:%M',           # DD/MM/YYYY HH:MM
            '%d/%m/%Y %H:%M %p',        # DD/MM/YYYY HH:MM AM/PM
            '%Y-%m-%d %H:%M:%S',        # With seconds
            '%d/%m/%Y %H:%M:%S',        # DD/MM/YYYY with seconds
        ]
        self.fields['start_time'].input_formats = datetime_formats
        self.fields['end_time'].input_formats = datetime_formats

    def clean(self):
        cleaned_data = super().clean()
        quiz_type = cleaned_data.get('quiz_type')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        duration_minutes = cleaned_data.get('duration_minutes')
        total_marks_mode = cleaned_data.get('total_marks_mode')
        total_marks = cleaned_data.get('total_marks')
        passing_marks = cleaned_data.get('passing_marks')
        allow_late_submission = cleaned_data.get('allow_late_submission')
        auto_submit_on_timeout = cleaned_data.get('auto_submit_on_timeout')
        omr_file = cleaned_data.get('omr_source_file')

        # Only validate times if both are provided
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError('End time must be later than start time.')

        if duration_minutes and duration_minutes < 1:
            self.add_error('duration_minutes', 'Duration must be at least 1 minute.')

        if allow_late_submission and auto_submit_on_timeout:
            self.add_error('auto_submit_on_timeout', 'Auto-submit and late submission cannot both be enabled at the same time.')

        # Only validate marks comparison if BOTH are provided
        if total_marks_mode == 'manual' and total_marks is not None and passing_marks is not None:
            if passing_marks > total_marks:
                self.add_error('passing_marks', 'Passing marks cannot be greater than total marks.')

        if quiz_type == 'manual':
            cleaned_data['question_source'] = 'manual'
            cleaned_data['answer_key_text'] = ''

        if quiz_type == 'mixed':
            cleaned_data['question_source'] = 'manual'
            cleaned_data['answer_key_text'] = ''

        if quiz_type == 'auto':
            cleaned_data['question_source'] = 'omr_upload' if omr_file else 'manual'

        if quiz_type == 'auto' and cleaned_data.get('question_source') == 'omr_upload':
            if not omr_file and not self.instance.pk:
                self.add_error('omr_source_file', 'Upload an OMR/MCQ source file for OMR mode.')

            if omr_file:
                filename = (omr_file.name or '').lower()
                if not filename.endswith(('.pdf', '.png', '.jpg', '.jpeg', '.docx')):
                    self.add_error('omr_source_file', 'Supported formats: PDF, JPG, PNG, DOCX.')

        return cleaned_data


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

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        option_a = (cleaned_data.get('option_a') or '').strip()
        option_b = (cleaned_data.get('option_b') or '').strip()
        correct_answer = (cleaned_data.get('correct_answer') or '').strip()

        if question_type in {'mcq', 'omr', 'true_false'}:
            if not option_a or not option_b:
                raise forms.ValidationError('Option A and Option B are required for objective questions.')
            if not correct_answer:
                raise forms.ValidationError('Correct answer is required for objective questions.')

        if question_type == 'subjective':
            cleaned_data['correct_answer'] = ''
            cleaned_data['option_a'] = ''
            cleaned_data['option_b'] = ''
            cleaned_data['option_c'] = ''
            cleaned_data['option_d'] = ''

        cleaned_data['options'] = [
            cleaned_data.get('option_a') or '',
            cleaned_data.get('option_b') or '',
            cleaned_data.get('option_c') or '',
            cleaned_data.get('option_d') or '',
        ]

        return cleaned_data

    def save(self, commit=True):
        question = super().save(commit=False)
        question.options = [
            self.cleaned_data.get('option_a') or '',
            self.cleaned_data.get('option_b') or '',
            self.cleaned_data.get('option_c') or '',
            self.cleaned_data.get('option_d') or '',
        ]
        if commit:
            question.save()
        return question


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

