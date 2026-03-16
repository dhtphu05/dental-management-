from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser, UserRole
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentStatus


class AppointmentValidationTests(TestCase):
    def setUp(self):
        self.doctor = CustomUser.objects.create_user(
            username="doctor1",
            password="secret123",
            phone="0900000001",
            role=UserRole.DOCTOR,
        )
        self.patient_one = Patient.objects.create(full_name="Patient One", phone="0900000002")
        self.patient_two = Patient.objects.create(full_name="Patient Two", phone="0900000003")

    def test_doctor_cannot_have_two_active_appointments_same_slot(self):
        Appointment.objects.create(
            patient=self.patient_one,
            doctor=self.doctor,
            date=date(2026, 3, 20),
            time_slot=time(9, 0),
            status=AppointmentStatus.CONFIRMED,
        )

        duplicate = Appointment(
            patient=self.patient_two,
            doctor=self.doctor,
            date=date(2026, 3, 20),
            time_slot=time(9, 0),
            status=AppointmentStatus.PENDING,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()


class PublicBookingFlowTests(TestCase):
    def setUp(self):
        self.doctor = CustomUser.objects.create_user(
            username="doctor-public",
            password="secret123",
            phone="0900111222",
            role=UserRole.DOCTOR,
        )

    def test_public_booking_page_is_accessible_without_login(self):
        response = self.client.get(reverse("public-booking"))
        self.assertEqual(response.status_code, 200)

    def test_public_booking_creates_account_patient_and_appointment(self):
        response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "Public Patient",
                "phone": "0900333444",
                "doctor": self.doctor.pk,
                "date": "2026-03-25",
                "time_slot": "09:00",
                "reason": "Consultation",
                "notes": "First visit",
            },
        )

        self.assertRedirects(response, reverse("booking-success"))
        self.assertFalse(CustomUser.objects.filter(phone="0900333444", role=UserRole.PATIENT).exists())
        patient = Patient.objects.get(phone="0900333444")
        self.assertIsNone(patient.user)
        self.assertTrue(
            Appointment.objects.filter(
                patient=patient,
                doctor=self.doctor,
                status=AppointmentStatus.PENDING,
            ).exists()
        )

    def test_account_is_created_only_after_booking_success_step(self):
        booking_response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "Public Patient",
                "phone": "0900555666",
                "doctor": self.doctor.pk,
                "date": "2026-03-25",
                "time_slot": "10:00",
                "reason": "Consultation",
                "notes": "",
            },
        )
        self.assertRedirects(booking_response, reverse("booking-success"))

        response = self.client.post(
            reverse("booking-create-account"),
            {
                "password1": "secret123",
                "password2": "secret123",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        patient = Patient.objects.get(phone="0900555666")
        self.assertIsNotNone(patient.user)
        self.assertEqual(patient.user.phone, "0900555666")
