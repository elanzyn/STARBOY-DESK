from apps.notifications.models import Notification


def dashboard_context(request):
    if not request.user.is_authenticated:
        return {
            'sidebar_notifications_count': 0,
            'sidebar_recent_notifications': [],
        }

    recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return {
        'sidebar_notifications_count': unread_count,
        'sidebar_recent_notifications': recent_notifications,
    }
