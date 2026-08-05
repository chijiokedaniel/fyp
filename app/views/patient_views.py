from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, models
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.decorators import patient_required
from app.forms.auth_forms import PatientRegistrationForm
from app.forms.doctor_forms import AppointmentRequestForm
from app.forms.profile_forms import PatientOnboardingForm
from app.models import Appointment, SpecialtyChoices, User, UserRole
from app.utils.appointment_slots import build_schedule_map
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

    now = timezone.now()
    # Find doctor IDs with active (pending requested or upcoming confirmed) appointments for the current patient
    active_doctor_ids = set(
        Appointment.objects.filter(
            patient=request.user
        ).filter(
            models.Q(status=Appointment.Status.REQUESTED) |
            models.Q(status=Appointment.Status.CONFIRMED, confirmed_date__gt=now)
        ).values_list('doctor_id', flat=True)
    )

    context = {
        'doctors': doctors,
        'specialties': SpecialtyChoices.choices,
        'selected_specialty': specialty,
        'active_doctor_ids': active_doctor_ids,
    }

    return render(request, 'app/doctor_list.html', context=context)


@login_required
def request_appointment(request, doctor_pk):
    doctor = get_object_or_404(User, pk=doctor_pk, role=UserRole.DOCTOR, doctor_profile__approved=True)
    if request.user.role != UserRole.PATIENT:
        messages.warning(request, 'Only patients can request appointments.')
        return redirect('app:doctor_list')

    now = timezone.now()

    # Abuse Prevention Rule 1: Limit total active appointments per patient to MAX 3 across all doctors
    total_active_patient_appointments = Appointment.objects.filter(
        patient=request.user
    ).filter(
        models.Q(status=Appointment.Status.REQUESTED) |
        models.Q(status=Appointment.Status.CONFIRMED, confirmed_date__gt=now)
    ).count()

    MAX_ACTIVE_LIMIT = 3
    if total_active_patient_appointments >= MAX_ACTIVE_LIMIT:
        messages.warning(
            request,
            f"🚫 Abuse Prevention Notice: You currently have {total_active_patient_appointments} active (pending or upcoming) appointments. "
            f"Patients are allowed a maximum of {MAX_ACTIVE_LIMIT} active appointments across all doctors at a time. "
            f"Please wait until your existing appointments conclude or resolve before booking additional consultations."
        )
        return redirect('app:patient_appointments')

    # Check if patient already has an active appointment with this specific doctor
    active_appointment = Appointment.objects.filter(
        patient=request.user,
        doctor=doctor
    ).filter(
        models.Q(status=Appointment.Status.REQUESTED) |
        models.Q(status=Appointment.Status.CONFIRMED, confirmed_date__gt=now)
    ).first()

    if active_appointment:
        doc_name = doctor.get_full_name() or doctor.email
        if active_appointment.status == Appointment.Status.REQUESTED:
            messages.warning(
                request,
                f"You already have a pending appointment request with Dr. {doc_name}. "
                f"You cannot request another appointment with this doctor until your current request is resolved or past."
            )
        else:
            date_str = active_appointment.confirmed_date.strftime("%A, %B %d, %Y at %I:%M %p") if active_appointment.confirmed_date else ""
            messages.warning(
                request,
                f"You already have an active appointment with Dr. {doc_name} scheduled for {date_str}. "
                f"You cannot book another appointment until after your current appointment time has passed."
            )
        return redirect('app:patient_appointments')

    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST, doctor=doctor)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.specialty = doctor.doctor_profile.specialty
            try:
                appointment.save()
            except IntegrityError:
                form.add_error('requested_time', 'That time slot was just booked. Please choose another available slot.')
                schedule_map = build_schedule_map(doctor, timezone.now().date(), days_ahead=14)
                return render(request, 'app/appointment_request.html', {'form': form, 'doctor': doctor, 'schedule_json': schedule_map})

            formatted_date = appointment.requested_date.strftime("%b %d, %Y at %I:%M %p")
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
                message=f"Your appointment request with Dr. {doctor_name} for {formatted_date} has been submitted. Dr. {doctor_name} will review and confirm this selected slot.",
                target_obj=appointment,
                category="appointment_request",
                type="success"
            )

            messages.success(request, f'Appointment request submitted for {formatted_date}. Dr. {doctor_name} will review and confirm the selected slot.')
            return redirect('app:doctor_list')
    else:
        form = AppointmentRequestForm(doctor=doctor)

    schedule_map = build_schedule_map(doctor, timezone.now().date(), days_ahead=14)
    context = {
        'form': form,
        'doctor': doctor,
        'schedule_json': schedule_map,
    }
    return render(request, 'app/appointment_request.html', context)


@patient_required
def submit_appointment_feedback(request, appointment_pk):
    """View to handle post-appointment feedback confirmation from patients."""
    appointment = get_object_or_404(Appointment, pk=appointment_pk, patient=request.user)

    if request.method == 'POST':
        showed_up_str = request.POST.get('doctor_showed_up')
        doctor_showed_up = True if showed_up_str == 'true' else False if showed_up_str == 'false' else None
        rating_str = request.POST.get('rating', '')
        try:
            rating = int(rating_str) if rating_str else None
        except ValueError:
            rating = None
        feedback_text = request.POST.get('patient_feedback', '').strip()

        appointment.doctor_showed_up = doctor_showed_up
        appointment.rating = rating
        appointment.patient_feedback = feedback_text
        appointment.feedback_submitted_at = timezone.now()

        doctor_name = appointment.doctor.get_full_name() or appointment.doctor.email
        patient_name = request.user.get_full_name() or request.user.email

        # Dispute Handling: If patient claims doctor did NOT show up, but doctor already completed consultation notes:
        if doctor_showed_up is False and appointment.doctor_completed:
            appointment.status = Appointment.Status.DISPUTED
            appointment.save()

            messages.warning(
                request,
                f"Your feedback has been recorded. Note: Dr. {doctor_name} logged clinical consultation notes for this session. "
                f"This appointment has been flagged as DISPUTED and queued for Hospital Administration review."
            )

            NotificationService.send_notification(
                recipient=appointment.doctor,
                actor=request.user,
                title="Appointment Disputed 🚨",
                message=f"Patient {patient_name} reported a no-show for the appointment on {appointment.confirmed_date.strftime('%b %d, %Y')}. Case queued for Admin review.",
                target_obj=appointment,
                category="appointment",
                type="warning"
            )
        else:
            appointment.status = Appointment.Status.COMPLETED
            appointment.save()

            if doctor_showed_up is False:
                NotificationService.send_notification(
                    recipient=appointment.doctor,
                    actor=request.user,
                    title="Appointment Attendance Notice ⚠️",
                    message=f"Patient {patient_name} reported that you were unable to attend the appointment on {appointment.confirmed_date.strftime('%b %d, %Y')}.",
                    target_obj=appointment,
                    category="appointment",
                    type="warning"
                )

            NotificationService.send_notification(
                recipient=request.user,
                actor=None,
                title="Feedback Received Thank You! 🌟",
                message=f"Thank you for confirming your feedback for your appointment with Dr. {doctor_name}.",
                target_obj=appointment,
                category="appointment",
                type="success"
            )

            messages.success(request, f"Thank you! Your feedback for Dr. {doctor_name} has been recorded successfully.")

    return redirect(request.META.get('HTTP_REFERER', 'app:patient_dashboard'))

    return redirect(request.META.get('HTTP_REFERER', 'app:patient_dashboard'))


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
