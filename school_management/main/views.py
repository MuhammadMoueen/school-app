from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q, Count, F
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from .forms import (TeacherSignupForm, StudentSignupForm, CustomLoginForm,
                   AssignEmailForm, CourseForm, EnrollmentForm, TranscriptForm,
                   MarksReportForm, ReportReplyForm, AdminCreateStudentForm, ProfileEditForm,
                   LectureForm)
from .models import User, PreassignedEmail, Course, Enrollment, Transcript, MarksReport, ReportReply, Lecture

def home(request):
    """Home page view"""
    return render(request, 'shared/home.html')

@login_required
def dashboard(request):
    """Dashboard view - redirects based on user role"""
    user = request.user
    
    if user.role == 'admin':
        return admin_dashboard(request)
    elif user.role == 'teacher':
        return teacher_dashboard(request)
    elif user.role == 'student':
        return student_dashboard(request)
    else:
        messages.warning(request, 'No role assigned. Please contact administrator.')
        logout(request)
        return redirect('main:home')

def signup_selection(request):
    """Signup is disabled - redirect to login"""
    messages.info(request, 'Public signup is disabled. Please contact the administrator to create your account.')
    return redirect('main:login')

def signup_teacher(request):
    """Signup is disabled - redirect to login"""
    messages.info(request, 'Teacher signup is disabled. Please contact the administrator to create your account.')
    return redirect('main:login')

def signup_student(request):
    """Signup is disabled - redirect to login"""
    messages.info(request, 'Student signup is disabled. Please contact the administrator to create your account.')
    return redirect('main:login')

def custom_login(request):
    """Custom login view with role-based redirect"""
    if request.user.is_authenticated:
        return redirect('main:dashboard')
    
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username_or_email or not password:
            messages.error(request, 'Please enter both username/email and password.')
            return render(request, 'shared/login.html', {'form': CustomLoginForm()})
        
        # Check if input is an email and convert to username
        username = username_or_email
        user_obj = None
        
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                messages.error(request, 'No account found with that email address.')
                return render(request, 'shared/login.html', {'form': CustomLoginForm()})
        else:
            try:
                user_obj = User.objects.get(username__iexact=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                messages.error(request, 'No account found with that username.')
                return render(request, 'shared/login.html', {'form': CustomLoginForm()})
        
        # Authenticate with username
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account is inactive. Please contact the administrator.')
                return render(request, 'shared/login.html', {'form': CustomLoginForm()})
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Role-based redirect
            if user.role in ['admin', 'teacher', 'student']:
                return redirect('main:dashboard')
            else:
                return redirect('main:home')
        else:
            messages.error(request, f'Incorrect password for {user_obj.email}. Please try again or contact admin.')
    
    form = CustomLoginForm()
    return render(request, 'shared/login.html', {'form': form})


def custom_logout(request):
    """Custom logout view that clears session and redirects to home"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('main:home')


# ==================== Admin/Coordinator Dashboard Views ====================

@login_required
def admin_dashboard(request):
    """Admin/Coordinator dashboard for managing students and viewing system overview"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin/Coordinator only.')
        return redirect('main:home')
    
    from .models import AuditLog
    
    # Get statistics
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_courses = Course.objects.all().count()
    total_enrollments = Enrollment.objects.all().count()
    
    # Get recent actions from audit log (last 5)
    recent_actions = AuditLog.objects.select_related('admin', 'target_user').order_by('-created_at')[:5]
    
    # Get all teachers
    teachers = User.objects.filter(role='teacher').order_by('first_name')
    
    context = {
        'admin': request.user,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'recent_actions': recent_actions,
        'teachers': teachers,
    }
    return render(request, 'admin/admin_dashboard.html', context)


@login_required
def admin_create_student(request):
    """Admin view to create student account directly"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin/Coordinator only.')
        return redirect('main:home')
    
    from .models import AuditLog
    
    if request.method == 'POST':
        form = AdminCreateStudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                admin=request.user,
                action='create_student',
                description=f'Created student account: {student.username} ({student.get_full_name()})',
                target_user=student,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(
                request,
                f'Student account created successfully! '
                f'Email: {student.email} | '
                f'Username: {student.username} | '
                f'Password: Student@123 '
                f'(Please share these credentials with the student. They can change password after first login.)'
            )
            return redirect('main:coordinator_manage_students')
    else:
        form = AdminCreateStudentForm()
    
    return render(request, 'admin/admin_create_student.html', {'form': form})


@login_required
def admin_manage_students(request):
    """Admin view to manage all students"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin/Coordinator only.')
        return redirect('main:home')
    
    # Get registered students
    students = User.objects.filter(role='student').order_by('first_name')
    
    # Get enrollment count for each student
    for student in students:
        student.enrollment_count = Enrollment.objects.filter(student=student).count()
    
    # Get pre-assigned emails that haven't been used yet
    preassigned_emails = PreassignedEmail.objects.filter(is_used=False).order_by('-created_at')
    
    context = {
        'students': students,
        'preassigned_emails': preassigned_emails,
    }
    return render(request, 'admin/admin_manage_students.html', context)


@login_required
def admin_delete_student(request, student_id):
    """Admin view to delete a student account"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin/Coordinator only.')
        return redirect('main:home')
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    if request.method == 'POST':
        username = student.username
        student.delete()
        messages.success(request, f'Student account "{username}" has been deleted.')
        return redirect('main:coordinator_manage_students')
    
    return render(request, 'admin/admin_confirm_delete.html', {'student': student})


@login_required
def admin_view_teachers(request):
    """Admin view to see all teachers"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin/Coordinator only.')
        return redirect('main:home')
    
    teachers = User.objects.filter(role='teacher').order_by('first_name')
    
    # Get course count for each teacher
    for teacher in teachers:
        teacher.course_count = Course.objects.filter(teacher=teacher).count()
        teacher.student_count = Enrollment.objects.filter(course__teacher=teacher).values('student').distinct().count()
    
    context = {
        'teachers': teachers,
    }
    return render(request, 'admin/admin_view_teachers.html', context)


# ==================== Profile Management Views ====================

@login_required
def edit_profile(request):
    """Edit user profile - for all authenticated users"""
    from .forms import ProfileEditForm
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('main:dashboard')
    else:
        form = ProfileEditForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'shared/edit_profile.html', context)


