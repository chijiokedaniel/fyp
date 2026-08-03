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


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, 'Monday'
    TUESDAY = 1, 'Tuesday'
    WEDNESDAY = 2, 'Wednesday'
    THURSDAY = 3, 'Thursday'
    FRIDAY = 4, 'Friday'
    SATURDAY = 5, 'Saturday'
    SUNDAY = 6, 'Sunday'


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

    def get_working_hours_list(self):
        """Returns sorted list of active working hours for doctors."""
        return self.working_hours.filter(is_available=True).order_by('day')


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


class DoctorWorkingHours(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='working_hours')
    day = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField(default='09:00')
    end_time = models.TimeField(default='17:00')
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day')
        ordering = ['day']

    def __str__(self):
        day_name = self.get_day_display()
        if not self.is_available:
            return f"{day_name}: Off"
        return f"{day_name}: {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


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
    confirmed_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        date_str = self.confirmed_date.strftime('%Y-%m-%d %H:%M') if self.confirmed_date else self.requested_date.strftime('%Y-%m-%d %H:%M')
        return f'Appointment for {self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} on {date_str}'

