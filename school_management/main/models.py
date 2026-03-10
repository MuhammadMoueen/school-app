from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Custom User model with role-based authentication
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin/Coordinator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, help_text='Department (for teachers)')
    student_class = models.CharField(max_length=50, blank=True, help_text='Class (for students, e.g., Grade 10)')
    section = models.CharField(max_length=10, blank=True, help_text='Section (for students, e.g., A, B)')
    roll_number = models.CharField(max_length=20, blank=True, help_text='Roll Number (for students)')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# Model for pre-assigned student emails
class PreassignedEmail(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, blank=True)  # Store student name for reference
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_emails')
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        status = "Used" if self.is_used else "Available"
        return f"{self.email} - {status}"
    
    def generate_username(self):
        """Generate username from email"""
        return self.email.split('@')[0].lower()

# Keep old model name for backward compatibility during migration
PreassignedUsername = PreassignedEmail


# Course model
class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_teaching', limit_choices_to={'role': 'teacher'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# Enrollment model - links students to courses
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments', limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.name}"


# Transcript model - stores student marks/grades
class Transcript(models.Model):
    GRADE_CHOICES = (
        ('A', 'A (85-100)'),
        ('B', 'B (70-84)'),
        ('C', 'C (55-69)'),
        ('D', 'D (40-54)'),
        ('F', 'F (Below 40)'),
    )
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='transcript')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.enrollment.course.name}: {self.marks_obtained}/{self.total_marks}"
    
    @staticmethod
    def calculate_grade(marks_obtained, total_marks):
        """Calculate grade based on percentage using new grading criteria"""
        if total_marks <= 0:
            return 'F'
        
        percentage = (float(marks_obtained) / float(total_marks)) * 100
        
        # New grading scale: 85-100=A, 70-84=B, 55-69=C, 40-54=D, <40=F
        if percentage >= 85:
            return 'A'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 55:
            return 'C'
        elif percentage >= 40:
            return 'D'
        else:
            return 'F'
    
    @property
    def percentage(self):
        if self.total_marks > 0:
            return (self.marks_obtained / self.total_marks) * 100
        return 0


# Marks Report model - for student-teacher communication about marks
class MarksReport(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('replied', 'Replied'),
        ('resolved', 'Resolved'),
    )
    
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name='reports')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marks_reports_sent')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marks_reports_received')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_read_by_teacher = models.BooleanField(default=False)  # Track if teacher has read the report
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report from {self.student.username} about {self.transcript.enrollment.course.name}"


# Report Reply model - teacher replies to student reports
class ReportReply(models.Model):
    report = models.ForeignKey(MarksReport, on_delete=models.CASCADE, related_name='replies')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_replies')
    message = models.TextField()
    is_read_by_student = models.BooleanField(default=False)  # Track if student has read the reply
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply by {self.sender.username} on report #{self.report.id}"


# Audit Log model - track admin activities
class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create_student', 'Created Student'),
        ('edit_student', 'Edited Student'),
        ('delete_student', 'Deleted Student'),
        ('create_teacher', 'Created Teacher'),
        ('edit_teacher', 'Edited Teacher'),
        ('delete_teacher', 'Deleted Teacher'),
        ('create_course', 'Created Course'),
        ('edit_course', 'Edited Course'),
        ('delete_course', 'Deleted Course'),
        ('bulk_import', 'Bulk Import'),
        ('bulk_email', 'Bulk Email Generation'),
        ('export_data', 'Exported Data'),
        ('other', 'Other Action'),
    )
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs_as_target')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.admin.username} - {self.get_action_display()} at {self.created_at}"