@login_required
def change_password(request):
    """Change password for authenticated users"""
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('main:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'shared/change_password.html', context)


# ==================== Teacher Dashboard Views ====================

@login_required
def teacher_dashboard(request):
    """Teacher dashboard with all management features"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    
    # Get teacher's data
    courses = Course.objects.filter(teacher=teacher)
    
    # Get unread reports count for notifications
    unread_reports = MarksReport.objects.filter(
        teacher=teacher,
        status='pending'
    ).count()
    
    # Get recent reports
    recent_reports = MarksReport.objects.filter(teacher=teacher).select_related(
        'student', 'transcript__enrollment__course'
    )[:5]
    
    # Statistics
    total_students = User.objects.filter(role='student', enrollments__course__teacher=teacher).distinct().count()
    total_enrollments = Enrollment.objects.filter(course__teacher=teacher).count()
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'unread_reports': unread_reports,
        'recent_reports': recent_reports,
        'total_students': total_students,
        'total_courses': courses.count(),
        'total_enrollments': total_enrollments,
    }
    
    return render(request, 'teacher/teacher_dashboard.html', context)


@login_required

# assign_username view removed - Student account creation is now handled by Admin/Coordinator only
# Teachers can no longer assign usernames. All student accounts must be created by admin.

@login_required
def manage_courses(request):
    """View and manage subjects"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    courses = Course.objects.filter(teacher=request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, f'Subject "{course.name}" created successfully!')
            return redirect('main:manage_courses')
    else:
        form = CourseForm()
    
    context = {
        'courses': courses,
        'form': form
    }
    return render(request, 'teacher/manage_courses.html', context)


@login_required
def edit_course(request, course_id):
    """Edit a subject"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject "{course.name}" updated successfully!')
            return redirect('main:manage_courses')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'teacher/edit_course.html', {'form': form, 'course': course})


@login_required
def delete_course(request, course_id):
    """Delete a subject"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    course_name = course.name
    course.delete()
    messages.success(request, f'Subject "{course_name}" deleted successfully!')
    return redirect('main:manage_courses')


# ==================== LECTURE MANAGEMENT VIEWS ====================

@login_required
def manage_lectures(request):
    """View and manage all lectures/materials"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    course_filter = request.GET.get('course', '')
    
    # Get all lectures for this teacher's courses
    lectures = Lecture.objects.filter(
        course__teacher=teacher
    ).select_related('course').order_by('course', 'order', '-created_at')
    
    # Filter by course if specified
    if course_filter:
        lectures = lectures.filter(course_id=course_filter)
    
    # Get teacher's courses for filter dropdown
    courses = Course.objects.filter(teacher=teacher)
    
    context = {
        'lectures': lectures,
        'courses': courses,
        'selected_course': course_filter,
    }
    
    return render(request, 'teacher/manage_lectures.html', context)


@login_required
def create_lecture(request):
    """Upload new lecture/material"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    
    if request.method == 'POST':
        form = LectureForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.uploaded_by = teacher
            lecture.save()
            messages.success(
                request, 
                f'Lecture "{lecture.title}" uploaded successfully for {lecture.course.name}!'
            )
            return redirect('main:manage_lectures')
    else:
        form = LectureForm(teacher=teacher)
    
    context = {
        'form': form,
    }
    
    return render(request, 'teacher/create_lecture.html', context)


@login_required
def edit_lecture(request, lecture_id):
    """Edit an existing lecture"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    lecture = get_object_or_404(
        Lecture, 
        id=lecture_id, 
        course__teacher=teacher
    )
    
    if request.method == 'POST':
        form = LectureForm(request.POST, request.FILES, instance=lecture, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lecture "{lecture.title}" updated successfully!')
            return redirect('main:manage_lectures')
    else:
        form = LectureForm(instance=lecture, teacher=teacher)
    
    context = {
        'form': form,
        'lecture': lecture,
    }
    
    return render(request, 'teacher/edit_lecture.html', context)


@login_required
def delete_lecture(request, lecture_id):
    """Delete a lecture"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    lecture = get_object_or_404(
        Lecture,
        id=lecture_id,
        course__teacher=teacher
    )
    
    lecture_title = lecture.title
    course_name = lecture.course.name
    
    # Delete the file from storage
    if lecture.file:
        lecture.file.delete()
    
    lecture.delete()
    
    messages.success(
        request,
        f'Lecture "{lecture_title}" from {course_name} deleted successfully!'
    )
    
    return redirect('main:manage_lectures')


