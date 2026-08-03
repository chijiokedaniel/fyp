from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from app.decorators import patient_required
from app.forms.auth_forms import PatientRegistrationForm
from app.forms.doctor_forms import AppointmentRequestForm
from app.forms.profile_forms import PatientOnboardingForm
from app.models import Appointment, SpecialtyChoices, User, UserRole
from notifications.notification_services import NotificationService


def patient_register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            NotificationService.send_notification(
                recipient=user,
                actor=None,
                title="Complete Your Patient Profile 📋",
                message="Welcome to Automated Hospital Management System! Please complete your personal profile to start booking appointments.",
                category="onboarding",
                type="info"
            )

            messages.success(request, 'Account created! Please complete your personal profile details below.')
            return redirect('app:patient_onboarding')
    else:
        form = PatientRegistrationForm()
    return render(request, 'app/register.html', {'form': form, 'title': 'Patient Account Registration'})


@patient_required
def patient_onboarding(request):
    """Onboarding view for patients to set up their personal profile details."""
    user = request.user
    if request.method == 'POST':
        form = PatientOnboardingForm(request.POST, instance=user)
        if form.is_valid():
            form.save()

            NotificationService.send_notification(
                recipient=user,
                actor=None,
                title="Patient Profile Setup Completed 🎉",
                message="Your profile setup is complete! You can now search for specialists and book appointments.",
                category="onboarding",
                type="success"
            )

            messages.success(request, 'Patient onboarding completed! Welcome to your health portal.')
            return redirect('app:patient_dashboard')
    else:
        form = PatientOnboardingForm(instance=user)

    return render(request, 'app/patient_onboarding.html', {'form': form, 'patient': user})


@patient_required
def doctor_list(request):
    doctors = User.objects.filter(role=UserRole.DOCTOR, doctor_profile__approved=True)
    specialty = request.GET.get('specialty')
    if specialty:
        doctors = doctors.filter(doctor_profile__specialty=specialty)

    context = {
        'doctors': doctors,
        'specialties': SpecialtyChoices.choices,
        'selected_specialty': specialty,
    }

    return render(request, 'app/doctor_list.html', context=context)


@login_required
def request_appointment(request, doctor_pk):
    doctor = get_object_or_404(User, pk=doctor_pk, role=UserRole.DOCTOR, doctor_profile__approved=True)
    if request.user.role != UserRole.PATIENT:
        messages.warning(request, 'Only patients can request appointments.')
        return redirect('app:doctor_list')

    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.save()

            formatted_date = appointment.requested_date.strftime("%b %d, %Y")
            patient_name = request.user.get_full_name() or request.user.email
            doctor_name = doctor.get_full_name() or doctor.email

            NotificationService.send_notification(
                recipient=doctor,
                actor=request.user,
                title="New Appointment Request",
                message=f"{patient_name} requested an appointment for {formatted_date}.",
                target_obj=appointment,
                category="appointment_request",
                type="info"
            )

            NotificationService.send_notification(
                recipient=request.user,
                actor=None,
                title="Appointment Request Submitted",
                message=f"Your appointment request with Dr. {doctor_name} for {formatted_date} has been submitted. Dr. {doctor_name} will set the confirmed appointment time based on their available schedule.",
                target_obj=appointment,
                category="appointment_request",
                type="success"
            )

            messages.success(request, f'Appointment request submitted for {formatted_date}. Dr. {doctor_name} will review and assign the confirmed time.')
            return redirect('app:doctor_list')
    else:
        form = AppointmentRequestForm(initial={'specialty': doctor.doctor_profile.specialty})

    return render(request, 'app/appointment_request.html', {'form': form, 'doctor': doctor})


@patient_required
def patient_dashboard(request):
    """Patient dashboard showing profile and appointment summary."""
    patient_appointments = Appointment.objects.filter(patient=request.user).order_by('-requested_date')
    pending = patient_appointments.filter(status=Appointment.Status.REQUESTED).count()
    confirmed = patient_appointments.filter(status=Appointment.Status.CONFIRMED).count()

    context = {
        'patient': request.user,
        'appointments': patient_appointments[:5],
        'pending_count': pending,
        'confirmed_count': confirmed,
    }
    return render(request, 'app/patient_dashboard.html', context)


@patient_required
def patient_appointments(request):
    """Patient view all their appointments."""
    appointments = Appointment.objects.filter(patient=request.user).order_by('-requested_date')

    context = {
        'appointments': appointments,
        'statuses': Appointment.Status.choices,
    }
    return render(request, 'app/patient_appointments.html', context)
