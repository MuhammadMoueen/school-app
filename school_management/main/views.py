from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q, Count, F, Avg
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
import json
from .forms import (TeacherSignupForm, StudentSignupForm, CustomLoginForm,
                   AssignEmailForm, CourseForm, EnrollmentForm, TranscriptForm,
                   MarksReportForm, ReportReplyForm, AdminCreateStudentForm, ProfileEditForm,
                   LectureForm, AttendanceForm, BulkAttendanceForm, QuizForm, QuestionForm,
                   DiscussionThreadForm, DiscussionReplyForm, TeacherActivityResponseForm,
                   AssignmentForm, AssignmentSubmissionForm, AssignmentGradingForm)
from .models import (User, PreassignedEmail, Course, Enrollment, Transcript, MarksReport, ReportReply, Lecture,
                    Attendance, Quiz, Question, QuizAttempt, QuizAnswer, LectureProgress, DiscussionThread, DiscussionReply,
                    AuditLog,
                    TeacherActivityLog, TeacherActivityNotification, TeacherActivityResponse,
                    LectureAttachment, LectureView, LectureDownload, LectureNotification,
                    Assignment, AssignmentAttachment, AssignmentSubmission)

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
    total_students = User.objects.filter(role='student').count()  # All students in the system
    total_enrollments = Enrollment.objects.filter(course__teacher=teacher).count()
    total_assignments = Assignment.objects.filter(created_by=teacher).count()
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'unread_reports': unread_reports,
        'recent_reports': recent_reports,
        'total_students': total_students,
        'total_courses': courses.count(),
        'total_enrollments': total_enrollments,
        'total_assignments': total_assignments,
    }
    
    return render(request, 'teacher/teacher_dashboard.html', context)


def log_teacher_activity(teacher, action_type, description, course=None):
    """Create a persistent teacher activity log and unread notifications for all admins."""
    teacher_name = teacher.get_full_name() or teacher.username
    activity = TeacherActivityLog.objects.create(
        teacher=teacher,
        teacher_name=teacher_name,
        action_type=action_type,
        course=course,
        student_class=course.student_class if course else '',
        section=course.section if course else '',
        description=description,
    )

    admins = User.objects.filter(role='admin', is_active=True)
    TeacherActivityNotification.objects.bulk_create([
        TeacherActivityNotification(admin=admin, activity=activity)
        for admin in admins
    ])

    return activity


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
            teacher_name = request.user.get_full_name() or request.user.username
            log_teacher_activity(
                teacher=request.user,
                action_type='create_course',
                description=f'Teacher {teacher_name} created a new course: {course.name} (Class {course.student_class}{course.section})',
                course=course,
            )
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
            teacher_name = request.user.get_full_name() or request.user.username
            log_teacher_activity(
                teacher=request.user,
                action_type='edit_course',
                description=f'Teacher {teacher_name} edited course details: {course.name} (Class {course.student_class}{course.section})',
                course=course,
            )
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

def _publish_due_scheduled_lectures():
    """Auto-publish any lecture that reached its scheduled publish datetime."""
    Lecture.objects.filter(
        visibility_status='schedule_later',
        is_published=False,
        scheduled_publish_at__isnull=False,
        scheduled_publish_at__lte=timezone.now(),
    ).update(is_published=True)


def _student_can_access_lecture(student, lecture):
    """Check enrollment + class/section eligibility for student lecture access."""
    if student.role != 'student':
        return False

    is_enrolled = Enrollment.objects.filter(student=student, course=lecture.course).exists()
    if not is_enrolled:
        return False

    # Enforce class/section when the student profile contains these fields.
    if student.student_class and student.student_class != lecture.course.student_class:
        return False
    if student.section and student.section != lecture.course.section:
        return False

    return True

