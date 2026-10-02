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

        self.patient2 = User.objects.create_user(
            username='patient2',
            email='patient2@example.com',
            password='password123',
            role=UserRole.PATIENT,
            first_name='Mary',
            last_name='Jones'
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
        selected_time = time(14, 30)
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_user,
            specialty=SpecialtyChoices.CARDIOLOGY,
            reason='Chest discomfort',
            requested_date=timezone.make_aware(timezone.datetime.combine(target_date, selected_time))
        )

        self.client.login(username='doctor1', password='password123')

        response = self.client.post(
            reverse('app:respond_appointment', kwargs={'appointment_pk': appointment.pk}),
            {'action': 'accept'}
        )

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
        self.assertIsNotNone(appointment.confirmed_date)
        self.assertIsNotNone(appointment.verification_pin)
        self.assertEqual(len(appointment.verification_pin), 6)
        self.assertEqual(appointment.confirmed_date.date(), target_date)
        self.assertEqual(appointment.confirmed_date.time(), selected_time)
        self.assertEqual(response.status_code, 302)

    def test_patient_cannot_book_taken_time_slot(self):
        target_date = (timezone.now() + timedelta(days=3)).date()
        slot_dt = timezone.make_aware(timezone.datetime.combine(target_date, time(10, 0)))

        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_user,
            specialty=SpecialtyChoices.CARDIOLOGY,
            reason='Initial booking',
            requested_date=slot_dt,
        )

        self.client.login(username='patient2', password='password123')
        response = self.client.post(
            reverse('app:request_appointment', kwargs={'doctor_pk': self.doctor_user.pk}),
            {
                'requested_date': target_date.strftime('%Y-%m-%d'),
                'requested_time': '10:00',
                'specialty': SpecialtyChoices.CARDIOLOGY,
                'reason': 'Second booking attempt',
                'notes': '',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.filter(doctor=self.doctor_user, requested_date=slot_dt).count(), 1)

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


class AdminWorkflowTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='password123',
            first_name='Super',
            last_name='Admin',
            role=UserRole.ADMIN
        )

    def test_super_admin_panel_access(self):
        self.client.login(username='admin@example.com', password='password123')
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dominion Super Admin Panel")

    def test_basic_admin_dashboard_access(self):
        self.client.login(username='admin@example.com', password='password123')
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Basic Hospital Admin Portal")

    def test_admin_create_doctor(self):
        self.client.login(username='admin@example.com', password='password123')
        response = self.client.post(reverse('app:admin_create_doctor'), {
            'first_name': 'Gregory',
            'last_name': 'House',
            'email': 'dr.house@hospital.com',
            'phone': '1234567890',
            'specialty': SpecialtyChoices.GENERAL,
            'bio': 'Diagnostician',
            'password': 'password123',
            'auto_approve': 'on',
        })
        self.assertEqual(response.status_code, 302)
        created_doctor = User.objects.get(email='dr.house@hospital.com')
        self.assertEqual(created_doctor.role, UserRole.DOCTOR)
        self.assertTrue(created_doctor.doctor_profile.approved)

    def test_admin_create_patient(self):
        self.client.login(username='admin@example.com', password='password123')
        response = self.client.post(reverse('app:admin_create_patient'), {
            'first_name': 'Alice',
            'last_name': 'Wonder',
            'email': 'alice@example.com',
            'phone': '9876543210',
            'address': 'Wonderland',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        created_patient = User.objects.get(email='alice@example.com')
        self.assertEqual(created_patient.role, UserRole.PATIENT)


class UnifiedRegistrationAndOnboardingTests(TestCase):
    def test_registration_page_get_defaults(self):
        response = self.client.get(reverse('app:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Your Account")
        self.assertContains(response, "Patient")
        self.assertContains(response, "Doctor")
        self.assertEqual(response.context['selected_role'], 'patient')

    def test_registration_page_get_with_doctor_param(self):
        response = self.client.get(reverse('app:register') + '?role=doctor')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_role'], 'doctor')

    def test_legacy_doctor_apply_redirects_to_register(self):
        response = self.client.get(reverse('app:doctor_apply'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/register/?role=doctor', response.url)

    def test_legacy_patient_register_redirects_to_register(self):
        response = self.client.get(reverse('app:patient_register'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/register/?role=patient', response.url)

    def test_patient_registration_flow(self):
        response = self.client.post(reverse('app:register'), {
            'role': UserRole.PATIENT,
            'email': 'new_patient@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('app:patient_onboarding'))

        user = User.objects.get(email='new_patient@example.com')
        self.assertEqual(user.role, UserRole.PATIENT)
        self.assertTrue(user.is_authenticated)

    def test_doctor_registration_and_specialization_onboarding(self):
        # 1. Register as a doctor on the unified registration page
        response = self.client.post(reverse('app:register'), {
            'role': UserRole.DOCTOR,
            'email': 'dr_new@hospital.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('app:doctor_onboarding'))

        doctor = User.objects.get(email='dr_new@hospital.com')
        self.assertEqual(doctor.role, UserRole.DOCTOR)

        # 2. Access doctor onboarding page - doctor must choose specialization
        onboarding_page = self.client.get(reverse('app:doctor_onboarding'))
        self.assertEqual(onboarding_page.status_code, 200)
        self.assertContains(onboarding_page, "Medical Specialization")

        # 3. Doctor submits onboarding with specialization (e.g. Cardiology)
        submit_response = self.client.post(reverse('app:doctor_onboarding'), {
            'first_name': 'Leonard',
            'last_name': 'McCoy',
            'phone': '5551234567',
            'specialty': SpecialtyChoices.CARDIOLOGY,
            'bio': 'Chief medical officer and cardiologist.',
        })
        self.assertRedirects(submit_response, reverse('app:doctor_pending_approval'))

        doctor.refresh_from_db()
        self.assertEqual(doctor.first_name, 'Leonard')
        self.assertEqual(doctor.last_name, 'McC McCoy'.replace('McC McCoy', 'McCoy'))
        self.assertTrue(hasattr(doctor, 'doctor_profile'))
        self.assertEqual(doctor.doctor_profile.specialty, SpecialtyChoices.CARDIOLOGY)
        self.assertFalse(doctor.doctor_profile.approved)

    def test_registration_password_mismatch_validation(self):
        response = self.client.post(reverse('app:register'), {
            'role': UserRole.PATIENT,
            'email': 'mismatch@example.com',
            'password1': 'Secret123',
            'password2': 'DifferentPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='mismatch@example.com').exists())
        self.assertContains(response, "Passwords do not match.")

