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


# Lecture/Material model - for course materials
class Lecture(models.Model):
    FILE_TYPE_CHOICES = (
        ('video', 'Video'),
        ('pdf', 'PDF Document'),
        ('doc', 'Word Document'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='lectures/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    order = models.PositiveIntegerField(default=0, help_text='Display order of the lecture')
    is_published = models.BooleanField(default=True, help_text='Whether students can view this lecture')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_lectures')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order', '-created_at']
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"
    
    def get_file_extension(self):
        """Get file extension from filename"""
        import os
        return os.path.splitext(self.file.name)[1].lower()
    
    def detect_file_type(self):
        """Auto-detect file type based on extension"""
        ext = self.get_file_extension()
        
        video_exts = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        pdf_exts = ['.pdf']
        doc_exts = ['.doc', '.docx', '.txt', '.rtf']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        audio_exts = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        
        if ext in video_exts:
            return 'video'
        elif ext in pdf_exts:
            return 'pdf'
        elif ext in doc_exts:
            return 'doc'
        elif ext in image_exts:
            return 'image'
        elif ext in audio_exts:
            return 'audio'
        else:
            return 'other'
    
    def save(self, *args, **kwargs):
        """Auto-detect file type on save if not set"""
        if not self.file_type or self.file_type == 'other':
            self.file_type = self.detect_file_type()
        super().save(*args, **kwargs)
    
    @property
    def file_size(self):
        """Get file size in human-readable format"""
        if self.file:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
        return "0 B"


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


# Attendance model - track student attendance
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances', limit_choices_to={'role': 'student'})
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'student', 'date']
        ordering = ['-date', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code} - {self.date} - {self.status}"


# Quiz model - create quizzes/tests
class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(help_text='Quiz duration in minutes')
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    passing_marks = models.DecimalField(max_digits=5, decimal_places=2, default=40)
    is_published = models.BooleanField(default=False, help_text='Whether students can take this quiz')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Quizzes'
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"
    
    @property
    def question_count(self):
        return self.questions.count()


# Question model - quiz questions
class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='mcq')
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['quiz', 'order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


# Quiz Attempt model - student attempts
class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', limit_choices_to={'role': 'student'})
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_passed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - {self.score}"
    
    @property
    def percentage(self):
        if self.quiz.total_marks > 0:
            return (self.score / self.quiz.total_marks) * 100
        return 0


# Quiz Answer model - student answers
class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    selected_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.student.username} - Q{self.question.order} - {self.selected_answer}"


# Lecture Progress model - track lecture completion
class LectureProgress(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='progress_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_progress', limit_choices_to={'role': 'student'})
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['lecture', 'student']
        ordering = ['-last_accessed']
    
    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.username} - {self.lecture.title} - {status}"


# Discussion Thread model - lecture discussions
class DiscussionThread(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='discussions')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_threads')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.lecture.title} - {self.title}"
    
    @property
    def reply_count(self):
        return self.replies.count()


# Discussion Reply model - replies to threads
class DiscussionReply(models.Model):
    thread = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Discussion Replies'
    
    def __str__(self):
        return f"Reply by {self.author.username} on {self.thread.title}"


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
