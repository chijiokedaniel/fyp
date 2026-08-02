from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from app.decorators import doctor_required, patient_required
from app.forms.auth_forms import DoctorApplicationForm, LoginForm, PatientRegistrationForm
from app.forms.doctor_forms import AppointmentRequestForm
from app.forms.profile_forms import PatientProfileForm, DoctorProfileForm, DoctorOnboardingForm
from app.models import Appointment, SpecialtyChoices, User, UserRole, DoctorProfile


from notifications.notification_services import NotificationService


def home(request):
    return render(request, 'app/home.html')


def patient_register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your patient account has been created. You can now log in.')
            return redirect('app:login')
    else:
        form = PatientRegistrationForm()
    return render(request, 'app/register.html', {'form': form, 'title': 'Patient Registration'})


def doctor_apply(request):
    if request.method == 'POST':
        form = DoctorApplicationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Notification 1: Doctor Registration Completed
            NotificationService.send_notification(
                recipient=user,
                actor=None,
                title="Complete Your Doctor Onboarding 🩺",
                message="Welcome to Dominion Health! Please complete your medical onboarding details to submit your profile for administrator review.",
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

    # If profile already exists, redirect appropriately
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

            # Notification 2: Onboarding Submitted
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


def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == UserRole.DOCTOR:
            if not hasattr(request.user, 'doctor_profile'):
                return redirect('app:doctor_onboarding')
            elif not request.user.doctor_profile.approved:
                return redirect('app:doctor_pending_approval')
            return redirect('app:doctor_dashboard')
        elif request.user.role == UserRole.PATIENT:
            return redirect('app:patient_dashboard')
        return redirect('app:home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'You are now logged in.')

            if user.role == UserRole.DOCTOR:
                if not hasattr(user, 'doctor_profile'):
                    return redirect('app:doctor_onboarding')
                elif not user.doctor_profile.approved:
                    return redirect('app:doctor_pending_approval')
                return redirect('app:doctor_dashboard')
            elif user.role == UserRole.PATIENT:
                return redirect('app:patient_dashboard')
            return redirect('app:home')
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('app:home')


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

    return render(
        request,
        'app/doctor_list.html',
        context=context
    )


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

            formatted_date = appointment.requested_date.strftime("%b %d, %Y at %I:%M %p")
            patient_name = request.user.get_full_name() or request.user.username
            doctor_name = doctor.get_full_name() or doctor.username

            # Send notification to Doctor
            NotificationService.send_notification(
                recipient=doctor,
                actor=request.user,
                title="New Appointment Request",
                message=f"{patient_name} requested an appointment for {formatted_date}.",
                target_obj=appointment,
                category="appointment_request",
                type="info"
            )

            # Send notification to Patient
            NotificationService.send_notification(
                recipient=request.user,
                actor=None,
                title="Appointment Request Submitted",
                message=f"Your appointment request with Dr. {doctor_name} for {formatted_date} has been submitted.",
                target_obj=appointment,
                category="appointment_request",
                type="success"
            )

            messages.success(request, 'Appointment request submitted. The doctor or admin will review it.')
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
        'appointments': patient_appointments[:5],  # Latest 5
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


@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard showing profile, approval status, and appointment requests."""
    doctor_profile = request.user.doctor_profile
    appointment_requests = Appointment.objects.filter(doctor=request.user, status=Appointment.Status.REQUESTED).order_by('-created_at')
    confirmed = Appointment.objects.filter(doctor=request.user, status=Appointment.Status.CONFIRMED).count()
    
    context = {
        'doctor': request.user,
        'profile': doctor_profile,
        'appointment_requests': appointment_requests[:5],  # Latest 5
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


@login_required
def edit_profile(request):
    """Allow users to edit their profile (patient or doctor)."""
    user = request.user
    if user.role == UserRole.PATIENT:
        if request.method == 'POST':
            form = PatientProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('app:patient_dashboard')
        else:
            form = PatientProfileForm(instance=user)
        return render(request, 'app/profile_edit.html', {'form': form})

    if user.role == UserRole.DOCTOR:
        profile = user.doctor_profile
        if request.method == 'POST':
            form = DoctorProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save(user=user)
                messages.success(request, 'Profile updated successfully.')
                return redirect('app:doctor_dashboard')
        else:
            # prefill combined fields
            initial = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }
            form = DoctorProfileForm(instance=profile, initial=initial)
        return render(request, 'app/profile_edit.html', {'form': form})


@doctor_required
def respond_appointment(request, appointment_pk):
    """Doctor accepts/rejects an appointment request."""
    appointment = get_object_or_404(Appointment, pk=appointment_pk, doctor=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        formatted_date = appointment.requested_date.strftime("%b %d, %Y at %I:%M %p")
        doctor_name = request.user.get_full_name() or request.user.username

        if action == 'accept':
            appointment.status = Appointment.Status.CONFIRMED
            appointment.save()
            messages.success(request, 'Appointment confirmed.')

            # Notify Patient
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

            # Notify Patient
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