@login_required
def manage_lectures(request):
    """View and manage all lectures/materials"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    _publish_due_scheduled_lectures()

    course_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '').strip()
    
    # Get all lectures for this teacher's courses
    lectures = Lecture.objects.filter(
        course__teacher=teacher
    ).select_related('course').annotate(
        views_count=Count('views', distinct=True),
        downloads_count=Count('downloads', distinct=True),
    ).order_by('course', 'order', '-created_at')
    
    # Filter by course if specified
    if course_filter:
        lectures = lectures.filter(course_id=course_filter)
    if status_filter:
        lectures = lectures.filter(visibility_status=status_filter)
    if search_query:
        lectures = lectures.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(course__name__icontains=search_query) |
            Q(course__code__icontains=search_query)
        )
    
    # Get teacher's courses for filter dropdown
    courses = Course.objects.filter(teacher=teacher)
    
    context = {
        'lectures': lectures,
        'courses': courses,
        'selected_course': course_filter,
        'selected_status': status_filter,
        'search_query': search_query,
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

            for uploaded_file in request.FILES.getlist('attachments'):
                LectureAttachment.objects.create(
                    lecture=lecture,
                    title=uploaded_file.name,
                    file=uploaded_file,
                )

            teacher_name = teacher.get_full_name() or teacher.username
            log_teacher_activity(
                teacher=teacher,
                action_type='upload_lecture',
                description=f'Teacher {teacher_name} uploaded a new lecture for {lecture.course.name} (Class {lecture.course.student_class}{lecture.course.section}): {lecture.title}',
                course=lecture.course,
            )
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
            lecture = form.save()

            for uploaded_file in request.FILES.getlist('attachments'):
                LectureAttachment.objects.create(
                    lecture=lecture,
                    title=uploaded_file.name,
                    file=uploaded_file,
                )

            teacher_name = teacher.get_full_name() or teacher.username
            log_teacher_activity(
                teacher=teacher,
                action_type='upload_lecture',
                description=f'Teacher {teacher_name} updated lecture content for {lecture.course.name} (Class {lecture.course.student_class}{lecture.course.section}): {lecture.title}',
                course=lecture.course,
            )
            messages.success(request, f'Lecture "{lecture.title}" updated successfully!')
            return redirect('main:manage_lectures')
    else:
        form = LectureForm(instance=lecture, teacher=teacher)
    
    context = {
        'form': form,
        'lecture': lecture,
        'attachments': lecture.attachments.all(),
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
    
    # Delete lecture and attachment files from storage
    if lecture.file:
        lecture.file.delete()
    for attachment in lecture.attachments.all():
        if attachment.file:
            attachment.file.delete()
    
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
def delete_lecture_attachment(request, lecture_id, attachment_id):
    """Delete an attachment from a lecture (teacher only)."""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    lecture = get_object_or_404(Lecture, id=lecture_id, course__teacher=request.user)
    attachment = get_object_or_404(LectureAttachment, id=attachment_id, lecture=lecture)

    if attachment.file:
        attachment.file.delete()
    attachment.delete()

    messages.success(request, 'Attachment deleted successfully.')
    return redirect('main:edit_lecture', lecture_id=lecture.id)


@login_required
def student_lecture_detail(request, lecture_id):
    """Student lecture detail page with access check and engagement tracking."""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('main:dashboard')

    _publish_due_scheduled_lectures()
    lecture = get_object_or_404(Lecture.objects.select_related('course', 'course__teacher'), id=lecture_id)

    if not lecture.is_published:
        messages.error(request, 'This lecture is not available yet.')
        return redirect('main:dashboard')

    if not _student_can_access_lecture(request.user, lecture):
        messages.error(request, 'Access denied. This lecture is not assigned to your class/section.')
        return redirect('main:dashboard')

    LectureView.objects.get_or_create(lecture=lecture, student=request.user)

    threads = DiscussionThread.objects.filter(lecture=lecture).select_related('author').order_by('-created_at')[:10]

    context = {
        'lecture': lecture,
        'threads': threads,
        'attachments': lecture.attachments.all(),
    }
    return render(request, 'student/student_lecture_detail.html', context)


@login_required
def student_download_lecture_file(request, lecture_id):
    """Track student lecture file downloads and redirect to file URL."""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('main:dashboard')

    lecture = get_object_or_404(Lecture, id=lecture_id, is_published=True)
    if not _student_can_access_lecture(request.user, lecture):
        messages.error(request, 'Access denied.')
        return redirect('main:dashboard')

    if not lecture.file:
        messages.error(request, 'No primary file available for this lecture.')
        return redirect('main:student_lecture_detail', lecture_id=lecture.id)

    download, _ = LectureDownload.objects.get_or_create(
        lecture=lecture,
        attachment=None,
        student=request.user,
    )
    download.download_count += 1
    download.save(update_fields=['download_count', 'last_downloaded_at'])

    return redirect(lecture.file.url)


@login_required
def student_download_lecture_attachment(request, lecture_id, attachment_id):
    """Track student attachment downloads and redirect to file URL."""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('main:dashboard')

    lecture = get_object_or_404(Lecture, id=lecture_id, is_published=True)
    attachment = get_object_or_404(LectureAttachment, id=attachment_id, lecture=lecture)

    if not _student_can_access_lecture(request.user, lecture):
        messages.error(request, 'Access denied.')
        return redirect('main:dashboard')

    download, _ = LectureDownload.objects.get_or_create(
        lecture=lecture,
        attachment=attachment,
        student=request.user,
    )
    download.download_count += 1
    download.save(update_fields=['download_count', 'last_downloaded_at'])

    return redirect(attachment.file.url)


# ==================== ASSIGNMENT MANAGEMENT VIEWS ====================

def _student_can_access_assignment(student, assignment):
    if student.role != 'student':
        return False

    is_enrolled = Enrollment.objects.filter(student=student, course=assignment.course).exists()
    if not is_enrolled:
        return False

    if student.student_class and student.student_class != assignment.student_class:
        return False
    if student.section and student.section != assignment.section:
        return False

    return True


def _late_duration_text(duration):
    if not duration:
        return ''

    total_seconds = int(duration.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"Late by {days} day{'s' if days != 1 else ''}"
    if hours > 0:
        return f"Late by {hours} hour{'s' if hours != 1 else ''}"
    return f"Late by {max(minutes, 1)} minute{'s' if minutes != 1 else ''}"


@login_required
def manage_assignments(request):
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    teacher = request.user
    course_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '').strip()

    assignments = Assignment.objects.filter(created_by=teacher).select_related('course').order_by('-created_at')

    if course_filter:
        assignments = assignments.filter(course_id=course_filter)
    if status_filter:
        assignments = assignments.filter(status=status_filter)
    if search_query:
        assignments = assignments.filter(
            Q(title__icontains=search_query) |
            Q(instructions__icontains=search_query) |
            Q(course__name__icontains=search_query) |
            Q(course__code__icontains=search_query)
        )

    context = {
        'assignments': assignments,
        'courses': Course.objects.filter(teacher=teacher).order_by('code', 'name'),
        'selected_course': course_filter,
        'selected_status': status_filter,
        'search_query': search_query,
    }
    return render(request, 'teacher/manage_assignments.html', context)


@login_required
def create_assignment(request):
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    teacher = request.user

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = teacher
            assignment.save()

            for uploaded_file in request.FILES.getlist('attachments'):
                AssignmentAttachment.objects.create(
                    assignment=assignment,
                    title=uploaded_file.name,
                    file=uploaded_file,
                )

            teacher_name = teacher.get_full_name() or teacher.username
            log_teacher_activity(
                teacher=teacher,
                action_type='create_assessment',
                description=f'Teacher {teacher_name} created assignment for {assignment.course.name} (Class {assignment.student_class}{assignment.section}): {assignment.title}',
                course=assignment.course,
            )

            messages.success(request, f'Assignment "{assignment.title}" created successfully.')
            return redirect('main:manage_assignments')
    else:
        form = AssignmentForm(teacher=teacher)

    return render(request, 'teacher/create_assignment.html', {'form': form})


@login_required
def edit_assignment(request, assignment_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    teacher = request.user
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=teacher)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment, teacher=teacher)
        if form.is_valid():
            assignment = form.save()

            for uploaded_file in request.FILES.getlist('attachments'):
                AssignmentAttachment.objects.create(
                    assignment=assignment,
                    title=uploaded_file.name,
                    file=uploaded_file,
                )

            teacher_name = teacher.get_full_name() or teacher.username
            log_teacher_activity(
                teacher=teacher,
                action_type='create_assessment',
                description=f'Teacher {teacher_name} updated assignment for {assignment.course.name} (Class {assignment.student_class}{assignment.section}): {assignment.title}',
                course=assignment.course,
            )

            messages.success(request, f'Assignment "{assignment.title}" updated successfully.')
            return redirect('main:manage_assignments')
    else:
        form = AssignmentForm(instance=assignment, teacher=teacher)

    context = {
        'form': form,
        'assignment': assignment,
        'attachments': assignment.attachments.all(),
    }
    return render(request, 'teacher/edit_assignment.html', context)


@login_required
def delete_assignment(request, assignment_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    assignment_title = assignment.title

    for attachment in assignment.attachments.all():
        if attachment.file:
            attachment.file.delete()

    for submission in assignment.submissions.all():
        if submission.submission_file:
            submission.submission_file.delete()

    assignment.delete()
    messages.success(request, f'Assignment "{assignment_title}" deleted successfully.')
    return redirect('main:manage_assignments')


@login_required
def delete_assignment_attachment(request, assignment_id, attachment_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    attachment = get_object_or_404(AssignmentAttachment, id=attachment_id, assignment=assignment)

    if attachment.file:
        attachment.file.delete()
    attachment.delete()

    messages.success(request, 'Attachment deleted successfully.')
    return redirect('main:edit_assignment', assignment_id=assignment.id)


@login_required
def assignment_submissions(request, assignment_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    assignment = get_object_or_404(
        Assignment.objects.select_related('course', 'created_by'),
        id=assignment_id,
        created_by=request.user,
    )

    enrollments = Enrollment.objects.filter(course=assignment.course).select_related('student').order_by('student__first_name', 'student__last_name', 'student__username')
    submission_qs = AssignmentSubmission.objects.filter(assignment=assignment).select_related('student', 'graded_by').order_by('student_id', '-attempt_number', '-submitted_at')

    latest_submission_by_student = {}
    for submission in submission_qs:
        if submission.student_id not in latest_submission_by_student:
            latest_submission_by_student[submission.student_id] = submission

    rows = []
    submitted_count = 0
    late_count = 0
    pending_count = 0
    missing_count = 0
    deadline_passed = timezone.now() > assignment.deadline

    for enrollment in enrollments:
        student = enrollment.student
        submission = latest_submission_by_student.get(student.id)

        if submission:
            if submission.is_late:
                row_status = 'Late'
                late_count += 1
            else:
                row_status = 'Submitted'
                submitted_count += 1
            late_text = submission.late_by_text
        else:
            if deadline_passed:
                row_status = 'Missing'
                missing_count += 1
            else:
                row_status = 'Pending'
                pending_count += 1
            late_text = ''

        rows.append({
            'student': student,
            'submission': submission,
            'status': row_status,
            'late_text': late_text,
        })

    context = {
        'assignment': assignment,
        'rows': rows,
        'total_students': enrollments.count(),
        'submitted_count': submitted_count,
        'late_count': late_count,
        'pending_count': pending_count,
        'missing_count': missing_count,
    }
    return render(request, 'teacher/assignment_submissions.html', context)


@login_required
def grade_assignment_submission(request, submission_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related('assignment', 'assignment__course', 'student'),
        id=submission_id,
        assignment__created_by=request.user,
    )

    if request.method == 'POST':
        form = AssignmentGradingForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_by = request.user
            graded_submission.graded_at = timezone.now()
            graded_submission.save()
            messages.success(request, 'Submission graded successfully.')
            return redirect('main:assignment_submissions', assignment_id=submission.assignment.id)
    else:
        form = AssignmentGradingForm(instance=submission)

    return render(request, 'teacher/grade_assignment_submission.html', {
        'form': form,
        'submission': submission,
    })


@login_required
def student_my_assignments(request):
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('main:home')

    student = request.user
    enrolled_course_ids = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
    assignments = Assignment.objects.filter(
        course_id__in=enrolled_course_ids,
    ).exclude(status='draft').select_related('course').order_by('deadline', '-created_at')

    assignment_rows = []
    for assignment in assignments:
        latest_submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=student,
        ).order_by('-attempt_number', '-submitted_at').first()

        if latest_submission:
            if latest_submission.is_late:
                status = 'Late'
                late_text = latest_submission.late_by_text
            else:
                status = 'Submitted'
                late_text = ''
        else:
            if timezone.now() > assignment.deadline:
                status = 'Missing'
            else:
                status = 'Pending'
            late_text = ''

        assignment_rows.append({
            'assignment': assignment,
            'submission': latest_submission,
            'status': status,
            'late_text': late_text,
        })

    return render(request, 'student/my_assignments.html', {
        'assignment_rows': assignment_rows,
    })


@login_required
def submit_assignment(request, assignment_id):
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('main:home')

    assignment = get_object_or_404(Assignment.objects.select_related('course', 'created_by'), id=assignment_id)
    student = request.user

    if assignment.status == 'draft':
        messages.error(request, 'This assignment is not published yet.')
        return redirect('main:student_my_assignments')

    if assignment.status == 'closed':
        messages.error(request, 'This assignment is closed and no longer accepts submissions.')
        return redirect('main:student_my_assignments')

    if not _student_can_access_assignment(student, assignment):
        messages.error(request, 'Access denied. You are not enrolled in this assignment course.')
        return redirect('main:student_my_assignments')

    previous_submissions = AssignmentSubmission.objects.filter(assignment=assignment, student=student).order_by('-attempt_number')
    attempts_used = previous_submissions.count()
    attempts_left = max(assignment.max_attempts - attempts_used, 0)

    if request.method == 'POST':
        if attempts_left <= 0:
            messages.error(request, 'You have reached the maximum number of submission attempts for this assignment.')
            return redirect('main:student_my_assignments')

        if attempts_used > 0 and not assignment.allow_resubmission:
            messages.error(request, 'Resubmission is not allowed for this assignment.')
            return redirect('main:student_my_assignments')

        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = student
            submission.attempt_number = attempts_used + 1
            submission.is_late = timezone.now() > assignment.deadline
            if submission.is_late:
                submission.late_duration = timezone.now() - assignment.deadline
            submission.save()

            if submission.is_late:
                messages.warning(request, f'Submission received. {submission.late_by_text}.')
            else:
                messages.success(request, 'Assignment submitted successfully.')
            return redirect('main:student_my_assignments')
    else:
        form = AssignmentSubmissionForm()

    return render(request, 'student/submit_assignment.html', {
        'form': form,
        'assignment': assignment,
        'attempts_used': attempts_used,
        'attempts_left': attempts_left,
    })


# ==================== ATTENDANCE VIEWS ====================

@login_required
def manage_attendance(request):
    """Teacher attendance page: mark/edit attendance, view history, and daily analytics."""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    teacher = request.user
    courses = Course.objects.filter(teacher=teacher).order_by('code', 'name')

    selected_course_id = (request.POST.get('course') if request.method == 'POST' else request.GET.get('course'))
    raw_selected_date = (request.POST.get('date') if request.method == 'POST' else request.GET.get('date'))

    selected_date = timezone.localdate()
    if raw_selected_date:
        try:
            selected_date = datetime.strptime(raw_selected_date, '%Y-%m-%d').date()
        except ValueError:
            messages.warning(request, 'Invalid date selected. Showing today instead.')

    selected_course = None
    students = []
    history_rows = []
    attendance_exists = False
    total_students = 0
    today = timezone.localdate()
    today_summary = {
        'total_students': 0,
        'present': 0,
        'absent': 0,
        'late': 0,
        'leave': 0,
        'attendance_rate': 0,
    }

    if selected_course_id:
        selected_course = get_object_or_404(Course, id=selected_course_id, teacher=teacher)
        enrollments = Enrollment.objects.filter(course=selected_course).select_related('student').order_by(
            'student__first_name',
            'student__last_name',
            'student__username',
        )
        total_students = enrollments.count()

        selected_date_records = Attendance.objects.filter(
            course=selected_course,
            date=selected_date,
        ).select_related('student')
        attendance_map = {record.student_id: record for record in selected_date_records}
        attendance_exists = selected_date_records.exists()

        if request.method == 'POST':
            valid_statuses = {choice[0] for choice in Attendance.STATUS_CHOICES}

            for enrollment in enrollments:
                student = enrollment.student
                status = request.POST.get(f'status_{student.id}', 'present')
                remarks = request.POST.get(f'remarks_{student.id}', '').strip()

                if status not in valid_statuses:
                    status = 'present'

                existing_record = attendance_map.get(student.id)
                if existing_record:
                    existing_record.status = status
                    existing_record.remarks = remarks
                    existing_record.marked_by = teacher
                    existing_record.student_class = selected_course.student_class
                    existing_record.section = selected_course.section
                    existing_record.save()
                else:
                    Attendance.objects.create(
                        course=selected_course,
                        student=student,
                        date=selected_date,
                        status=status,
                        remarks=remarks,
                        marked_by=teacher,
                        student_class=selected_course.student_class,
                        section=selected_course.section,
                    )

            teacher_name = teacher.get_full_name() or teacher.username
            log_teacher_activity(
                teacher=teacher,
                action_type='mark_attendance',
                description=f'Teacher {teacher_name} marked attendance for {selected_course.name} (Class {selected_course.student_class}{selected_course.section}) on {selected_date}',
                course=selected_course,
            )

            if attendance_exists:
                messages.info(request, 'Attendance already recorded for this date.')
                messages.success(request, 'Existing attendance has been updated successfully.')
            else:
                messages.success(request, f'Attendance saved successfully for {selected_course.name} on {selected_date}.')

            return redirect(f"{reverse('main:manage_attendance')}?course={selected_course.id}&date={selected_date.isoformat()}")

        selected_date_records = Attendance.objects.filter(
            course=selected_course,
            date=selected_date,
        ).select_related('student')
        attendance_map = {record.student_id: record for record in selected_date_records}
        attendance_exists = selected_date_records.exists()

        for enrollment in enrollments:
            record = attendance_map.get(enrollment.student_id)
            students.append({
                'student': enrollment.student,
                'attendance': record,
                'status': record.status if record else 'present',
            })

        course_records = Attendance.objects.filter(course=selected_course).order_by('-date')
        history_map = {}
        for record in course_records:
            row = history_map.setdefault(record.date, {
                'date': record.date,
                'present': 0,
                'absent': 0,
                'late': 0,
                'leave': 0,
            })
            row[record.status] += 1

        history_rows = sorted(history_map.values(), key=lambda row: row['date'], reverse=True)[:20]

        today_records = Attendance.objects.filter(course=selected_course, date=today)
        today_summary['total_students'] = total_students
        today_summary['present'] = today_records.filter(status='present').count()
        today_summary['absent'] = today_records.filter(status='absent').count()
        today_summary['late'] = today_records.filter(status='late').count()
        today_summary['leave'] = today_records.filter(status='leave').count()
        today_summary['attendance_rate'] = round(
            (today_summary['present'] / total_students * 100) if total_students > 0 else 0,
            2,
        )

    context = {
        'courses': courses,
        'selected_course': selected_course,
        'selected_course_id': str(selected_course.id) if selected_course else '',
        'selected_date': selected_date.isoformat(),
        'students': students,
        'attendance_exists': attendance_exists,
        'history_rows': history_rows,
        'today_summary': today_summary,
        'today_date': today,
    }
    return render(request, 'teacher/manage_attendance.html', context)


@login_required
def mark_attendance(request):
    """Legacy route - redirect to unified attendance management page."""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')

    course_id = request.GET.get('course', '')
    selected_date = request.GET.get('date', '')
    if course_id and selected_date:
        return redirect(f"{reverse('main:manage_attendance')}?course={course_id}&date={selected_date}")
    return redirect('main:manage_attendance')


@login_required
def attendance_report(request, course_id):
    """View attendance report for a course"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    # Get all students enrolled in this course
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    
    # Calculate attendance statistics for each student
    student_stats = []
    for enrollment in enrollments:
        student = enrollment.student
        attendances = Attendance.objects.filter(course=course, student=student)
        
        total = attendances.count()
        present = attendances.filter(status='present').count()
        absent = attendances.filter(status='absent').count()
        late = attendances.filter(status='late').count()
        leave = attendances.filter(status='leave').count()
        
        percentage = (present / total * 100) if total > 0 else 0
        
        student_stats.append({
            'student': student,
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'leave': leave,
            'percentage': round(percentage, 2)
        })
    
    context = {
        'course': course,
        'student_stats': student_stats,
    }
    
    return render(request, 'teacher/attendance_report.html', context)


