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
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('alumni', 'Alumni'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text='User status (for students and record keeping)')
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
    CLASS_CHOICES = (
        ('Prep', 'Prep'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
    )
    
    SECTION_CHOICES = (
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    )
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_teaching', limit_choices_to={'role': 'teacher'})
    student_class = models.CharField(max_length=10, choices=CLASS_CHOICES, default='1', help_text='Class/Grade level')
    section = models.CharField(max_length=10, choices=SECTION_CHOICES, default='A', help_text='Section')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name} (Class {self.student_class}-{self.section})"


# Lecture/Material model - for course materials
class Lecture(models.Model):
    FILE_TYPE_CHOICES = (
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'PDF / Document'),
        ('image', 'Image'),
        ('link', 'External Link'),
    )

    VISIBILITY_CHOICES = (
        ('publish_now', 'Publish Now'),
        ('schedule_later', 'Schedule Later'),
        ('draft', 'Draft'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='lectures/%Y/%m/', blank=True, null=True)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='document')
    external_link = models.URLField(blank=True)
    visibility_status = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='publish_now')
    lecture_date = models.DateField(default=timezone.localdate)
    scheduled_publish_at = models.DateTimeField(blank=True, null=True)
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
        if not self.file:
            return self.file_type

        ext = self.get_file_extension()
        
        video_exts = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        pdf_exts = ['.pdf']
        doc_exts = ['.doc', '.docx', '.txt', '.rtf', '.ppt', '.pptx']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        audio_exts = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        
        if ext in video_exts:
            return 'video'
        elif ext in pdf_exts or ext in doc_exts:
            return 'document'
        elif ext in image_exts:
            return 'image'
        elif ext in audio_exts:
            return 'audio'
        else:
            return 'document'
    
    def save(self, *args, **kwargs):
        """Auto-detect file type on save if not set"""
        if self.file and self.file_type != 'link':
            self.file_type = self.detect_file_type()

        if self.visibility_status == 'publish_now':
            self.is_published = True
            self.scheduled_publish_at = None
        elif self.visibility_status == 'draft':
            self.is_published = False
            self.scheduled_publish_at = None
        else:
            if self.scheduled_publish_at and self.scheduled_publish_at <= timezone.now():
                self.is_published = True
            else:
                self.is_published = False

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


