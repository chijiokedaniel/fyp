from app.models import Appointment, UserRole


def appointment_counts(request):
    """Context processor to add appointment counts to all templates."""
    context = {
        'appointment_count': 0,
        'request_count': 0,
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
    
    return context