@login_required
def view_course_lectures(request, course_id):
    """View all lectures for a specific course"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    lectures = Lecture.objects.filter(course=course).order_by('order', '-created_at')
    
    context = {
        'course': course,
        'lectures': lectures,
    }
    
    return render(request, 'teacher/course_lectures.html', context)


@login_required
def manage_enrollments(request):
    """Enroll students in subjects"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    enrollments = Enrollment.objects.filter(course__teacher=request.user).select_related(
        'student', 'course'
    )
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        # Filter subjects to only show teacher's subjects
        form.fields['course'].queryset = Course.objects.filter(teacher=request.user)
        
        if form.is_valid():
            enrollment = form.save()
            messages.success(request, f'{enrollment.student.get_full_name()} enrolled in {enrollment.course.name}!')
            return redirect('main:manage_enrollments')
    else:
        form = EnrollmentForm()
        form.fields['course'].queryset = Course.objects.filter(teacher=request.user)
    
    context = {
        'enrollments': enrollments,
        'form': form
    }
    return render(request, 'teacher/manage_enrollments.html', context)


@login_required
def delete_enrollment(request, enrollment_id):
    """Delete an enrollment"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, course__teacher=request.user)
    student_name = enrollment.student.get_full_name()
    course_name = enrollment.course.name
    enrollment.delete()
    messages.success(request, f'{student_name} removed from {course_name}!')
    return redirect('main:manage_enrollments')


@login_required
def manage_transcripts(request):
    """View and manage student transcripts"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    enrollments = Enrollment.objects.filter(course__teacher=request.user).select_related(
        'student', 'course'
    ).prefetch_related('transcript')
    
    context = {
        'enrollments': enrollments
    }
    return render(request, 'teacher/manage_transcripts.html', context)


