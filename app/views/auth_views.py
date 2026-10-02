from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from app.forms.auth_forms import LoginForm, RegistrationForm
from app.models import UserRole
from notifications.notification_services import NotificationService


def get_user_dashboard(user):
    """Helper to determine post-login redirect for different roles."""
    if user.is_superuser or user.is_staff or user.role == UserRole.ADMIN:
        return 'app:admin_dashboard'
    elif user.role == UserRole.DOCTOR:
        if not hasattr(user, 'doctor_profile'):
            return 'app:doctor_onboarding'
        elif not user.doctor_profile.approved:
            return 'app:doctor_pending_approval'
        return 'app:doctor_dashboard'
    elif user.role == UserRole.PATIENT:
        if not user.first_name:
            return 'app:patient_onboarding'
        return 'app:patient_dashboard'
    return 'app:home'


def home(request):
    return render(request, 'app/home.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_user_dashboard(request.user))

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
            return redirect(get_user_dashboard(user))
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('app:home')


def register_view(request):
    """
    Unified signup view for both patients and doctors.
    Users select their role (Patient or Doctor).
    Doctors will choose their specialization subsequently in onboarding.
    """
    if request.user.is_authenticated:
        return redirect(get_user_dashboard(request.user))

    initial_role = request.GET.get('role', UserRole.PATIENT).lower()
    if initial_role not in [UserRole.PATIENT, UserRole.DOCTOR]:
        initial_role = UserRole.PATIENT

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if user.role == UserRole.DOCTOR:
                NotificationService.send_notification(
                    recipient=user,
                    actor=None,
                    title="Complete Your Doctor Onboarding 🩺",
                    message="Welcome to Automated Hospital Management System! Please complete your medical onboarding details and choose your specialization to submit your profile for administrator review.",
                    category="onboarding",
                    type="info"
                )
                messages.success(
                    request,
                    'Account created! Please choose your medical specialization and complete your onboarding details below.',
                )
                return redirect('app:doctor_onboarding')
            else:
                NotificationService.send_notification(
                    recipient=user,
                    actor=None,
                    title="Complete Your Patient Profile 📋",
                    message="Welcome to Automated Hospital Management System! Please complete your personal profile to start booking appointments.",
                    category="onboarding",
                    type="info"
                )
                messages.success(
                    request,
                    'Account created! Please complete your personal profile details below.',
                )
                return redirect('app:patient_onboarding')
    else:
        form = RegistrationForm(initial={'role': initial_role})

    selected_role = (
        form.data.get('role')
        if form.is_bound and form.data.get('role') in [UserRole.PATIENT, UserRole.DOCTOR]
        else initial_role
    )

    return render(request, 'app/register.html', {
        'form': form,
        'title': 'Create Your Account',
        'selected_role': selected_role,
    })
