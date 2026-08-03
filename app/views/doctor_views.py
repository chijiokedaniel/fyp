from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from app.decorators import doctor_required
from app.forms.auth_forms import DoctorApplicationForm
from app.forms.profile_forms import DoctorOnboardingForm
from app.models import Appointment, UserRole
from notifications.notification_services import NotificationService


def doctor_apply(request):
    if request.method == 'POST':
        form = DoctorApplicationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            NotificationService.send_notification(
                recipient=user,
                actor=None,
                title="Complete Your Doctor Onboarding 🩺",
                message="Welcome to Automated Hospital Management System! Please complete your medical onboarding details to submit your profile for administrator review.",
                category="onboarding",
                type="info"
            )

            messages.success(
                request,
                'Account created! Please complete your medical onboarding details below.',
            )
            return redirect('app:doctor_onboarding')
    else:
        form = DoctorApplicationForm()
    return render(request, 'app/doctor_application.html', {'form': form, 'title': 'Doctor Registration'})


@login_required
def doctor_onboarding(request):
    """Onboarding view for doctors to complete their profile."""
    if request.user.role != UserRole.DOCTOR:
        messages.error(request, 'Only doctors can access onboarding.')
        return redirect('app:home')

    if hasattr(request.user, 'doctor_profile'):
        if request.user.doctor_profile.approved:
            return redirect('app:doctor_dashboard')
        return redirect('app:doctor_pending_approval')

    if request.method == 'POST':
        form = DoctorOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(user=request.user, commit=False)
            profile.approved = False
            profile.save()

            NotificationService.send_notification(
                recipient=request.user,
                actor=None,
                title="Medical Profile Submitted ⏳",
                message="Your medical profile has been submitted successfully and is currently under review by hospital administration.",
                target_obj=profile,
                category="onboarding",
                type="success"
            )

            messages.success(request, 'Medical profile submitted successfully! Your application is now under review.')
            return redirect('app:doctor_pending_approval')
    else:
        form = DoctorOnboardingForm()

    return render(request, 'app/doctor_onboarding.html', {'form': form, 'doctor': request.user})


@login_required
def doctor_pending_approval(request):
    """Waiting page for doctors awaiting admin approval."""
    if request.user.role != UserRole.DOCTOR:
        messages.error(request, 'Only doctors can access this page.')
        return redirect('app:home')

    if not hasattr(request.user, 'doctor_profile'):
        return redirect('app:doctor_onboarding')

    if request.user.doctor_profile.approved:
        messages.success(request, 'Your doctor profile has been approved! Welcome to your dashboard.')
        return redirect('app:doctor_dashboard')

    return render(request, 'app/doctor_pending_approval.html', {
        'doctor': request.user,
        'profile': request.user.doctor_profile
    })


@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard showing profile, approval status, and appointment requests."""
    doctor_profile = request.user.doctor_profile
    appointment_requests = Appointment.objects.filter(doctor=request.user, status=Appointment.Status.REQUESTED).order_by('-created_at')
    confirmed = Appointment.objects.filter(doctor=request.user, status=Appointment.Status.CONFIRMED).count()

    context = {
        'doctor': request.user,
        'profile': doctor_profile,
        'appointment_requests': appointment_requests[:5],
        'requests_count': appointment_requests.count(),
        'confirmed_count': confirmed,
    }
    return render(request, 'app/doctor_dashboard.html', context)


@doctor_required
def doctor_appointments(request):
    """Doctor view all appointment requests and confirmed appointments."""
    status_filter = request.GET.get('status', '')

    appointments = Appointment.objects.filter(doctor=request.user).order_by('-created_at')
    if status_filter and status_filter in [choice[0] for choice in Appointment.Status.choices]:
        appointments = appointments.filter(status=status_filter)

    context = {
        'appointments': appointments,
        'statuses': Appointment.Status.choices,
        'selected_status': status_filter,
    }
    return render(request, 'app/doctor_appointments.html', context)


@doctor_required
def respond_appointment(request, appointment_pk):
    """Doctor accepts/rejects an appointment request."""
    appointment = get_object_or_404(Appointment, pk=appointment_pk, doctor=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        formatted_date = appointment.requested_date.strftime("%b %d, %Y at %I:%M %p")
        doctor_name = request.user.get_full_name() or request.user.email

        if action == 'accept':
            appointment.status = Appointment.Status.CONFIRMED
            appointment.save()
            messages.success(request, 'Appointment confirmed.')

            NotificationService.send_notification(
                recipient=appointment.patient,
                actor=request.user,
                title="Appointment Confirmed",
                message=f"Dr. {doctor_name} confirmed your appointment request for {formatted_date}.",
                target_obj=appointment,
                category="appointment_response",
                type="success"
            )
        elif action == 'reject':
            appointment.status = Appointment.Status.CANCELLED
            appointment.save()
            messages.info(request, 'Appointment rejected.')

            NotificationService.send_notification(
                recipient=appointment.patient,
                actor=request.user,
                title="Appointment Declined",
                message=f"Dr. {doctor_name} declined your appointment request for {formatted_date}.",
                target_obj=appointment,
                category="appointment_response",
                type="warning"
            )
    return redirect('app:doctor_appointments')
