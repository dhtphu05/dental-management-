from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser, UserRole
from apps.billing.models import Invoice
from apps.clinical.models import Service, Tooth, ToothStatus, TreatmentPlan, TreatmentPlanStatus
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


class MixedAuthenticationTests(TestCase):
    def setUp(self):
        self.patient = CustomUser.objects.create_user(
            username="0912333444",
            password="secret123",
            phone="0912333444",
            role=UserRole.PATIENT,
        )
        self.doctor = CustomUser.objects.create_user(
            username="doctorlogin",
            password="secret123",
            phone="0900222333",
            role=UserRole.DOCTOR,
        )

    def test_patient_can_log_in_with_phone(self):
        response = self.client.post(
            reverse("login"),
            {"username": "0912333444", "password": "secret123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.patient.id)

    def test_staff_logs_in_with_username(self):
        response = self.client.post(
            reverse("login"),
            {"username": "doctorlogin", "password": "secret123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.doctor.id)

    def test_staff_cannot_log_in_with_phone(self):
        response = self.client.post(
            reverse("login"),
            {"username": "0900222333", "password": "secret123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tên đăng nhập, số điện thoại hoặc mật khẩu không đúng.")


class PatientHistoryFlowTests(TestCase):
    def setUp(self):
        self.patient_user = CustomUser.objects.create_user(
            username="0912999888",
            password="secret123",
            phone="0912999888",
            role=UserRole.PATIENT,
        )
        self.other_patient_user = CustomUser.objects.create_user(
            username="0912777666",
            password="secret123",
            phone="0912777666",
            role=UserRole.PATIENT,
        )
        self.doctor = CustomUser.objects.create_user(
            username="doctor-history",
            password="secret123",
            phone="0900333000",
            role=UserRole.DOCTOR,
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            full_name="Patient History",
            phone="0912999888",
        )
        self.other_patient = Patient.objects.create(
            user=self.other_patient_user,
            full_name="Other Patient",
            phone="0912777666",
        )
        self.service = Service.objects.create(
            name="Khám tổng quát",
            price=Decimal("150000.00"),
            estimated_duration=timedelta(minutes=30),
        )
        self.completed_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2026, 3, 20),
            time_slot=time(9, 0),
            status=AppointmentStatus.COMPLETED,
            reason="Đau răng",
            notes="Đã khám",
        )
        self.pending_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2026, 3, 28),
            time_slot=time(10, 0),
            status=AppointmentStatus.PENDING,
        )
        self.other_completed_appointment = Appointment.objects.create(
            patient=self.other_patient,
            doctor=self.doctor,
            date=date(2026, 3, 18),
            time_slot=time(8, 30),
            status=AppointmentStatus.COMPLETED,
        )

        tooth = Tooth.objects.get(patient=self.patient, tooth_number=16)
        tooth.status = ToothStatus.CAVITY
        tooth.save(update_fields=["status", "updated_at"])

        plan = TreatmentPlan.objects.create(
            appointment=self.completed_appointment,
            diagnosis="Sâu răng 16",
            notes="Đã trám phục hồi",
            status=TreatmentPlanStatus.COMPLETED,
            resulting_tooth_status=ToothStatus.TREATED,
        )
        plan.services.add(self.service)
        plan.teeth.add(tooth)
        self.invoice = Invoice.objects.get(treatment_plan=plan)
        self.invoice.status = "paid"
        self.invoice.save(update_fields=["status", "updated_at"])

    def test_patient_history_list_only_shows_completed_records(self):
        self.client.login(username="0912999888", password="secret123")

        response = self.client.get(reverse("patient-history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sâu răng 16")
        self.assertContains(response, "Đã thanh toán")
        self.assertNotContains(response, "2026-03-28")

    def test_patient_cannot_view_other_patient_history_detail(self):
        self.client.login(username="0912999888", password="secret123")

        response = self.client.get(reverse("patient-history-detail", args=[self.other_completed_appointment.pk]))

        self.assertEqual(response.status_code, 404)

    def test_patient_history_detail_renders_treatment_and_invoice(self):
        self.client.login(username="0912999888", password="secret123")

        response = self.client.get(reverse("patient-history-detail", args=[self.completed_appointment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hồ sơ điều trị")
        self.assertContains(response, "Sâu răng 16")
        self.assertContains(response, "Khám tổng quát")
        self.assertContains(response, "Răng 16")
        self.assertContains(response, "Đã thanh toán")

    def test_dashboard_links_to_history_and_detail(self):
        self.client.login(username="0912999888", password="secret123")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("patient-history"))
        self.assertContains(response, reverse("patient-history-detail", args=[self.completed_appointment.pk]))

    def test_patient_history_can_filter_by_doctor_and_invoice_status(self):
        second_doctor = CustomUser.objects.create_user(
            username="doctor-second",
            password="secret123",
            phone="0900333111",
            role=UserRole.DOCTOR,
        )
        second_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=second_doctor,
            date=date(2026, 3, 22),
            time_slot=time(11, 0),
            status=AppointmentStatus.COMPLETED,
        )

        self.client.login(username="0912999888", password="secret123")
        response = self.client.get(
            reverse("patient-history"),
            {"doctor": second_doctor.pk, "invoice_status": "none"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, second_doctor.username)
        self.assertContains(response, "Chưa có hóa đơn")
        self.assertNotContains(response, "Sâu răng 16")

    def test_patient_history_is_paginated(self):
        for offset in range(6):
            Appointment.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                date=date(2026, 4, 1) + timedelta(days=offset),
                time_slot=time(8, 0),
                status=AppointmentStatus.COMPLETED,
            )

        self.client.login(username="0912999888", password="secret123")
        response = self.client.get(reverse("patient-history"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["paginator"].per_page, 5)