@login_required
def create_transcript(request, enrollment_id):
    """Create transcript for an enrollment"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, course__teacher=request.user)
    
    # Check if transcript already exists
    if hasattr(enrollment, 'transcript'):
        messages.warning(request, 'Transcript already exists for this enrollment!')
        return redirect('main:edit_transcript', transcript_id=enrollment.transcript.id)
    
    if request.method == 'POST':
        form = TranscriptForm(request.POST)
        if form.is_valid():
            transcript = form.save(commit=False)
            transcript.enrollment = enrollment
            
            # Auto-calculate grade based on marks (backend validation)
            transcript.grade = Transcript.calculate_grade(
                transcript.marks_obtained, 
                transcript.total_marks
            )
            
            transcript.save()
            messages.success(request, f'Transcript created for {enrollment.student.get_full_name()}!')
            return redirect('main:manage_transcripts')
    else:
        form = TranscriptForm()
    
    context = {
        'form': form,
        'enrollment': enrollment
    }
    return render(request, 'teacher/create_transcript.html', context)


@login_required
def edit_transcript(request, transcript_id):
    """Edit a transcript"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    transcript = get_object_or_404(Transcript, id=transcript_id, enrollment__course__teacher=request.user)
    
    if request.method == 'POST':
        form = TranscriptForm(request.POST, instance=transcript)
        if form.is_valid():
            transcript = form.save(commit=False)
            
            # Auto-calculate grade based on marks (backend validation)
            transcript.grade = Transcript.calculate_grade(
                transcript.marks_obtained, 
                transcript.total_marks
            )
            
            transcript.save()
            messages.success(request, 'Transcript updated successfully!')
            return redirect('main:manage_transcripts')
    else:
        form = TranscriptForm(instance=transcript)
    
    context = {
        'form': form,
        'transcript': transcript
    }
    return render(request, 'teacher/edit_transcript.html', context)


@login_required
def delete_transcript(request, transcript_id):
    """Delete a transcript"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    transcript = get_object_or_404(Transcript, id=transcript_id, enrollment__course__teacher=request.user)
    student_name = transcript.enrollment.student.get_full_name()
    transcript.delete()
    messages.success(request, f'Transcript deleted for {student_name}!')
    return redirect('main:manage_transcripts')


@login_required
def view_reports(request):
    """View all marks reports"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    reports = MarksReport.objects.filter(teacher=request.user).select_related(
        'student', 'transcript__enrollment__course'
    ).prefetch_related('replies')
    
    context = {
        'reports': reports
    }
    return render(request, 'teacher/view_reports.html', context)


