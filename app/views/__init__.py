from app.views.auth_views import home, login_view, logout_view
from app.views.doctor_views import (
    doctor_apply,
    doctor_appointments,
    doctor_dashboard,
    doctor_onboarding,
    doctor_pending_approval,
    doctor_working_hours,
    respond_appointment,
)
from app.views.patient_views import (
    doctor_list,
    patient_appointments,
    patient_dashboard,
    patient_onboarding,
    patient_register,
    request_appointment,
)
from app.views.profile_views import edit_profile

__all__ = [
    'home',
    'patient_register',
    'patient_onboarding',
    'doctor_apply',
    'doctor_onboarding',
    'doctor_pending_approval',
    'doctor_working_hours',
    'login_view',
    'logout_view',
    'doctor_list',
    'request_appointment',
    'patient_dashboard',
    'patient_appointments',
    'doctor_dashboard',
    'doctor_appointments',
    'edit_profile',
    'respond_appointment',
]
