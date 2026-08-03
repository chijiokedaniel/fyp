from app.models import Appointment, UserRole
from notifications.models.notification import Notification


def appointment_counts(request):
    """Context processor to add appointment counts and unread notification count to all templates."""
    context = {
        'appointment_count': 0,
        'request_count': 0,
        'unread_notifications_count': 0,
    }
    
    if request.user.is_authenticated:
        if request.user.role == UserRole.PATIENT:
            context['appointment_count'] = Appointment.objects.filter(
                patient=request.user
            ).count()
        elif request.user.role == UserRole.DOCTOR:
            context['request_count'] = Appointment.objects.filter(
                doctor=request.user,
                status=Appointment.Status.REQUESTED
            ).count()
        
        context['unread_notifications_count'] = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    
    return context

