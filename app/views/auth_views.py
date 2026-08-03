from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from app.forms.auth_forms import LoginForm
from app.models import UserRole


def home(request):
    return render(request, 'app/home.html')


def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == UserRole.DOCTOR:
            if not hasattr(request.user, 'doctor_profile'):
                return redirect('app:doctor_onboarding')
            elif not request.user.doctor_profile.approved:
                return redirect('app:doctor_pending_approval')
            return redirect('app:doctor_dashboard')
        elif request.user.role == UserRole.PATIENT:
            if not request.user.first_name:
                return redirect('app:patient_onboarding')
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
                if not user.first_name:
                    return redirect('app:patient_onboarding')
                return redirect('app:patient_dashboard')
            return redirect('app:home')
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('app:home')
