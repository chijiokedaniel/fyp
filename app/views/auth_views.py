from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from app.forms.auth_forms import LoginForm
from app.models import UserRole


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
