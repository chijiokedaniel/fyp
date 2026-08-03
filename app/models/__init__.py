from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    PATIENT = 'patient', 'Patient'
    DOCTOR = 'doctor', 'Doctor'
    ADMIN = 'admin', 'Admin'


class SpecialtyChoices(models.TextChoices):
    GENERAL = 'general', 'General Medicine'
    CARDIOLOGY = 'cardiology', 'Cardiology'
    DERMATOLOGY = 'dermatology', 'Dermatology'
    PEDIATRICS = 'pediatrics', 'Pediatrics'
    ORTHOPEDICS = 'orthopedics', 'Orthopedics'
    PSYCHIATRY = 'psychiatry', 'Psychiatry'
    NEUROLOGY = 'neurology', 'Neurology'


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PATIENT)
    phone = models.CharField(max_length=24, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='patient_profiles/', blank=True, null=True)

    def is_patient(self):
        return self.role == UserRole.PATIENT

    def is_doctor(self):
        return self.role == UserRole.DOCTOR

    @property
    def get_avatar_url(self):
        if hasattr(self, 'doctor_profile') and self.doctor_profile and self.doctor_profile.profile_picture:
            return self.doctor_profile.profile_picture.url
        if self.profile_picture:
            return self.profile_picture.url
        return None


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=50, choices=SpecialtyChoices.choices)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='doctor_profiles/', blank=True, null=True)
    approved = models.BooleanField(default=False)
    applied_at = models.DateTimeField(default=timezone.now)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f'Dr. {self.user.get_full_name()} — {self.get_specialty_display()}'


class Appointment(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    patient = models.ForeignKey(User, limit_choices_to={'role': UserRole.PATIENT}, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(User, limit_choices_to={'role': UserRole.DOCTOR}, on_delete=models.CASCADE, related_name='doctor_appointments')
    specialty = models.CharField(max_length=50, choices=SpecialtyChoices.choices)
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    requested_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Appointment for {self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} on {self.requested_date:%Y-%m-%d %H:%M}'
