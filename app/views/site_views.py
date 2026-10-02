"""
Legacy site_views facade re-exporting modularized views from:
- auth_views
- patient_views
- doctor_views
- profile_views
- admin_views
"""

from app.views.admin_views import (
    admin_approve_doctor,
    admin_create_doctor,
    admin_create_patient,
    admin_dashboard,
    admin_doctors,
    admin_patients,
    admin_reject_doctor,
)
from app.views.auth_views import home, login_view, logout_view, register_view
from app.views.doctor_views import (
    complete_consultation,
    doctor_apply,
    doctor_appointments,
    doctor_dashboard,
    doctor_onboarding,
    doctor_pending_approval,
    doctor_working_hours,
    mark_patient_absent,
    respond_appointment,
)
from app.views.patient_views import (
    doctor_list,
    patient_appointments,
    patient_dashboard,
    patient_onboarding,
    patient_register,
    request_appointment,
    submit_appointment_feedback,
)
from app.views.profile_views import edit_profile

__all__ = [
    'home',
    'register_view',
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
    'submit_appointment_feedback',
    'complete_consultation',
    'mark_patient_absent',
    'admin_dashboard',
    'admin_doctors',
    'admin_approve_doctor',
    'admin_reject_doctor',
    'admin_create_doctor',
    'admin_patients',
    'admin_create_patient',
]