# ==================== QUIZ VIEWS ====================

@login_required
def manage_quizzes(request):
    """View and manage all quizzes"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    quizzes = Quiz.objects.filter(created_by=teacher).select_related('course').order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
    }
    
    return render(request, 'teacher/manage_quizzes.html', context)


@login_required
def create_quiz(request):
    """Create a new quiz"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    
    if request.method == 'POST':
        form = QuizForm(request.POST, teacher=teacher)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = teacher
            quiz.save()
            teacher_name = teacher.get_full_name() or teacher.username
            log_teacher_activity(
                teacher=teacher,
                action_type='create_assessment',
                description=f'Teacher {teacher_name} created a quiz for {quiz.course.name} (Class {quiz.course.student_class}{quiz.course.section}): {quiz.title}',
                course=quiz.course,
            )
            messages.success(request, f'Quiz "{quiz.title}" created successfully! Now add questions.')
            return redirect('main:add_questions', quiz_id=quiz.id)
    else:
        form = QuizForm(teacher=teacher)
    
    context = {
        'form': form,
    }
    
    return render(request, 'teacher/create_quiz.html', context)


@login_required
def edit_quiz(request, quiz_id):
    """Edit an existing quiz"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=teacher)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, f'Quiz "{quiz.title}" updated successfully!')
            return redirect('main:manage_quizzes')
    else:
        form = QuizForm(instance=quiz, teacher=teacher)
    
    context = {
        'form': form,
        'quiz': quiz,
    }
    
    return render(request, 'teacher/edit_quiz.html', context)


@login_required
def delete_quiz(request, quiz_id):
    """Delete a quiz"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=teacher)
    
    quiz_title = quiz.title
    quiz.delete()
    
    messages.success(request, f'Quiz "{quiz_title}" deleted successfully!')
    return redirect('main:manage_quizzes')


