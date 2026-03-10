from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PreassignedEmail, Course, Enrollment, Transcript, MarksReport, ReportReply

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
