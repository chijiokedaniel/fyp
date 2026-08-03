from datetime import time, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Appointment, DoctorProfile, DoctorWorkingHours, SpecialtyChoices, User, UserRole


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

        # Create doctor 2 and 3 for testing global limits
        self.doctor2 = User.objects.create_user(
            username='doctor2',
            email='doctor2@example.com',
            password='password123',
            role=UserRole.DOCTOR,
            first_name='Alan',
            last_name='Turing'
        )
        DoctorProfile.objects.create(user=self.doctor2, specialty=SpecialtyChoices.DERMATOLOGY, approved=True)

        self.doctor3 = User.objects.create_user(
            username='doctor3',
            email='doctor3@example.com',
            password='password123',
            role=UserRole.DOCTOR,
            first_name='Clara',
            last_name='Barton'
        )
        DoctorProfile.objects.create(user=self.doctor3, specialty=SpecialtyChoices.PEDIATRICS, approved=True)

        self.doctor4 = User.objects.create_user(
            username='doctor4',
            email='doctor4@example.com',
            password='password123',
            role=UserRole.DOCTOR,
            first_name='David',
            last_name='Livingstone'
        )
        DoctorProfile.objects.create(user=self.doctor4, specialty=SpecialtyChoices.NEUROLOGY, approved=True)

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

        response = self.client.post(
            reverse('app:respond_appointment', kwargs={'appointment_pk': appointment.pk}),
            {'action': 'accept', 'confirmed_time': '14:30'}
        )

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
        self.assertIsNotNone(appointment.confirmed_date)
        self.assertIsNotNone(appointment.verification_pin)
        self.assertEqual(len(appointment.verification_pin), 6)
        self.assertEqual(appointment.confirmed_date.date(), target_date)
        self.assertEqual(appointment.confirmed_date.time(), time(14, 30))
        self.assertEqual(response.status_code, 302)

    def test_doctor_complete_consultation_with_valid_and_invalid_pin(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_user,
            specialty=SpecialtyChoices.CARDIOLOGY,
            reason='Consultation',
            requested_date=timezone.now(),
            confirmed_date=timezone.now(),
            status=Appointment.Status.CONFIRMED,
            verification_pin='123456'
        )

        self.client.login(username='doctor1', password='password123')

        # Attempt with wrong PIN
        response_wrong = self.client.post(
            reverse('app:complete_consultation', kwargs={'appointment_pk': appointment.pk}),
            {'verification_pin': '999999', 'doctor_notes': 'Some notes'}
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
        self.assertFalse(appointment.doctor_completed)

        # Attempt with correct PIN
        response_correct = self.client.post(
            reverse('app:complete_consultation', kwargs={'appointment_pk': appointment.pk}),
            {'verification_pin': '123456', 'doctor_notes': 'Diagnosis and treatment prescribed.'}
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)
        self.assertTrue(appointment.doctor_completed)
        self.assertTrue(appointment.patient_showed_up)

    def test_mark_patient_absent_after_one_hour(self):
        two_hours_ago = timezone.now() - timedelta(hours=2)
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_user,
            specialty=SpecialtyChoices.CARDIOLOGY,
            reason='Follow-up',
            requested_date=two_hours_ago,
            confirmed_date=two_hours_ago,
            status=Appointment.Status.CONFIRMED,
            verification_pin='654321'
        )

        self.client.login(username='doctor1', password='password123')

        response = self.client.post(
            reverse('app:mark_patient_absent', kwargs={'appointment_pk': appointment.pk}),
            {'doctor_notes': 'Patient failed to show up.'}
        )

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.ABSENT)
        self.assertFalse(appointment.patient_showed_up)
        self.assertTrue(appointment.doctor_completed)
