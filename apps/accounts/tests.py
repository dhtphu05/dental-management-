from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser, UserRole
from apps.billing.models import Invoice
from apps.clinical.models import Service, TreatmentPlan
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentStatus


class CrudViewSmokeTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="reception",
            password="secret123",
            phone="0900999999",
            role=UserRole.RECEPTIONIST,
        )
        self.doctor = CustomUser.objects.create_user(
            username="doctor2",
            password="secret123",
            phone="0900888888",
            role=UserRole.DOCTOR,
        )
        self.client.login(username="reception", password="secret123")

    def test_patient_create_view(self):
        response = self.client.post(
            reverse("patient-create"),
            {
                "full_name": "Nguyen Van A",
                "phone": "0900777777",
                "email": "a@example.com",
                "date_of_birth": "1999-01-01",
                "address": "HCM",
                "medical_history": "None",
                "notes": "Test",
            },
        )

        self.assertRedirects(response, reverse("patient-list"))
        self.assertTrue(Patient.objects.filter(phone="0900777777").exists())

    def test_service_create_view(self):
        response = self.client.post(
            reverse("service-create"),
            {
                "name": "Cao voi",
                "price": "200000.00",
                "estimated_duration": "00:30:00",
                "description": "Lam sach",
            },
        )

        self.assertRedirects(response, reverse("service-list"))
        self.assertTrue(Service.objects.filter(name="Cao voi").exists())

    def test_invoice_update_view(self):
        patient = Patient.objects.create(full_name="Patient One", phone="0900666666")
        service = Service.objects.create(
            name="Tram rang",
            price=Decimal("500000.00"),
            estimated_duration=timedelta(minutes=45),
        )
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.doctor,
            date=date(2026, 3, 24),
            time_slot=time(9, 30),
            status=AppointmentStatus.CONFIRMED,
        )
        plan = TreatmentPlan.objects.create(appointment=appointment, diagnosis="Sau rang")
        plan.services.add(service)
        invoice = Invoice.objects.get(treatment_plan=plan)

        response = self.client.post(reverse("invoice-update", args=[invoice.pk]), {"status": "paid"})

        self.assertRedirects(response, reverse("invoice-list"))
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