@login_required
def add_questions(request, quiz_id):
    """Add questions to a quiz"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=teacher)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            teacher_name = teacher.get_full_name() or teacher.username
            log_teacher_activity(
                teacher=teacher,
                action_type='create_assessment',
                description=f'Teacher {teacher_name} added quiz questions for {quiz.course.name} (Class {quiz.course.student_class}{quiz.course.section}): {quiz.title}',
                course=quiz.course,
            )
            messages.success(request, 'Question added successfully!')
            return redirect('main:add_questions', quiz_id=quiz.id)
    else:
        # Set default order to next number
        next_order = quiz.questions.count() + 1
        form = QuestionForm(initial={'order': next_order})
    
    questions = quiz.questions.all().order_by('order')
    
    context = {
        'quiz': quiz,
        'form': form,
        'questions': questions,
    }
    
    return render(request, 'teacher/add_questions.html', context)


@login_required
def edit_question(request, question_id):
    """Edit a quiz question"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    question = get_object_or_404(Question, id=question_id, quiz__created_by=teacher)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('main:add_questions', quiz_id=question.quiz.id)
    else:
        form = QuestionForm(instance=question)
    
    context = {
        'form': form,
        'question': question,
        'quiz': question.quiz,
    }
    
    return render(request, 'teacher/edit_question.html', context)


