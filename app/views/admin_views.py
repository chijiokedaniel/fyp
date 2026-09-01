from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.decorators import admin_required
from app.forms.admin_forms import AdminDoctorCreationForm, AdminPatientCreationForm
from app.models import Appointment, DoctorProfile, User, UserRole
from notifications.notification_services import NotificationService


@admin_required
def admin_dashboard(request):
    """Basic Admin Dashboard for hospital administration."""
    pending_profiles = DoctorProfile.objects.filter(approved=False).order_by('-applied_at')
    approved_doctors_count = DoctorProfile.objects.filter(approved=True).count()
    total_patients_count = User.objects.filter(role=UserRole.PATIENT).count()
    total_appointments_count = Appointment.objects.count()

    recent_appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-created_at')[:6]
    recent_patients = User.objects.filter(role=UserRole.PATIENT).order_by('-date_joined')[:5]

    context = {
        'pending_profiles': pending_profiles[:5],
        'pending_count': pending_profiles.count(),
        'approved_doctors_count': approved_doctors_count,
        'total_patients_count': total_patients_count,
        'total_appointments_count': total_appointments_count,
        'recent_appointments': recent_appointments,
        'recent_patients': recent_patients,
    }
    return render(request, 'app/admin/dashboard.html', context)


@admin_required
def admin_doctors(request):
    """Doctor management list with filtering and quick approval actions."""
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    queryset = DoctorProfile.objects.select_related('user').order_by('-applied_at')

    if status_filter == 'pending':
        queryset = queryset.filter(approved=False)
    elif status_filter == 'approved':
        queryset = queryset.filter(approved=True)

    if search_query:
        queryset = queryset.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(specialty__icontains=search_query)
        )

    context = {
        'doctor_profiles': queryset,
        'selected_status': status_filter,
        'search_query': search_query,
        'pending_count': DoctorProfile.objects.filter(approved=False).count(),
        'approved_count': DoctorProfile.objects.filter(approved=True).count(),
    }
    return render(request, 'app/admin/doctors_list.html', context)


@admin_required
def admin_approve_doctor(request, doctor_pk):
    """Approve a doctor application."""
    if request.method == 'POST':
        doctor_user = get_object_or_404(User, pk=doctor_pk, role=UserRole.DOCTOR)
        profile, created = DoctorProfile.objects.get_or_create(user=doctor_user)
        
        profile.approved = True
        admin_notes = request.POST.get('admin_notes', '').strip()
        if admin_notes:
            profile.admin_notes = admin_notes
        profile.save()

        NotificationService.send_notification(
            recipient=doctor_user,
            actor=request.user,
            title="Doctor Profile Approved 🎉",
            message="Congratulations! Your doctor profile has been verified and approved by hospital administration. You can now access your doctor dashboard and manage appointments.",
            target_obj=profile,
            category="approval",
            type="success"
        )

        messages.success(request, f'Dr. {doctor_user.get_full_name() or doctor_user.email} has been approved successfully!')
    return redirect('app:admin_doctors')


@admin_required
def admin_reject_doctor(request, doctor_pk):
    """Reject or revoke doctor approval."""
    if request.method == 'POST':
        doctor_user = get_object_or_404(User, pk=doctor_pk, role=UserRole.DOCTOR)
        profile = get_object_or_404(DoctorProfile, user=doctor_user)

        profile.approved = False
        admin_notes = request.POST.get('admin_notes', '').strip()
        if admin_notes:
            profile.admin_notes = admin_notes
        profile.save()

        NotificationService.send_notification(
            recipient=doctor_user,
            actor=request.user,
            title="Doctor Application Status Update ⚠️",
            message=f"Your doctor profile status has been updated to under review. Reason/Notes: {admin_notes or 'Pending administrative review.'}",
            target_obj=profile,
            category="approval",
            type="warning"
        )

        messages.info(request, f'Approval for Dr. {doctor_user.get_full_name() or doctor_user.email} has been revoked.')
    return redirect('app:admin_doctors')


@admin_required
def admin_create_doctor(request):
    """Form view for admin to create and register a new doctor directly."""
    if request.method == 'POST':
        form = AdminDoctorCreationForm(request.POST)
        if form.is_valid():
            user, profile = form.save()

            NotificationService.send_notification(
                recipient=user,
                actor=request.user,
                title="Doctor Account Created 🩺",
                message="An administrator has created your doctor account. You can now log in using your email address.",
                target_obj=profile,
                category="onboarding",
                type="info"
            )

            status_str = "approved and active" if profile.approved else "created (pending onboarding/review)"
            messages.success(
                request,
                f"Doctor account for Dr. {user.get_full_name()} ({user.email}) has been successfully {status_str}!"
            )
            return redirect('app:admin_doctors')
    else:
        form = AdminDoctorCreationForm()

    return render(request, 'app/admin/create_doctor.html', {'form': form})


@admin_required
def admin_patients(request):
    """Patient management list view."""
    search_query = request.GET.get('q', '').strip()

    queryset = User.objects.filter(role=UserRole.PATIENT).annotate(
        appointment_count=Count('patient_appointments')
    ).order_by('-date_joined')

    if search_query:
        queryset = queryset.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    context = {
        'patients': queryset,
        'search_query': search_query,
        'total_patients': queryset.count(),
    }
    return render(request, 'app/admin/patients_list.html', context)


@admin_required
def admin_create_patient(request):
    """Form view for admin to create a new patient account directly."""
    if request.method == 'POST':
        form = AdminPatientCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            NotificationService.send_notification(
                recipient=user,
                actor=request.user,
                title="Welcome to Automated Hospital Management System 🏥",
                message="An administrator created your patient account. You can now log in and book appointments.",
                category="onboarding",
                type="info"
            )

            messages.success(
                request,
                f"Patient account for {user.get_full_name()} ({user.email}) created successfully!"
            )
            return redirect('app:admin_patients')
    else:
        form = AdminPatientCreationForm()

    return render(request, 'app/admin/create_patient.html', {'form': form})