class LectureAttachment(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='lecture_attachments/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.file.name


class LectureView(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='views')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_views', limit_choices_to={'role': 'student'})
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['lecture', 'student']
        ordering = ['-viewed_at']


class LectureDownload(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='downloads')
    attachment = models.ForeignKey(LectureAttachment, on_delete=models.SET_NULL, null=True, blank=True, related_name='downloads')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_downloads', limit_choices_to={'role': 'student'})
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['lecture', 'attachment', 'student']


class LectureNotification(models.Model):
    TYPE_CHOICES = (
        ('student_comment', 'Student Comment'),
        ('teacher_reply', 'Teacher Reply'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_notifications')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lecture_notifications_sent')
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='notifications')
    thread = models.ForeignKey('DiscussionThread', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    reply = models.ForeignKey('DiscussionReply', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Assignment(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    allow_resubmission = models.BooleanField(default=False)
    max_attempts = models.PositiveIntegerField(default=1)
    student_class = models.CharField(max_length=20, blank=True)
    section = models.CharField(max_length=10, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.code} - {self.title}"

    @property
    def is_deadline_passed(self):
        return timezone.now() > self.deadline

    @property
    def is_closed(self):
        return self.status == 'closed'

    def save(self, *args, **kwargs):
        if self.course_id:
            self.student_class = self.course.student_class
            self.section = self.course.section
        if self.max_attempts < 1:
            self.max_attempts = 1
        if not self.allow_resubmission:
            self.max_attempts = 1
        super().save(*args, **kwargs)


class AssignmentAttachment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='assignment_attachments/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.file.name


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions', limit_choices_to={'role': 'student'})
    attempt_number = models.PositiveIntegerField(default=1)
    submission_file = models.FileField(upload_to='assignment_submissions/%Y/%m/')
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    late_duration = models.DurationField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_assignment_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['assignment', 'student', 'attempt_number']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title} (Attempt {self.attempt_number})"

    @property
    def late_by_text(self):
        if not self.is_late or not self.late_duration:
            return ''

        total_seconds = int(self.late_duration.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            return f"Late by {days} day{'s' if days != 1 else ''}"
        if hours > 0:
            return f"Late by {hours} hour{'s' if hours != 1 else ''}"
        return f"Late by {max(minutes, 1)} minute{'s' if minutes != 1 else ''}"


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
        ('leave', 'Leave'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances', limit_choices_to={'role': 'student'})
    date = models.DateField()
    student_class = models.CharField(max_length=20, blank=True)
    section = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'student', 'date']
        ordering = ['-date', 'student']
    
    def save(self, *args, **kwargs):
        if self.course_id:
            self.student_class = self.course.student_class
            self.section = self.course.section
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.username} - {self.course.code} - {self.date} - {self.status}"


# Quiz model - create quizzes/tests
class Quiz(models.Model):
    QUIZ_TYPE_CHOICES = (
        ('auto', 'Auto-Graded (MCQs / OMR)'),
        ('manual', 'Manual (Subjective)'),
    )

    QUESTION_SOURCE_CHOICES = (
        ('manual', 'Manual MCQ Entry'),
        ('omr_upload', 'Upload MCQ File (OMR Style)'),
    )

    QUESTION_DISPLAY_CHOICES = (
        ('full', 'Show Full Quiz'),
        ('one_by_one', 'Show One by One'),
    )

    TOTAL_MARKS_MODE_CHOICES = (
        ('manual', 'Manual'),
        ('auto', 'Auto from Questions'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPE_CHOICES, default='auto')
    question_source = models.CharField(max_length=20, choices=QUESTION_SOURCE_CHOICES, default='manual')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(help_text='Quiz duration in minutes')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    auto_submit_on_timeout = models.BooleanField(default=True)
    question_display_mode = models.CharField(max_length=20, choices=QUESTION_DISPLAY_CHOICES, default='full')
    total_marks_mode = models.CharField(max_length=20, choices=TOTAL_MARKS_MODE_CHOICES, default='manual')
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    passing_marks = models.DecimalField(max_digits=5, decimal_places=2, default=40)
    omr_source_file = models.FileField(upload_to='quiz_sources/%Y/%m/', blank=True, null=True)
    answer_key_text = models.TextField(blank=True)
    answer_key_file = models.FileField(upload_to='quiz_answer_keys/%Y/%m/', blank=True, null=True)
    answer_key_map = models.JSONField(default=dict, blank=True)
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

    @property
    def computed_total_marks(self):
        aggregate_total = self.questions.aggregate(total=models.Sum('marks')).get('total')
        return aggregate_total or 0

    def sync_total_marks_from_questions(self):
        if self.total_marks_mode != 'auto':
            return
        self.total_marks = self.computed_total_marks
        self.save(update_fields=['total_marks', 'updated_at'])


# Question model - quiz questions
class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('mcq', 'Multiple Choice'),
        ('omr', 'OMR MCQ'),
        ('true_false', 'True/False'),
        ('subjective', 'Subjective'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='mcq')
    options = models.JSONField(default=list, blank=True)
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], blank=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['quiz', 'order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"

    def save(self, *args, **kwargs):
        if self.options:
            normalized_options = [str(item).strip() for item in self.options][:4]
            while len(normalized_options) < 4:
                normalized_options.append('')
            self.option_a, self.option_b, self.option_c, self.option_d = normalized_options[:4]
        elif any([self.option_a, self.option_b, self.option_c, self.option_d]):
            self.options = [self.option_a, self.option_b, self.option_c, self.option_d]

        if self.question_type == 'subjective':
            self.correct_answer = ''
            self.options = []
            self.option_a = ''
            self.option_b = ''
            self.option_c = ''
            self.option_d = ''

        super().save(*args, **kwargs)


# Quiz Attempt model - student attempts
class QuizAttempt(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('pending_check', 'Pending Check'),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', limit_choices_to={'role': 'student'})
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    answers_json = models.JSONField(default=dict, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
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
    selected_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], blank=True)
    answer_text = models.TextField(blank=True)
    answer_file = models.FileField(upload_to='quiz_answers/%Y/%m/', blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    manual_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_manually_checked = models.BooleanField(default=False)
    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_quiz_answers',
        limit_choices_to={'role': 'teacher'},
    )
    checked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.student.username} - Q{self.question.order} - {self.selected_answer}"


class QuizResult(models.Model):
    RESULT_STATUS_CHOICES = (
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('pending', 'Pending Check'),
    )

    attempt = models.OneToOneField(QuizAttempt, on_delete=models.CASCADE, related_name='result')
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    result_status = models.CharField(max_length=20, choices=RESULT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Result - Attempt {self.attempt_id} ({self.result_status})"


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


class TranscriptQuizMark(models.Model):
    """Per-quiz marks linked to a student's course transcript context."""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_marks')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='transcript_marks')
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='transcript_mark')
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    attempt_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment', 'quiz']
        ordering = ['-attempt_date']

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.quiz.title}: {self.obtained_marks}/{self.total_marks}"


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
    is_seen_by_target = models.BooleanField(default=False)
    seen_by_target_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.admin.username} - {self.get_action_display()} at {self.created_at}"


class TeacherActivityLog(models.Model):
    ACTION_CHOICES = (
        ('create_course', 'Created Course'),
        ('edit_course', 'Edited Course'),
        ('enroll_students', 'Enrolled Students'),
        ('upload_lecture', 'Uploaded Lecture'),
        ('create_assessment', 'Created Quiz/Test'),
        ('upload_transcript', 'Uploaded Transcript/Grade'),
        ('update_grades', 'Updated Student Grades'),
        ('post_report', 'Posted Report/Reply'),
        ('mark_attendance', 'Marked Attendance'),
        ('other', 'Other Academic Action'),
    )

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_activity_logs')
    teacher_name = models.CharField(max_length=255)
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_activity_logs')
    student_class = models.CharField(max_length=20, blank=True)
    section = models.CharField(max_length=10, blank=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.teacher_name} - {self.get_action_type_display()}"


class TeacherActivityNotification(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_activity_notifications')
    activity = models.ForeignKey(TeacherActivityLog, on_delete=models.CASCADE, related_name='notifications')
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['admin', 'activity']

    def __str__(self):
        return f"Notification for {self.admin.username}: {self.activity.teacher_name}"


class TeacherActivityResponse(models.Model):
    RESPONSE_CHOICES = (
        ('message', 'Message to Teacher'),
        ('report_question', 'Report/Question Activity'),
    )

    notification = models.ForeignKey(TeacherActivityNotification, on_delete=models.CASCADE, related_name='responses')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_activity_responses')
    response_type = models.CharField(max_length=30, choices=RESPONSE_CHOICES)
    message = models.TextField()
    is_read_by_teacher = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin.username} - {self.get_response_type_display()}"