@login_required
def delete_question(request, question_id):
    """Delete a quiz question"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    question = get_object_or_404(Question, id=question_id, quiz__created_by=teacher)
    
    quiz_id = question.quiz.id
    question.delete()
    
    messages.success(request, 'Question deleted successfully!')
    return redirect('main:add_questions', quiz_id=quiz_id)


@login_required
def quiz_results(request, quiz_id):
    """View quiz results for all students"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=teacher)
    
    attempts = QuizAttempt.objects.filter(quiz=quiz, is_completed=True).select_related('student').order_by('-score')
    
    context = {
        'quiz': quiz,
        'attempts': attempts,
    }
    
    return render(request, 'teacher/quiz_results.html', context)


# ==================== STUDENT PROGRESS VIEWS ====================

@login_required
def course_analytics(request):
    """View analytics for all courses"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    courses = Course.objects.filter(teacher=teacher)
    
    course_stats = []
    for course in courses:
        # Get enrolled students
        total_students = Enrollment.objects.filter(course=course).count()
        
        # Get lecture stats
        total_lectures = Lecture.objects.filter(course=course, is_published=True).count()
        
        # Get average progress
        if total_students > 0 and total_lectures > 0:
            completed_progress = LectureProgress.objects.filter(
                lecture__course=course,
                is_completed=True
            ).count()
            avg_progress = (completed_progress / (total_students * total_lectures) * 100) if total_students * total_lectures > 0 else 0
        else:
            avg_progress = 0
        
        # Get quiz stats
        total_quizzes = Quiz.objects.filter(course=course, is_published=True).count()
        completed_attempts = QuizAttempt.objects.filter(quiz__course=course, is_completed=True).count()
        
        # Get attendance stats
        attendance_records = Attendance.objects.filter(course=course)
        total_attendance = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0
        
        course_stats.append({
            'course': course,
            'total_students': total_students,
            'total_lectures': total_lectures,
            'avg_progress': round(avg_progress, 2),
            'total_quizzes': total_quizzes,
            'completed_attempts': completed_attempts,
            'attendance_rate': round(attendance_rate, 2),
        })
    
    context = {
        'course_stats': course_stats,
    }
    
    return render(request, 'teacher/course_analytics.html', context)


@login_required
def student_performance(request, course_id):
    """View detailed performance of students in a course"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    teacher = request.user
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    
    student_performance = []
    for enrollment in enrollments:
        student = enrollment.student
        
        # Lecture progress
        total_lectures = Lecture.objects.filter(course=course, is_published=True).count()
        completed_lectures = LectureProgress.objects.filter(
            lecture__course=course,
            student=student,
            is_completed=True
        ).count()
        lecture_progress = (completed_lectures / total_lectures * 100) if total_lectures > 0 else 0
        
        # Quiz performance
        quiz_attempts = QuizAttempt.objects.filter(
            quiz__course=course,
            student=student,
            is_completed=True
        )
        avg_quiz_score = quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0
        
        # Attendance
        attendance_records = Attendance.objects.filter(course=course, student=student)
        total_attendance = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0
        
        # Overall grade
        try:
            transcript = Transcript.objects.get(enrollment=enrollment)
            grade = transcript.grade
            percentage = transcript.percentage
        except Transcript.DoesNotExist:
            grade = 'N/A'
            percentage = 0
        
        student_performance.append({
            'student': student,
            'lecture_progress': round(lecture_progress, 2),
            'completed_lectures': completed_lectures,
            'total_lectures': total_lectures,
            'avg_quiz_score': round(avg_quiz_score, 2),
            'attendance_rate': round(attendance_rate, 2),
            'grade': grade,
            'percentage': round(percentage, 2),
        })
    
    # Sort by percentage descending
    student_performance = sorted(student_performance, key=lambda x: x['percentage'], reverse=True)
    
    context = {
        'course': course,
        'student_performance': student_performance,
    }
    
    return render(request, 'teacher/student_performance.html', context)


# ==================== DISCUSSION FORUM VIEWS ====================

@login_required
def lecture_discussions(request, lecture_id):
    """View discussions for a specific lecture"""
    lecture = get_object_or_404(Lecture, id=lecture_id)
    
    # Check access: teacher of the course or enrolled student
    if request.user.role == 'teacher':
        if lecture.course.teacher != request.user:
            messages.error(request, 'Access denied.')
            return redirect('main:home')
    elif request.user.role == 'student':
        if not Enrollment.objects.filter(course=lecture.course, student=request.user).exists():
            messages.error(request, 'Access denied. You must be enrolled in this course.')
            return redirect('main:home')
    else:
        messages.error(request, 'Access denied.')
        return redirect('main:home')
    
    threads = DiscussionThread.objects.filter(lecture=lecture).select_related('author').order_by('-created_at')
    
    if request.method == 'POST':
        form = DiscussionThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.lecture = lecture
            thread.author = request.user
            thread.save()

            if request.user.role == 'student' and lecture.course.teacher != request.user:
                actor_name = request.user.get_full_name() or request.user.username
                LectureNotification.objects.create(
                    recipient=lecture.course.teacher,
                    actor=request.user,
                    lecture=lecture,
                    thread=thread,
                    notification_type='student_comment',
                    message=f'{actor_name} commented on "{lecture.title}" in {lecture.course.name}.',
                )

            messages.success(request, 'Discussion thread created successfully!')
            return redirect('main:lecture_discussions', lecture_id=lecture.id)
    else:
        form = DiscussionThreadForm()
    
    context = {
        'lecture': lecture,
        'threads': threads,
        'form': form,
    }

    template_name = 'teacher/lecture_discussions.html' if request.user.role == 'teacher' else 'student/lecture_discussions.html'
    return render(request, template_name, context)


@login_required
def discussion_detail(request, thread_id):
    """View a specific discussion thread with replies"""
    thread = get_object_or_404(DiscussionThread, id=thread_id)
    lecture = thread.lecture
    
    # Check access
    if request.user.role == 'teacher':
        if lecture.course.teacher != request.user:
            messages.error(request, 'Access denied.')
            return redirect('main:home')
    elif request.user.role == 'student':
        if not Enrollment.objects.filter(course=lecture.course, student=request.user).exists():
            messages.error(request, 'Access denied.')
            return redirect('main:home')
    
    replies = thread.replies.select_related('author').order_by('created_at')
    
    if request.method == 'POST':
        form = DiscussionReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()

            if request.user.role == 'teacher' and thread.author.role == 'student':
                actor_name = request.user.get_full_name() or request.user.username
                LectureNotification.objects.create(
                    recipient=thread.author,
                    actor=request.user,
                    lecture=lecture,
                    thread=thread,
                    reply=reply,
                    notification_type='teacher_reply',
                    message=f'{actor_name} replied to your lecture discussion on "{lecture.title}".',
                )
            elif request.user.role == 'student' and lecture.course.teacher != request.user:
                actor_name = request.user.get_full_name() or request.user.username
                LectureNotification.objects.create(
                    recipient=lecture.course.teacher,
                    actor=request.user,
                    lecture=lecture,
                    thread=thread,
                    reply=reply,
                    notification_type='student_comment',
                    message=f'{actor_name} replied in lecture discussion "{thread.title}".',
                )

            messages.success(request, 'Reply posted successfully!')
            return redirect('main:discussion_detail', thread_id=thread.id)
    else:
        form = DiscussionReplyForm()
    
    context = {
        'thread': thread,
        'lecture': lecture,
        'replies': replies,
        'form': form,
    }

    template_name = 'teacher/discussion_detail.html' if request.user.role == 'teacher' else 'student/discussion_detail.html'
    return render(request, template_name, context)


