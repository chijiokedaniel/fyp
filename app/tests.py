from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import time, timedelta
from app.models import User, UserRole, DoctorProfile, DoctorWorkingHours, Appointment, SpecialtyChoices


class DoctorWorkingHoursAndAppointmentTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='password123',
            role=UserRole.PATIENT,
            first_name='John',
            last_name='Doe'
        )

        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='password123',
            role=UserRole.DOCTOR,
            first_name='Sarah',
            last_name='Smith'
        )

        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialty=SpecialtyChoices.CARDIOLOGY,
            approved=True
        )

    def test_doctor_working_hours_creation(self):
        wh = DoctorWorkingHours.objects.create(
            doctor=self.doctor_user,
            day=0,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )
        self.assertEqual(str(wh), "Monday: 09:00 AM - 05:00 PM")
        self.assertEqual(len(self.doctor_user.get_working_hours_list()), 1)

    def test_doctor_accept_appointment_locks_day_and_sets_time(self):
        target_date = (timezone.now() + timedelta(days=2)).date()
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_user,
            specialty=SpecialtyChoices.CARDIOLOGY,
            reason='Chest discomfort',
            requested_date=timezone.make_aware(timezone.datetime.combine(target_date, time(0, 0)))
        )

        self.client.login(username='doctor1', password='password123')

        # Doctor selects time 14:30 for the requested date
        response = self.client.post(
            reverse('app:respond_appointment', kwargs={'appointment_pk': appointment.pk}),
            {'action': 'accept', 'confirmed_time': '14:30'}
        )

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
        self.assertIsNotNone(appointment.confirmed_date)
        # Verify the day remains locked to the requested date
        self.assertEqual(appointment.confirmed_date.date(), target_date)
        self.assertEqual(appointment.confirmed_date.time(), time(14, 30))
        self.assertEqual(response.status_code, 302)

    def test_doctor_reject_appointment_with_reason(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_user,
            specialty=SpecialtyChoices.CARDIOLOGY,
            reason='Routine Checkup',
            requested_date=timezone.now() + timedelta(days=3)
        )

        self.client.login(username='doctor1', password='password123')
        rejection_reason = "Out of office on this date due to conference."

        response = self.client.post(
            reverse('app:respond_appointment', kwargs={'appointment_pk': appointment.pk}),
            {'action': 'reject', 'rejection_reason': rejection_reason}
        )

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        self.assertEqual(appointment.rejection_reason, rejection_reason)
        self.assertEqual(response.status_code, 302)