@login_required
def report_detail(request, report_id):
    """View and reply to a specific report"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    report = get_object_or_404(MarksReport, id=report_id, teacher=request.user)
    
    # Mark as read when teacher views it
    if not report.is_read_by_teacher:
        report.is_read_by_teacher = True
        report.save()
    
    if request.method == 'POST':
        form = ReportReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.report = report
            reply.sender = request.user
            reply.save()
            
            # Update report status
            report.status = 'replied'
            report.save()
            
            messages.success(request, 'Reply sent successfully!')
            return redirect('main:report_detail', report_id=report.id)
    else:
        form = ReportReplyForm()
    
    context = {
        'report': report,
        'form': form,
        'replies': report.replies.all()
    }
    return render(request, 'teacher/report_detail.html', context)


# ==================== Student Dashboard Views ====================

@login_required
def student_dashboard(request):
    """Student dashboard with courses and transcripts"""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('main:home')
    
    student = request.user
    
    # Get student's enrollments and transcripts
    enrollments = Enrollment.objects.filter(student=student).select_related(
        'course', 'course__teacher'
    ).prefetch_related('transcript')
    
    # Get student's reports
    reports = MarksReport.objects.filter(student=student).select_related(
        'transcript__enrollment__course'
    ).prefetch_related('replies')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'reports': reports,
        'total_courses': enrollments.count(),
    }
    
    return render(request, 'student/student_dashboard.html', context)


@login_required
def submit_marks_report(request, transcript_id):
    """Submit a marks report"""
    if request.user.role != 'student':
        return redirect('main:dashboard')
    
    transcript = get_object_or_404(Transcript, id=transcript_id, enrollment__student=request.user)
    
    if request.method == 'POST':
        form = MarksReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.transcript = transcript
            report.student = request.user
            report.teacher = transcript.enrollment.course.teacher
            report.save()
            messages.success(request, 'Your report has been submitted to the teacher!')
            return redirect('main:dashboard')
    else:
        form = MarksReportForm()
    
    context = {
        'form': form,
        'transcript': transcript
    }
    return render(request, 'student/submit_marks_report.html', context)


@login_required
def student_report_detail(request, report_id):
    """View report details and replies"""
    if request.user.role != 'student':
        return redirect('main:dashboard')
    
    report = get_object_or_404(MarksReport, id=report_id, student=request.user)
    
    # Mark all teacher replies as read when student views them
    report.replies.exclude(sender=request.user).update(is_read_by_student=True)
    
    if request.method == 'POST':
        form = ReportReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.report = report
            reply.sender = request.user
            reply.save()
            
            messages.success(request, 'Reply sent successfully!')
            return redirect('main:student_report_detail', report_id=report.id)
    else:
        form = ReportReplyForm()
    
    context = {
        'report': report,
        'form': form,
        'replies': report.replies.all()
    }
    return render(request, 'student/student_report_detail.html', context)


# ==================== Notification Views ====================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.utils import timezone
from datetime import datetime

@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """Get notifications for current user"""
    notifications = []
    
    if request.user.role == 'teacher':
        # Get unread student reports for teacher
        reports = MarksReport.objects.filter(
            teacher=request.user
        ).select_related('student', 'transcript__enrollment__course').order_by('-created_at')[:20]
        
        for report in reports:
            time_diff = timezone.now() - report.created_at
            if time_diff.days > 0:
                time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds >= 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_str = "Just now"
            
            notifications.append({
                'id': report.id,
                'type': 'report',
                'sender': report.student.get_full_name(),
                'message': f"Report about {report.transcript.enrollment.course.name}: {report.message[:50]}...",
                'time': time_str,
                'is_read': report.is_read_by_teacher,
                'url': f"/teacher/report/{report.id}/",
                'icon': 'fa-user-graduate'
            })
    
    elif request.user.role == 'student':
        # Get unread teacher replies to student's reports
        student_reports = MarksReport.objects.filter(student=request.user)
        replies = ReportReply.objects.filter(
            report__in=student_reports
        ).exclude(sender=request.user).select_related('sender', 'report').order_by('-created_at')[:20]
        
        for reply in replies:
            time_diff = timezone.now() - reply.created_at
            if time_diff.days > 0:
                time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds >= 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_str = "Just now"
            
            notifications.append({
                'id': reply.id,
                'type': 'reply',
                'sender': reply.sender.get_full_name(),
                'message': f"Reply to your report: {reply.message[:50]}...",
                'time': time_str,
                'is_read': reply.is_read_by_student,
                'url': f"/student/report/{reply.report.id}/",
                'icon': 'fa-chalkboard-teacher'
            })
    
    return JsonResponse({'notifications': notifications})


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request):
    """Mark notification as read"""
    try:
        data = json.loads(request.body)
        notif_id = data.get('id')
        notif_type = data.get('type')
        
        if notif_type == 'report' and request.user.role == 'teacher':
            MarksReport.objects.filter(id=notif_id, teacher=request.user).update(is_read_by_teacher=True)
        elif notif_type == 'reply' and request.user.role == 'student':
            ReportReply.objects.filter(id=notif_id).update(is_read_by_student=True)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== COMPREHENSIVE ADMIN VIEWS ====================

@login_required
def admin_create_teacher(request):
    """Admin view to create teacher accounts"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .forms import AdminCreateTeacherForm
    from .models import AuditLog
    
    if request.method == 'POST':
        form = AdminCreateTeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                admin=request.user,
                action='create_teacher',
                description=f'Created teacher account: {teacher.username} ({teacher.get_full_name()})',
                target_user=teacher,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(
                request, 
                f'Teacher account created successfully! '
                f'Email: {teacher.email} | '
                f'Username: {teacher.username} | '
                f'Password: Teacher@123 '
                f'(Please share these credentials with the teacher. They can update their profile and change password after first login.)'
            )
            return redirect('main:admin_teachers_hub')
    else:
        form = AdminCreateTeacherForm()
    
    return render(request, 'admin/admin_create_teacher.html', {'form': form})


