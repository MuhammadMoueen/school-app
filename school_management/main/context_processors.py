"""
Context processors for the main app.
These functions add variables to all template contexts.
"""

def notification_count(request):
    """
    Add unread notification count to template context.
    Available in all templates as {{ notification_count }}
    """
    if request.user.is_authenticated:
        try:
            from .models import TeacherActivityNotification, TeacherActivityResponse, MarksReport, ReportReply, LectureNotification, AuditLog, UserNotification

            unread_count = 0
            recent_notifications = []

            if request.user.role == 'admin':
                unread_count = TeacherActivityNotification.objects.filter(
                    admin=request.user,
                    is_seen=False,
                ).count()
                recent_notifications = TeacherActivityNotification.objects.filter(
                    admin=request.user,
                ).select_related('activity').order_by('-created_at')[:5]
            elif request.user.role == 'teacher':
                unread_reports = MarksReport.objects.filter(
                    teacher=request.user,
                    is_read_by_teacher=False,
                ).count()
                unread_assignment_notifications = AuditLog.objects.filter(
                    target_user=request.user,
                    action__in=['create_course', 'edit_course'],
                    is_seen_by_target=False,
                ).count()
                unread_admin_responses = TeacherActivityResponse.objects.filter(
                    notification__activity__teacher=request.user,
                    is_read_by_teacher=False,
                ).count()
                unread_lecture_notifications = LectureNotification.objects.filter(
                    recipient=request.user,
                    is_read=False,
                ).count()
                unread_user_notifications = UserNotification.objects.filter(
                    recipient=request.user,
                    is_read=False,
                ).count()
                unread_count = unread_reports + unread_assignment_notifications + unread_admin_responses + unread_lecture_notifications + unread_user_notifications
            elif request.user.role == 'student':
                unread_report_replies = ReportReply.objects.filter(
                    report__student=request.user,
                    is_read_by_student=False,
                ).exclude(sender=request.user).count()
                unread_lecture_notifications = LectureNotification.objects.filter(
                    recipient=request.user,
                    is_read=False,
                ).count()
                unread_user_notifications = UserNotification.objects.filter(
                    recipient=request.user,
                    is_read=False,
                ).count()
                unread_count = unread_report_replies + unread_lecture_notifications + unread_user_notifications

            return {
                'notification_count': unread_count,
                'unread_notification_count': unread_count,
                'recent_notifications': recent_notifications,
            }
        except Exception:
            return {
                'notification_count': 0,
                'unread_notification_count': 0,
                'recent_notifications': [],
            }
    
    return {
        'notification_count': 0,
        'unread_notification_count': 0,
        'recent_notifications': [],
    }


def site_settings(request):
    """
    Add site-wide settings to template context.
    """
    return {
        'site_name': 'The City School of Bahawalpur',
        'site_short_name': 'TCS',
        'current_year': '2025-2026',
    }
