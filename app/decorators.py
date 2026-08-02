from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

from app.models import UserRole


def patient_required(view_func):
    """Decorator to restrict view access to patients only."""
    @wraps(view_func)
    @login_required(login_url='app:login')
    def wrapper(request, *args, **kwargs):
        if request.user.role == UserRole.PATIENT:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'This page is only accessible to patients.')
        return redirect('app:home')
    return wrapper


def doctor_required(view_func):
    """Decorator to restrict view access to approved doctors only."""
    @wraps(view_func)
    @login_required(login_url='app:login')
    def wrapper(request, *args, **kwargs):
        if request.user.role != UserRole.DOCTOR:
            messages.error(request, 'This page is only accessible to doctors.')
            return redirect('app:home')

        # Check 1: Must complete onboarding
        if not hasattr(request.user, 'doctor_profile'):
            messages.info(request, 'Please complete your doctor onboarding first.')
            return redirect('app:doctor_onboarding')

        # Check 2: Must be approved by admin
        if not request.user.doctor_profile.approved:
            return redirect('app:doctor_pending_approval')

        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator to restrict view access to admins only."""
    @wraps(view_func)
    @login_required(login_url='app:login')
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'This page is only accessible to administrators.')
        return redirect('app:home')
    return wrapper