@login_required
def admin_edit_user(request, user_id):
    """Admin view to edit student or teacher details"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .forms import AdminEditUserForm
    from .models import AuditLog
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminEditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            
            # Create audit log
            action = 'edit_student' if user.role == 'student' else 'edit_teacher'
            AuditLog.objects.create(
                admin=request.user,
                action=action,
                description=f'Edited {user.role} account: {user.username} ({user.get_full_name()})',
                target_user=user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'{user.get_role_display()} details updated successfully.')
            return redirect('main:coordinator_manage_students' if user.role == 'student' else 'main:teachers-hub')
    else:
        form = AdminEditUserForm(instance=user)
    
    context = {
        'form': form,
        'user_being_edited': user,
    }
    return render(request, 'admin/admin_edit_user.html', context)


@login_required
def admin_search_users(request):
    """Admin view to search and filter students/teachers"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .forms import SearchFilterForm
    
    form = SearchFilterForm(request.GET)
    users = User.objects.none()
    
    if form.is_valid():
        query = form.cleaned_data.get('search_query', '')
        role = form.cleaned_data.get('role_filter', 'all')
        department = form.cleaned_data.get('department_filter', '')
        
        # Start with all users except admin
        users = User.objects.exclude(role='admin')
        
        # Apply role filter
        if role != 'all':
            users = users.filter(role=role)
        
        # Apply search query
        if query:
            users = users.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )
        
        # Apply department filter
        if department:
            users = users.filter(department__icontains=department)
        
        users = users.order_by('role', 'first_name')
    
    context = {
        'form': form,
        'users': users,
    }
    return render(request, 'admin/admin_search_users.html', context)


@login_required
def admin_bulk_import_students(request):
    """Admin view for bulk importing students via CSV"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .forms import BulkStudentImportForm
    from .models import AuditLog
    import csv
    import io
    
    if request.method == 'POST':
        form = BulkStudentImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                file_data = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(file_data))
                
                created_count = 0
                errors = []
                
                for row in csv_reader:
                    full_name = row.get('full_name', '').strip()
                    email = row.get('email', '').strip()
                    student_class = row.get('student_class', '').strip()
                    section = row.get('section', '').strip()
                    roll_number = row.get('roll_number', '').strip()
                    
                    if not email or not full_name:
                        errors.append(f"Row skipped: Missing email or full_name")
                        continue
                    
                    # Check if email already exists
                    if User.objects.filter(email=email).exists():
                        errors.append(f"Email '{email}' already exists, skipped.")
                        continue
                    
                    # Generate username from email
                    username = email.split('@')[0]
                    counter = 1
                    original_username = username
                    while User.objects.filter(username=username).exists():
                        username = f"{original_username}{counter}"
                        counter += 1
                    
                    # Split full name
                    name_parts = full_name.strip().split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    # Create student account with Student@123 password
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='Student@123',
                        first_name=first_name,
                        last_name=last_name,
                        role='student',
                        student_class=student_class,
                        section=section,
                        roll_number=roll_number
                    )
                    created_count += 1
                
                # Create audit log
                AuditLog.objects.create(
                    admin=request.user,
                    action='bulk_import',
                    description=f'Bulk imported {created_count} student account(s) from CSV',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Successfully created {created_count} student account(s). Default password: Student@123')
                if errors:
                    for error in errors[:5]:  # Show first 5 errors
                        messages.warning(request, error)
                
                return redirect('main:admin_students_hub')
            
            except Exception as e:
                messages.error(request, f'Error processing CSV: {str(e)}')
    else:
        form = BulkStudentImportForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin/admin_bulk_import.html', context)


@login_required
def admin_export_data(request):
    """Admin view to export student/grades data"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from django.http import HttpResponse
    from .models import AuditLog
    import csv
    
    export_type = request.GET.get('type', 'students')
    
    response = HttpResponse(content_type='text/csv')
    
    if export_type == 'students':
        response['Content-Disposition'] = 'attachment; filename="students_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Full Name', 'Email', 'Class', 'Section', 'Roll Number', 'Phone', 'Date Joined'])
        
        students = User.objects.filter(role='student').order_by('first_name')
        for student in students:
            writer.writerow([
                student.username,
                student.get_full_name(),
                student.email,
                student.student_class,
                student.section,
                student.roll_number,
                student.phone,
                student.date_joined.strftime('%Y-%m-%d')
            ])
    
    elif export_type == 'teachers':
        response['Content-Disposition'] = 'attachment; filename="teachers_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Full Name', 'Email', 'Department', 'Phone', 'Courses Count', 'Date Joined'])
        
        teachers = User.objects.filter(role='teacher').order_by('first_name')
        for teacher in teachers:
            course_count = Course.objects.filter(teacher=teacher).count()
            writer.writerow([
                teacher.username,
                teacher.get_full_name(),
                teacher.email,
                teacher.department,
                teacher.phone,
                course_count,
                teacher.date_joined.strftime('%Y-%m-%d')
            ])
    
    elif export_type == 'grades':
        response['Content-Disposition'] = 'attachment; filename="grades_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Student', 'Course', 'Marks Obtained', 'Total Marks', 'Percentage', 'Grade', 'Remarks'])
        
        transcripts = Transcript.objects.select_related('enrollment__student', 'enrollment__course').order_by('enrollment__student__first_name')
        for transcript in transcripts:
            writer.writerow([
                transcript.enrollment.student.get_full_name(),
                transcript.enrollment.course.name,
                transcript.marks_obtained,
                transcript.total_marks,
                f"{transcript.percentage:.2f}%",
                transcript.grade,
                transcript.remarks
            ])
    
    # Create audit log
    AuditLog.objects.create(
        admin=request.user,
        action='export_data',
        description=f'Exported {export_type} data to CSV',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return response


@login_required
def admin_create_course(request):
    """Admin view to create a new course"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .forms import AdminCourseForm
    from .models import AuditLog
    
    if request.method == 'POST':
        form = AdminCourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                admin=request.user,
                action='create_course',
                description=f'Created course: {course.code} - {course.name} (Teacher: {course.teacher.get_full_name()})',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Course "{course.name}" has been created successfully.')
            return redirect('main:admin_create_course')
    else:
        form = AdminCourseForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin/admin_create_course.html', context)


@login_required
def admin_manage_courses(request):
    """Admin view to view and manage all courses"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    courses = Course.objects.select_related('teacher').annotate(
        enrollment_count=Count('enrollments')
    ).order_by('name')
    
    context = {
        'courses': courses,
    }
    return render(request, 'admin/admin_manage_courses.html', context)


