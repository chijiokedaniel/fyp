from datetime import datetime
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.decorators import doctor_required
from app.forms.auth_forms import DoctorApplicationForm
from app.forms.profile_forms import DoctorOnboardingForm
from app.models import Appointment, DayOfWeek, DoctorWorkingHours, UserRole
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

    working_hours = request.user.get_working_hours_list()

    context = {
        'appointments': appointments,
        'statuses': Appointment.Status.choices,
        'selected_status': status_filter,
        'working_hours': working_hours,
    }
    return render(request, 'app/doctor_appointments.html', context)


@doctor_required
def respond_appointment(request, appointment_pk):
    """Doctor accepts (assigning time) or rejects (with reason modal) an appointment request."""
    appointment = get_object_or_404(Appointment, pk=appointment_pk, doctor=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        doctor_name = request.user.get_full_name() or request.user.email

        if action == 'accept':
            confirmed_time_raw = request.POST.get('confirmed_time', '').strip()
            confirmed_date_raw = request.POST.get('confirmed_date', '').strip()

            base_date = appointment.requested_date.date()
            time_obj = None

            if confirmed_time_raw:
                for fmt in ['%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M%p']:
                    try:
                        time_obj = datetime.strptime(confirmed_time_raw, fmt).time()
                        break
                    except ValueError:
                        pass

            if not time_obj and confirmed_date_raw:
                for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%H:%M']:
                    try:
                        parsed = datetime.strptime(confirmed_date_raw, fmt)
                        time_obj = parsed.time()
                        break
                    except ValueError:
                        pass

            if not time_obj:
                time_obj = datetime.strptime('09:00', '%H:%M').time()

            naive_dt = datetime.combine(base_date, time_obj)
            confirmed_dt = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt

            appointment.confirmed_date = confirmed_dt
            appointment.status = Appointment.Status.CONFIRMED
            appointment.generate_verification_pin()
            appointment.save()

            formatted_date = confirmed_dt.strftime("%b %d, %Y at %I:%M %p")
            messages.success(request, f'Appointment confirmed for {formatted_date}. Consultation Verification PIN: {appointment.verification_pin}')

            NotificationService.send_notification(
                recipient=appointment.patient,
                actor=request.user,
                title="Appointment Confirmed 🗓️",
                message=f"Dr. {doctor_name} confirmed your appointment for {formatted_date}. Your Verification PIN is: {appointment.verification_pin}.",
                target_obj=appointment,
                category="appointment_response",
                type="success"
            )
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            appointment.rejection_reason = rejection_reason
            appointment.status = Appointment.Status.CANCELLED
            appointment.save()

            messages.info(request, 'Appointment request has been rejected.')

            reason_str = f" Reason: {rejection_reason}" if rejection_reason else ""
            NotificationService.send_notification(
                recipient=appointment.patient,
                actor=request.user,
                title="Appointment Declined ❌",
                message=f"Dr. {doctor_name} declined your appointment request.{reason_str}",
                target_obj=appointment,
                category="appointment_response",
                type="warning"
            )

    return redirect('app:doctor_appointments')


@doctor_required
def complete_consultation(request, appointment_pk):
    """Doctor completes a consultation by verifying the patient's secret PIN and logging clinical notes."""
    appointment = get_object_or_404(Appointment, pk=appointment_pk, doctor=request.user)

    if request.method == 'POST':
        entered_pin = request.POST.get('verification_pin', '').strip()
        doctor_notes = request.POST.get('doctor_notes', '').strip()

        # Secret PIN Verification Check
        if entered_pin != appointment.verification_pin:
            messages.error(
                request,
                f"❌ Verification Failed: The 6-digit PIN '{entered_pin}' does not match the patient's code. "
                f"Please ask the patient for their secret Verification PIN from their app screen."
            )
            return redirect('app:doctor_appointments')

        appointment.doctor_completed = True
        appointment.doctor_completed_at = timezone.now()
        appointment.patient_showed_up = True
        appointment.doctor_showed_up = True
        appointment.doctor_notes = doctor_notes
        appointment.status = Appointment.Status.COMPLETED
        appointment.save()

        formatted_date = appointment.confirmed_date.strftime("%b %d, %Y") if appointment.confirmed_date else ""
        patient_name = appointment.patient.get_full_name() or appointment.patient.email
        doctor_name = request.user.get_full_name() or request.user.email

        NotificationService.send_notification(
            recipient=appointment.patient,
            actor=request.user,
            title="Consultation Verified & Completed 🩺",
            message=f"Dr. {doctor_name} successfully verified your 6-digit PIN and completed your consultation for {formatted_date}.",
            target_obj=appointment,
            category="appointment",
            type="success"
        )

        messages.success(request, f"✅ PIN Verified! Consultation for {patient_name} marked as completed with logged clinical notes!")

    return redirect('app:doctor_appointments')


@doctor_required
def mark_patient_absent(request, appointment_pk):
    """Doctor marks patient absent after 1 hour from confirmed appointment time without needing PIN."""
    from datetime import timedelta
    appointment = get_object_or_404(Appointment, pk=appointment_pk, doctor=request.user)

    if request.method == 'POST':
        now = timezone.now()
        # Enforce 1-Hour Elapsed Rule
        if appointment.confirmed_date and now < appointment.confirmed_date + timedelta(hours=1):
            messages.error(
                request,
                "⚠️ Rule Notice: You can only mark a patient as Absent/No-Show after 1 hour has elapsed from the scheduled appointment time."
            )
            return redirect('app:doctor_appointments')

        appointment.status = Appointment.Status.ABSENT
        appointment.patient_showed_up = False
        appointment.doctor_completed = True
        appointment.doctor_completed_at = now
        appointment.doctor_notes = request.POST.get('doctor_notes', 'Patient failed to show up for scheduled appointment. Marked absent after 1 hour elapsed.')
        appointment.save()

        formatted_date = appointment.confirmed_date.strftime("%b %d, %Y at %I:%M %p") if appointment.confirmed_date else ""
        patient_name = appointment.patient.get_full_name() or appointment.patient.email
        doctor_name = request.user.get_full_name() or request.user.email

        NotificationService.send_notification(
            recipient=appointment.patient,
            actor=request.user,
            title="Appointment Marked Absent ⚠️",
            message=f"Dr. {doctor_name} marked your appointment on {formatted_date} as Absent (No-Show) because 1 hour elapsed without PIN verification.",
            target_obj=appointment,
            category="appointment",
            type="warning"
        )

        messages.info(request, f"Patient {patient_name} marked as ABSENT (No-Show).")

    return redirect('app:doctor_appointments')


@doctor_required
def doctor_working_hours(request):
    """Doctor view and manage weekly working hours schedule."""
    existing_hours = {wh.day: wh for wh in DoctorWorkingHours.objects.filter(doctor=request.user)}

    if request.method == 'POST':
        for day_code, day_name in DayOfWeek.choices:
            is_available = request.POST.get(f'available_{day_code}') == 'on'
            start_time = request.POST.get(f'start_time_{day_code}', '09:00')
            end_time = request.POST.get(f'end_time_{day_code}', '17:00')

            wh, created = DoctorWorkingHours.objects.get_or_create(
                doctor=request.user,
                day=day_code,
                defaults={'start_time': start_time, 'end_time': end_time, 'is_available': is_available}
            )
            if not created:
                wh.start_time = start_time
                wh.end_time = end_time
                wh.is_available = is_available
                wh.save()

        messages.success(request, 'Your working hours have been updated successfully!')
        return redirect('app:doctor_working_hours')

    days_data = []
    for day_code, day_name in DayOfWeek.choices:
        wh = existing_hours.get(day_code)
        days_data.append({
            'day_code': day_code,
            'day_name': day_name,
            'is_available': wh.is_available if wh else (day_code < 5),
            'start_time': wh.start_time.strftime('%H:%M') if wh else '09:00',
            'end_time': wh.end_time.strftime('%H:%M') if wh else '17:00',
        })

    return render(request, 'app/doctor_working_hours.html', {'days_data': days_data})
