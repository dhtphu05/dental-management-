from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

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