@login_required
def admin_edit_course(request, course_id):
    """Admin view to edit any course"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .forms import AdminCourseForm
    from .models import AuditLog
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = AdminCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            
            # Create audit log
            AuditLog.objects.create(
                admin=request.user,
                action='edit_course',
                description=f'Edited course: {course.code} - {course.name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Course "{course.name}" has been updated successfully.')
            return redirect('main:admin_manage_courses')
    else:
        form = AdminCourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'admin/admin_edit_course.html', context)


@login_required
def admin_delete_course(request, course_id):
    """Admin view to delete a course"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .models import AuditLog
    
    course = get_object_or_404(Course, id=course_id)
    course_name = course.name
    course_code = course.code
    
    # Create audit log before deletion
    AuditLog.objects.create(
        admin=request.user,
        action='delete_course',
        description=f'Deleted course: {course_code} - {course_name}',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    course.delete()
    messages.success(request, f'Course "{course_name}" has been deleted successfully.')
    return redirect('main:admin_manage_courses')


@login_required
def admin_delete_teacher(request, teacher_id):
    """Admin view to delete a teacher account"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')
    
    from .models import AuditLog
    
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')
    
    if request.method == 'POST':
        username = teacher.username
        full_name = teacher.get_full_name()
        
        # Create audit log before deletion
        AuditLog.objects.create(
            admin=request.user,
            action='delete_teacher',
            description=f'Deleted teacher account: {username} ({full_name})',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        teacher.delete()
        messages.success(request, f'Teacher account "{username}" has been deleted.')
        return redirect('main:admin_view_teachers')
    
    return render(request, 'admin/admin_confirm_delete_teacher.html', {'teacher': teacher})


@login_required
def admin_statistics(request):
    """Admin view with comprehensive statistics and Chart.js data"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')

    from django.db.models import Avg, Count
    from datetime import timedelta
    from django.utils import timezone
    import json as _json

    # Basic statistics
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_courses = Course.objects.all().count()
    total_enrollments = Enrollment.objects.all().count()

    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_students = User.objects.filter(role='student', date_joined__gte=week_ago).count()
    recent_enrollments = Enrollment.objects.filter(enrolled_at__gte=week_ago).count()

    # Grade distribution
    grade_distribution = Transcript.objects.values('grade').annotate(count=Count('grade')).order_by('grade')

    # Department-wise teacher count
    departments = User.objects.filter(role='teacher').exclude(department='').values('department').annotate(count=Count('id')).order_by('-count')

    # ---- Chart data: Monthly student growth (last 12 months) ----
    now = timezone.now()
    monthly_labels = []
    monthly_counts = []
    monthly_enroll_counts = []
    for i in range(11, -1, -1):
        dt = now - timedelta(days=i * 30)
        month_start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            next_dt = now - timedelta(days=(i - 1) * 30)
        else:
            next_dt = now + timedelta(days=1)
        month_end = next_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = month_start.strftime('%b %Y')
        count = User.objects.filter(role='student', date_joined__gte=month_start, date_joined__lt=month_end).count()
        enroll_count = Enrollment.objects.filter(enrolled_at__gte=month_start, enrolled_at__lt=month_end).count()
        monthly_labels.append(label)
        monthly_counts.append(count)
        monthly_enroll_counts.append(enroll_count)

    monthly_student_data = _json.dumps({'labels': monthly_labels, 'counts': monthly_counts})
    monthly_enrollment_data = _json.dumps({'labels': monthly_labels, 'counts': monthly_enroll_counts})

    # ---- Chart data: Yearly student stats (last 5 years) ----
    yearly_labels = []
    yearly_counts = []
    current_year = now.year
    for y in range(current_year - 4, current_year + 1):
        yearly_labels.append(str(y))
        yearly_counts.append(User.objects.filter(role='student', date_joined__year=y).count())

    yearly_student_data = _json.dumps({'labels': yearly_labels, 'counts': yearly_counts})

    # Grade chart data
    grade_labels = _json.dumps([g['grade'] for g in grade_distribution])
    grade_counts = _json.dumps([g['count'] for g in grade_distribution])

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'recent_students': recent_students,
        'recent_enrollments': recent_enrollments,
        'grade_distribution': grade_distribution,
        'departments': departments,
        'monthly_student_data': monthly_student_data,
        'monthly_enrollment_data': monthly_enrollment_data,
        'yearly_student_data': yearly_student_data,
        'grade_labels': grade_labels,
        'grade_counts': grade_counts,
    }
    return render(request, 'admin/admin_statistics.html', context)


