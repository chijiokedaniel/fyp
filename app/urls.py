from django.urls import path

from app.views.site_views import (
    doctor_apply,
    doctor_appointments,
    doctor_dashboard,
    doctor_list,
    doctor_onboarding,
    doctor_pending_approval,
    home,
    login_view,
    logout_view,
    patient_appointments,
    patient_dashboard,
    patient_onboarding,
    patient_register,
    request_appointment,
    edit_profile,
    respond_appointment,
)

app_name = 'app'

urlpatterns = [
    path('', home, name='home'),
    path('register/', patient_register, name='patient_register'),
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
    path('profile/edit/', edit_profile, name='profile_edit'),
    path('appointment/<int:appointment_pk>/respond/', respond_appointment, name='respond_appointment'),
    
    # Doctor URLs
    path('doctor/dashboard/', doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/', doctor_appointments, name='doctor_appointments'),
]