@login_required
def mark_discussion_resolved(request, thread_id):
    """Mark a discussion thread as resolved (teacher only)"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('main:home')
    
    thread = get_object_or_404(DiscussionThread, id=thread_id)
    
    if thread.lecture.course.teacher != request.user:
        messages.error(request, 'Access denied.')
        return redirect('main:home')
    
    thread.is_resolved = not thread.is_resolved
    thread.save()
    
    status = "resolved" if thread.is_resolved else "reopened"
    messages.success(request, f'Discussion thread marked as {status}!')
    
    return redirect('main:discussion_detail', thread_id=thread.id)


@login_required
def manage_enrollments(request):
    """Enroll students in subjects"""
    if request.user.role != 'teacher':
        return redirect('main:dashboard')
    
    enrollments = Enrollment.objects.filter(course__teacher=request.user).select_related(
        'student', 'course'
    )
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, teacher=request.user)

        if form.is_valid():
            created_enrollments, skipped_students = form.save()
            course = form.cleaned_data['course']

            if created_enrollments:
                teacher_name = request.user.get_full_name() or request.user.username
                log_teacher_activity(
                    teacher=request.user,
                    action_type='enroll_students',
                    description=f'Teacher {teacher_name} enrolled {len(created_enrollments)} student(s) in {course.name} (Class {course.student_class}{course.section})',
                    course=course,
                )
                messages.success(
                    request,
                    f'{len(created_enrollments)} student(s) enrolled in {course.name} ({course.student_class}{course.section}).'
                )

            if skipped_students:
                skipped_names = ', '.join(student.get_full_name() or student.username for student in skipped_students)
                messages.warning(
                    request,
                    f'These student(s) were already enrolled in {course.name}: {skipped_names}.'
                )

            if created_enrollments or skipped_students:
                return redirect('main:manage_enrollments')
    else:
        form = EnrollmentForm(teacher=request.user)
    
    context = {
        'enrollments': enrollments,
        'form': form
    }
    return render(request, 'teacher/manage_enrollments.html', context)


@login_required
def get_course_students(request):
    """Return students matching the selected course class and section"""
    if request.user.role != 'teacher':
        return JsonResponse({'students': [], 'message': 'Access denied.'}, status=403)

    course_id = request.GET.get('course_id')
    if not course_id:
        return JsonResponse({'students': [], 'message': 'Course not provided.'}, status=400)

    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    students = User.objects.filter(
        role='student',
        student_class=course.student_class,
        section=course.section,
    ).exclude(
        enrollments__course=course
    ).order_by('first_name', 'last_name', 'username')

    student_data = [
        {
            'id': student.id,
            'name': student.get_full_name() or student.username,
            'roll_number': student.roll_number,
        }
        for student in students
    ]

    return JsonResponse({
        'students': student_data,
        'message': '' if student_data else 'No students found for this class and section.',
    })


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
            teacher_name = request.user.get_full_name() or request.user.username
            course = enrollment.course
            log_teacher_activity(
                teacher=request.user,
                action_type='upload_transcript',
                description=f'Teacher {teacher_name} uploaded student transcript for {course.name} (Class {course.student_class}{course.section}) - Student: {enrollment.student.get_full_name() or enrollment.student.username}',
                course=course,
            )
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
            teacher_name = request.user.get_full_name() or request.user.username
            course = transcript.enrollment.course
            student_name = transcript.enrollment.student.get_full_name() or transcript.enrollment.student.username
            log_teacher_activity(
                teacher=request.user,
                action_type='update_grades',
                description=f'Teacher {teacher_name} updated student grades for {course.name} (Class {course.student_class}{course.section}) - Student: {student_name}',
                course=course,
            )
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

            teacher_name = request.user.get_full_name() or request.user.username
            course = report.transcript.enrollment.course
            log_teacher_activity(
                teacher=request.user,
                action_type='post_report',
                description=f'Teacher {teacher_name} posted a report reply for {course.name} (Class {course.student_class}{course.section})',
                course=course,
            )
            
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
    _publish_due_scheduled_lectures()
    
    # Get student's enrollments and transcripts
    enrollments = Enrollment.objects.filter(student=student).select_related(
        'course', 'course__teacher'
    ).prefetch_related('transcript')
    
    # Get student's reports
    reports = MarksReport.objects.filter(student=student).select_related(
        'transcript__enrollment__course'
    ).prefetch_related('replies')

    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    lectures = Lecture.objects.filter(
        course_id__in=enrolled_course_ids,
        is_published=True,
    ).select_related('course', 'course__teacher').prefetch_related('attachments').order_by('-lecture_date', '-created_at')[:10]

    assignments = Assignment.objects.filter(
        course_id__in=enrolled_course_ids,
    ).exclude(status='draft').select_related('course').order_by('deadline', '-created_at')

    assignment_rows = []
    for assignment in assignments[:8]:
        latest_submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=student,
        ).order_by('-attempt_number', '-submitted_at').first()

        if latest_submission:
            status = 'Late' if latest_submission.is_late else 'Submitted'
            late_text = latest_submission.late_by_text
        else:
            status = 'Missing' if timezone.now() > assignment.deadline else 'Pending'
            late_text = ''

        assignment_rows.append({
            'assignment': assignment,
            'submission': latest_submission,
            'status': status,
            'late_text': late_text,
        })

    pending_assignments_count = sum(1 for row in assignment_rows if row['status'] == 'Pending')

    attendance_records = list(
        Attendance.objects.filter(
            student=student,
            course_id__in=enrolled_course_ids,
        ).select_related('course').order_by('-date', 'course__code')
    )

    attendance_by_course = {}
    for record in attendance_records:
        stats = attendance_by_course.setdefault(record.course_id, {
            'course': record.course,
            'present': 0,
            'absent': 0,
            'late': 0,
            'leave': 0,
            'total': 0,
        })
        stats[record.status] += 1
        stats['total'] += 1

    attendance_summary_rows = []
    for enrollment in enrollments:
        stats = attendance_by_course.get(enrollment.course_id, {
            'course': enrollment.course,
            'present': 0,
            'absent': 0,
            'late': 0,
            'leave': 0,
            'total': 0,
        })
        attendance_rate = (stats['present'] / stats['total'] * 100) if stats['total'] else 0
        attendance_summary_rows.append({
            'course': stats['course'],
            'present': stats['present'],
            'absent': stats['absent'],
            'late': stats['late'],
            'leave': stats['leave'],
            'attendance_rate': round(attendance_rate, 2),
        })

    attendance_history_rows = attendance_records[:20]
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'reports': reports,
        'recent_lectures': lectures,
        'assignment_rows': assignment_rows,
        'pending_assignments_count': pending_assignments_count,
        'attendance_summary_rows': attendance_summary_rows,
        'attendance_history_rows': attendance_history_rows,
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

            report.is_read_by_teacher = False
            report.save(update_fields=['is_read_by_teacher', 'updated_at'])
            
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

def _relative_time_text(reference_time):
    """Return a compact human-readable relative timestamp."""
    time_diff = timezone.now() - reference_time
    if time_diff.days > 0:
        return f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
    if time_diff.seconds >= 3600:
        hours = time_diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if time_diff.seconds >= 60:
        minutes = time_diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "Just now"

@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """Get notifications for current user"""
    notifications = []

    if request.user.role == 'admin':
        admin_notifications = TeacherActivityNotification.objects.filter(
            admin=request.user
        ).select_related('activity', 'activity__course').order_by('-created_at')[:20]

        for notif in admin_notifications:
            activity = notif.activity
            notifications.append({
                'id': notif.id,
                'type': 'teacher_activity',
                'sender': activity.teacher_name,
                'message': activity.description,
                'time': _relative_time_text(activity.timestamp),
                'is_read': notif.is_seen,
                'url': reverse('main:admin_notification_detail', args=[notif.id]),
                'icon': 'fa-chalkboard-teacher'
            })
        return JsonResponse({'notifications': notifications})
    
    if request.user.role == 'teacher':
        # Student reports addressed to teacher
        reports = MarksReport.objects.filter(
            teacher=request.user
        ).select_related('student', 'transcript__enrollment__course').order_by('-created_at')[:20]
        
        for report in reports:
            notifications.append({
                'id': report.id,
                'type': 'report',
                'sender': report.student.get_full_name() or report.student.username,
                'message': f"Student {report.student.get_full_name() or report.student.username} sent a report in {report.transcript.enrollment.course.name}",
                'time': _relative_time_text(report.created_at),
                'is_read': report.is_read_by_teacher,
                'sort_time': report.created_at.isoformat(),
                'url': reverse('main:report_detail', args=[report.id]),
                'icon': 'fa-user-graduate'
            })

        # Student replies inside existing report conversation threads
        student_replies = ReportReply.objects.filter(
            report__teacher=request.user,
            sender__role='student',
        ).select_related('sender', 'report', 'report__transcript__enrollment__course').order_by('-created_at')[:20]

        for reply in student_replies:
            sender_name = reply.sender.get_full_name() or reply.sender.username
            notifications.append({
                'id': reply.id,
                'type': 'student_reply',
                'sender': sender_name,
                'message': f"Student {sender_name} sent you a message",
                'time': _relative_time_text(reply.created_at),
                'is_read': reply.report.is_read_by_teacher,
                'sort_time': reply.created_at.isoformat(),
                'url': reverse('main:report_detail', args=[reply.report.id]),
                'icon': 'fa-comment-dots'
            })

        # Teacher outbound messages to students (activity confirmation)
        teacher_replies = ReportReply.objects.filter(
            report__teacher=request.user,
            sender=request.user,
        ).select_related('report', 'report__student').order_by('-created_at')[:20]

        for reply in teacher_replies:
            student_name = reply.report.student.get_full_name() or reply.report.student.username
            notifications.append({
                'id': reply.id,
                'type': 'teacher_reply_sent',
                'sender': request.user.get_full_name() or request.user.username,
                'message': f"You sent a message to {student_name}",
                'time': _relative_time_text(reply.created_at),
                'is_read': True,
                'sort_time': reply.created_at.isoformat(),
                'url': reverse('main:report_detail', args=[reply.report.id]),
                'icon': 'fa-paper-plane'
            })

        # Admin to teacher assignment/system activity notifications
        assignment_notifications = AuditLog.objects.filter(
            target_user=request.user,
            action__in=['create_course', 'edit_course'],
        ).select_related('admin').order_by('-created_at')[:20]

        for audit in assignment_notifications:
            admin_name = audit.admin.get_full_name() or audit.admin.username
            notifications.append({
                'id': audit.id,
                'type': 'course_assignment',
                'sender': admin_name,
                'message': audit.description,
                'time': _relative_time_text(audit.created_at),
                'is_read': audit.is_seen_by_target,
                'sort_time': audit.created_at.isoformat(),
                'url': reverse('main:manage_courses'),
                'icon': 'fa-book-open'
            })

        admin_responses = TeacherActivityResponse.objects.filter(
            notification__activity__teacher=request.user
        ).select_related('admin', 'notification__activity').order_by('-created_at')[:20]

        for response in admin_responses:
            notifications.append({
                'id': response.id,
                'type': 'admin_message',
                'sender': response.admin.get_full_name() or response.admin.username,
                'message': response.message,
                'time': _relative_time_text(response.created_at),
                'is_read': response.is_read_by_teacher,
                'sort_time': response.created_at.isoformat(),
                'url': reverse('main:dashboard'),
                'icon': 'fa-user-shield'
            })

        lecture_notifications = LectureNotification.objects.filter(
            recipient=request.user,
        ).select_related('actor', 'lecture').order_by('-created_at')[:20]

        for notif in lecture_notifications:
            notifications.append({
                'id': notif.id,
                'type': 'lecture_notification',
                'sender': (notif.actor.get_full_name() or notif.actor.username) if notif.actor else 'System',
                'message': notif.message,
                'time': _relative_time_text(notif.created_at),
                'is_read': notif.is_read,
                'sort_time': notif.created_at.isoformat(),
                'url': reverse('main:lecture_discussions', args=[notif.lecture.id]),
                'icon': 'fa-comments'
            })

        notifications.sort(key=lambda item: item.get('sort_time', ''), reverse=True)
        for item in notifications:
            item.pop('sort_time', None)
    
    elif request.user.role == 'student':
        # Get unread teacher replies to student's reports
        student_reports = MarksReport.objects.filter(student=request.user)
        replies = ReportReply.objects.filter(
            report__in=student_reports
        ).exclude(sender=request.user).select_related('sender', 'report').order_by('-created_at')[:20]
        
        for reply in replies:
            notifications.append({
                'id': reply.id,
                'type': 'reply',
                'sender': reply.sender.get_full_name(),
                'message': f"Reply to your report: {reply.message[:50]}...",
                'time': _relative_time_text(reply.created_at),
                'is_read': reply.is_read_by_student,
                'sort_time': reply.created_at.isoformat(),
                'url': f"/student/report/{reply.report.id}/",
                'icon': 'fa-chalkboard-teacher'
            })

        lecture_notifications = LectureNotification.objects.filter(
            recipient=request.user,
        ).select_related('actor', 'lecture').order_by('-created_at')[:20]

        for notif in lecture_notifications:
            notifications.append({
                'id': notif.id,
                'type': 'lecture_notification',
                'sender': (notif.actor.get_full_name() or notif.actor.username) if notif.actor else 'System',
                'message': notif.message,
                'time': _relative_time_text(notif.created_at),
                'is_read': notif.is_read,
                'sort_time': notif.created_at.isoformat(),
                'url': reverse('main:student_lecture_detail', args=[notif.lecture.id]),
                'icon': 'fa-comments'
            })

        notifications.sort(key=lambda item: item.get('sort_time', ''), reverse=True)
        for item in notifications:
            item.pop('sort_time', None)
    
    return JsonResponse({'notifications': notifications})


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request):
    """Mark notification as read"""
    try:
        data = json.loads(request.body)
        notif_id = data.get('id')
        notif_type = data.get('type')
        
        if notif_type == 'teacher_activity' and request.user.role == 'admin':
            TeacherActivityNotification.objects.filter(
                id=notif_id,
                admin=request.user,
            ).update(is_seen=True, seen_at=timezone.now())
        elif notif_type == 'report' and request.user.role == 'teacher':
            MarksReport.objects.filter(id=notif_id, teacher=request.user).update(is_read_by_teacher=True)
        elif notif_type == 'admin_message' and request.user.role == 'teacher':
            TeacherActivityResponse.objects.filter(
                id=notif_id,
                notification__activity__teacher=request.user,
            ).update(is_read_by_teacher=True)
        elif notif_type == 'student_reply' and request.user.role == 'teacher':
            report_ids = list(ReportReply.objects.filter(
                id=notif_id,
                report__teacher=request.user,
                sender__role='student',
            ).values_list('report_id', flat=True))
            if report_ids:
                MarksReport.objects.filter(id__in=report_ids, teacher=request.user).update(is_read_by_teacher=True)
        elif notif_type == 'course_assignment' and request.user.role == 'teacher':
            AuditLog.objects.filter(
                id=notif_id,
                target_user=request.user,
            ).update(is_seen_by_target=True, seen_by_target_at=timezone.now())
        elif notif_type == 'reply' and request.user.role == 'student':
            ReportReply.objects.filter(id=notif_id, report__student=request.user).update(is_read_by_student=True)
        elif notif_type == 'lecture_notification' and request.user.role in ['teacher', 'student']:
            LectureNotification.objects.filter(id=notif_id, recipient=request.user).update(is_read=True)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all unread notifications as read for current user."""
    try:
        now = timezone.now()

        if request.user.role == 'admin':
            TeacherActivityNotification.objects.filter(
                admin=request.user,
                is_seen=False,
            ).update(is_seen=True, seen_at=now)

        elif request.user.role == 'teacher':
            MarksReport.objects.filter(teacher=request.user, is_read_by_teacher=False).update(is_read_by_teacher=True)

            TeacherActivityResponse.objects.filter(
                notification__activity__teacher=request.user,
                is_read_by_teacher=False,
            ).update(is_read_by_teacher=True)

            AuditLog.objects.filter(
                target_user=request.user,
                is_seen_by_target=False,
            ).update(is_seen_by_target=True, seen_by_target_at=now)

            LectureNotification.objects.filter(
                recipient=request.user,
                is_read=False,
            ).update(is_read=True)

        elif request.user.role == 'student':
            ReportReply.objects.filter(
                report__student=request.user,
                is_read_by_student=False,
            ).update(is_read_by_student=True)

            LectureNotification.objects.filter(
                recipient=request.user,
                is_read=False,
            ).update(is_read=True)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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
                description=f'Admin assigned you to {course.name} (Class {course.student_class}{course.section})',
                target_user=course.teacher,
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
    previous_teacher = course.teacher
    
    if request.method == 'POST':
        form = AdminCourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                admin=request.user,
                action='edit_course',
                description=f'Admin updated your assignment for {course.name} (Class {course.student_class}{course.section})',
                target_user=course.teacher,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            if previous_teacher != course.teacher:
                AuditLog.objects.create(
                    admin=request.user,
                    action='edit_course',
                    description=f'Admin assigned you to {course.name} (Class {course.student_class}{course.section})',
                    target_user=course.teacher,
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


@login_required
def admin_teacher_activity_logs(request):
    """Admin page to review all teacher academic activity with filters."""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')

    teacher_id = request.GET.get('teacher', '').strip()
    course_id = request.GET.get('course', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    search_query = request.GET.get('q', '').strip()

    activities = TeacherActivityLog.objects.select_related('teacher', 'course').all()

    if teacher_id:
        activities = activities.filter(teacher_id=teacher_id)
    if course_id:
        activities = activities.filter(course_id=course_id)
    if start_date:
        activities = activities.filter(timestamp__date__gte=start_date)
    if end_date:
        activities = activities.filter(timestamp__date__lte=end_date)
    if search_query:
        activities = activities.filter(
            Q(teacher_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(course__name__icontains=search_query)
        )

    context = {
        'activities': activities,
        'teachers': User.objects.filter(role='teacher').order_by('first_name', 'last_name', 'username'),
        'courses': Course.objects.select_related('teacher').order_by('name'),
        'selected_teacher': teacher_id,
        'selected_course': course_id,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
    }
    return render(request, 'admin/admin_teacher_activity_logs.html', context)


@login_required
def admin_notification_detail(request, notification_id):
    """Detailed view for a teacher activity notification."""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('main:home')

    notification = get_object_or_404(
        TeacherActivityNotification.objects.select_related('activity', 'activity__teacher', 'activity__course'),
        id=notification_id,
        admin=request.user,
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'mark_seen':
            notification.is_seen = True
            notification.seen_at = timezone.now()
            notification.save(update_fields=['is_seen', 'seen_at'])
            messages.success(request, 'Notification marked as seen.')
            return redirect('main:admin_notification_detail', notification_id=notification.id)

        if action == 'save_response':
            form = TeacherActivityResponseForm(request.POST)
            if form.is_valid():
                response = form.save(commit=False)
                response.notification = notification
                response.admin = request.user
                response.save()

                if not notification.is_seen:
                    notification.is_seen = True
                    notification.seen_at = timezone.now()
                    notification.save(update_fields=['is_seen', 'seen_at'])

                if response.response_type == 'message':
                    messages.success(request, 'Message sent and activity recorded.')
                else:
                    messages.success(request, 'Question/report submitted and activity recorded.')
                return redirect('main:admin_notification_detail', notification_id=notification.id)
        else:
            form = TeacherActivityResponseForm()
    else:
        form = TeacherActivityResponseForm()

    context = {
        'notification_item': notification,
        'activity': notification.activity,
        'responses': notification.responses.select_related('admin').all(),
        'response_form': form,
    }
    return render(request, 'admin/admin_notification_detail.html', context)


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


@login_required
def update_student_status(request):
    """AJAX endpoint to update student status"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)
    
    try:
        import json
        data = json.loads(request.body)
        student_id = data.get('student_id')
        new_status = data.get('status')
        
        if not student_id or not new_status:
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        
        # Validate status choice
        valid_statuses = ['active', 'inactive', 'suspended', 'alumni']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status.'}, status=400)
        
        # Get student
        student = User.objects.get(id=student_id, role='student')
        old_status = student.status
        student.status = new_status
        student.save()
        
        # Create audit log
        try:
            from .models import AuditLog
            AuditLog.objects.create(
                admin=request.user,
                action='update_student_status',
                description=f'Updated student status from {old_status} to {new_status}: {student.username} ({student.get_full_name()})',
                target_user=student,
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except:
            pass  # Continue even if audit log fails
        
        return JsonResponse({
            'success': True,
            'message': f'Status updated to {new_status}',
            'new_status': new_status,
            'status_display': student.get_status_display()
        })
    
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