# ==================== ADMIN HUB VIEWS ====================

@login_required
def admin_students_hub(request):
    """Students hub page with actions and activity feed"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')

    from .models import AuditLog

    recently_added = User.objects.filter(role='student').order_by('-date_joined')[:10]
    recently_deleted = AuditLog.objects.filter(action='delete_student').order_by('-created_at')[:10]
    recent_activity = AuditLog.objects.filter(
        action__in=['create_student', 'edit_student', 'delete_student']
    ).order_by('-created_at')[:5]

    context = {
        'recently_added': recently_added,
        'recently_deleted': recently_deleted,
        'recent_activity': recent_activity,
    }
    return render(request, 'admin/admin_students_hub.html', context)


@login_required
def admin_teachers_hub(request):
    """Teachers hub page with actions and activity feed"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')

    from .models import AuditLog

    recently_added = User.objects.filter(role='teacher').order_by('-date_joined')[:10]
    recently_deleted = AuditLog.objects.filter(action='delete_teacher').order_by('-created_at')[:10]
    recent_activity = AuditLog.objects.filter(
        action__in=['create_teacher', 'edit_teacher', 'delete_teacher']
    ).order_by('-created_at')[:5]

    context = {
        'recently_added': recently_added,
        'recently_deleted': recently_deleted,
        'recent_activity': recent_activity,
    }
    return render(request, 'admin/admin_teachers_hub.html', context)


@login_required
def admin_courses_hub(request):
    """Courses hub page with list and actions"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')

    courses = Course.objects.select_related('teacher').annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-created_at')

    context = {
        'courses': courses,
    }
    return render(request, 'admin/admin_courses_hub.html', context)


@login_required
def admin_search_api(request):
    """AJAX endpoint for global search on the admin dashboard"""
    if request.user.role != 'admin':
        return JsonResponse({'results': []})

    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    from django.urls import reverse

    users = User.objects.filter(
        Q(role='student') | Q(role='teacher')
    ).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(username__icontains=query)
    ).order_by('role', 'first_name')[:15]

    results = []
    for u in users:
        results.append({
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'username': u.username,
            'email': u.email or '',
            'role': u.role,
            'edit_url': reverse('main:admin_edit_user', args=[u.id]),
        })

    return JsonResponse({'results': results})

