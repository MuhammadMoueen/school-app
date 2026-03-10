from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PreassignedEmail, Course, Enrollment, Transcript, MarksReport, ReportReply, Lecture, Attendance, Quiz, Question, QuizAttempt, QuizAnswer, LectureProgress, DiscussionThread, DiscussionReply

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'address')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'address')}),
    )


@admin.register(PreassignedEmail)
class PreassignedEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'assigned_by', 'is_used', 'created_at', 'used_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email', 'full_name', 'assigned_by__username']
    readonly_fields = ['is_used', 'used_at', 'created_at']
    
    def get_readonly_fields(self, request, obj=None):
        # Make assigned_by readonly after creation
        if obj:  # Editing an existing object
            return self.readonly_fields + ['assigned_by', 'email']
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        # Automatically set assigned_by to current user if not set
        if not obj.pk and not obj.assigned_by_id:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'teacher', 'created_at']
    list_filter = ['teacher', 'created_at']
    search_fields = ['name', 'code', 'teacher__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrolled_at']
    list_filter = ['course', 'enrolled_at']
    search_fields = ['student__username', 'course__name']
    readonly_fields = ['enrolled_at']


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'get_course', 'marks_obtained', 'total_marks', 'grade', 'updated_at']
    list_filter = ['grade', 'updated_at']
    search_fields = ['enrollment__student__username', 'enrollment__course__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_student(self, obj):
        return obj.enrollment.student.username
    get_student.short_description = 'Student'
    
    def get_course(self, obj):
        return obj.enrollment.course.name
    get_course.short_description = 'Course'


@admin.register(MarksReport)
class MarksReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher', 'get_course', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__username', 'teacher__username', 'message']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_course(self, obj):
        return obj.transcript.enrollment.course.name
    get_course.short_description = 'Course'


@admin.register(ReportReply)
class ReportReplyAdmin(admin.ModelAdmin):
    list_display = ['report', 'sender', 'created_at']
    list_filter = ['created_at']
    search_fields = ['sender__username', 'message']
    readonly_fields = ['created_at']


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'file_type', 'is_published', 'order', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'is_published', 'course', 'created_at']
    search_fields = ['title', 'description', 'course__name', 'course__code']
    readonly_fields = ['created_at', 'updated_at', 'file_size']
    list_editable = ['is_published', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description')
        }),
        ('File Details', {
            'fields': ('file', 'file_type', 'file_size')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_published')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Automatically set uploaded_by to current user if not set
        if not obj.pk and not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'date', 'status', 'marked_by', 'created_at']
    list_filter = ['status', 'course', 'date', 'created_at']
    search_fields = ['student__username', 'course__name', 'remarks']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    date_hierarchy = 'date'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'question_count', 'total_marks', 'passing_marks', 'duration_minutes', 'is_published', 'created_at']
    list_filter = ['is_published', 'course', 'created_at']
    search_fields = ['title', 'description', 'course__name']
    readonly_fields = ['created_at', 'updated_at', 'question_count']
    list_editable = ['is_published']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'question_text_short', 'question_type', 'correct_answer', 'marks']
    list_filter = ['question_type', 'quiz']
    search_fields = ['question_text', 'quiz__title']
    list_editable = ['order']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'percentage', 'is_passed', 'is_completed', 'started_at', 'submitted_at']
    list_filter = ['is_passed', 'is_completed', 'quiz', 'started_at']
    search_fields = ['student__username', 'quiz__title']
    readonly_fields = ['started_at', 'percentage']


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_answer', 'is_correct']
    list_filter = ['is_correct', 'attempt__quiz']
    search_fields = ['attempt__student__username', 'question__question_text']


@admin.register(LectureProgress)
class LectureProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lecture', 'is_completed', 'completed_at', 'last_accessed']
    list_filter = ['is_completed', 'lecture__course', 'completed_at']
    search_fields = ['student__username', 'lecture__title']
    readonly_fields = ['last_accessed']


@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'lecture', 'author', 'reply_count', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'lecture__course', 'created_at']
    search_fields = ['title', 'content', 'author__username', 'lecture__title']
    readonly_fields = ['created_at', 'updated_at', 'reply_count']
    list_editable = ['is_resolved']


@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ['thread', 'author', 'created_at']
    list_filter = ['created_at', 'thread__lecture__course']
    search_fields = ['content', 'author__username', 'thread__title']
    readonly_fields = ['created_at', 'updated_at']


