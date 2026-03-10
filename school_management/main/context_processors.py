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
            from .models import Notification
            unread_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
            
            # Get recent notifications
            recent_notifications = Notification.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
            
            return {
                'notification_count': unread_count,
                'recent_notifications': recent_notifications,
            }
        except Exception:
            # If Notification model doesn't exist or any error occurs
            return {
                'notification_count': 0,
                'recent_notifications': [],
            }
    
    return {
        'notification_count': 0,
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
