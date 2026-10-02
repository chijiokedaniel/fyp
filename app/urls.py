from django.urls import path

from app.views.site_views import (
    admin_approve_doctor,
    admin_create_doctor,
    admin_create_patient,
    admin_dashboard,
    admin_doctors,
    admin_patients,
    admin_reject_doctor,
    complete_consultation,
    doctor_apply,
    doctor_appointments,
    doctor_dashboard,
    doctor_list,
    doctor_onboarding,
    doctor_pending_approval,
    doctor_working_hours,
    edit_profile,
    home,
    login_view,
    logout_view,
    mark_patient_absent,
    patient_appointments,
    patient_dashboard,
    patient_onboarding,
    patient_register,
    register_view,
    request_appointment,
    respond_appointment,
    submit_appointment_feedback,
)

app_name = 'app'

urlpatterns = [
    path('', home, name='home'),
    path('register/', register_view, name='register'),
    path('patient/register/', patient_register, name='patient_register'),
    path('patient/onboarding/', patient_onboarding, name='patient_onboarding'),
    path('doctor/apply/', doctor_apply, name='doctor_apply'),
    path('doctor/onboarding/', doctor_onboarding, name='doctor_onboarding'),
    path('doctor/pending-approval/', doctor_pending_approval, name='doctor_pending_approval'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Patient URLs
    path('patient/dashboard/', patient_dashboard, name='patient_dashboard'),
    path('patient/appointments/', patient_appointments, name='patient_appointments'),
    path('doctors/', doctor_list, name='doctor_list'),
    path('doctors/<int:doctor_pk>/book/', request_appointment, name='request_appointment'),
    path('appointment/<int:appointment_pk>/feedback/', submit_appointment_feedback, name='submit_appointment_feedback'),
    path('profile/edit/', edit_profile, name='profile_edit'),
    path('appointment/<int:appointment_pk>/respond/', respond_appointment, name='respond_appointment'),
    
    # Doctor URLs
    path('doctor/dashboard/', doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/', doctor_appointments, name='doctor_appointments'),
    path('doctor/working-hours/', doctor_working_hours, name='doctor_working_hours'),
    path('doctor/appointment/<int:appointment_pk>/complete/', complete_consultation, name='complete_consultation'),
    path('doctor/appointment/<int:appointment_pk>/absent/', mark_patient_absent, name='mark_patient_absent'),

    # Basic Admin URLs (/admin/)
    path('admin/', admin_dashboard, name='admin_dashboard'),
    path('admin/doctors/', admin_doctors, name='admin_doctors'),
    path('admin/doctors/create/', admin_create_doctor, name='admin_create_doctor'),
    path('admin/doctors/<int:doctor_pk>/approve/', admin_approve_doctor, name='admin_approve_doctor'),
    path('admin/doctors/<int:doctor_pk>/reject/', admin_reject_doctor, name='admin_reject_doctor'),
    path('admin/patients/', admin_patients, name='admin_patients'),
    path('admin/patients/create/', admin_create_patient, name='admin_create_patient'),
]
