from django.utils import timezone
from app.models import Appointment, UserRole
from notifications.models.notification import Notification


def appointment_counts(request):
    """Context processor to add appointment counts, upcoming accepted appointment reminders, and unread notification count to all templates."""
    context = {
        'appointment_count': 0,
        'request_count': 0,
        'unread_notifications_count': 0,
        'upcoming_accepted_count': 0,
        'upcoming_next_appointment': None,
    }

    if request.user.is_authenticated:
        now = timezone.now()

        if request.user.role == UserRole.PATIENT:
            context['appointment_count'] = Appointment.objects.filter(
                patient=request.user
            ).count()

            upcoming_qs = Appointment.objects.filter(
                patient=request.user,
                status=Appointment.Status.CONFIRMED,
                confirmed_date__gte=now
            ).order_by('confirmed_date')

            context['upcoming_accepted_count'] = upcoming_qs.count()
            context['upcoming_next_appointment'] = upcoming_qs.first()

        elif request.user.role == UserRole.DOCTOR:
            context['request_count'] = Appointment.objects.filter(
                doctor=request.user,
                status=Appointment.Status.REQUESTED
            ).count()

            upcoming_qs = Appointment.objects.filter(
                doctor=request.user,
                status=Appointment.Status.CONFIRMED,
                confirmed_date__gte=now
            ).order_by('confirmed_date')

            context['upcoming_accepted_count'] = upcoming_qs.count()
            context['upcoming_next_appointment'] = upcoming_qs.first()

        context['unread_notifications_count'] = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

    return context
