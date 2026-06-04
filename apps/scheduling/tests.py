from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser, UserRole
from apps.billing.models import Invoice
from apps.clinical.models import Service, Tooth, ToothStatus, TreatmentPlan, TreatmentPlanStatus
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
        self.second_doctor = CustomUser.objects.create_user(
            username="doctor-public-2",
            password="secret123",
            phone="0900111223",
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
                "date": "2029-03-25",
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
                "date": "2029-03-25",
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

    def test_public_booking_rejects_invalid_phone(self):
        response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "A",
                "phone": "12345",
                "doctor": self.doctor.pk,
                "date": "2099-03-25",
                "time_slot": "09:00",
                "reason": "",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Số điện thoại không hợp lệ")
        self.assertFalse(Patient.objects.filter(phone="12345").exists())

    def test_public_booking_rejects_past_date(self):
        response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "Public Patient",
                "phone": "0900666777",
                "doctor": self.doctor.pk,
                "date": "2000-01-01",
                "time_slot": "09:00",
                "reason": "",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Không thể đặt lịch cho ngày trong quá khứ.")

    def test_public_booking_rejects_invalid_time_slot(self):
        response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "Public Patient",
                "phone": "0900666888",
                "doctor": self.doctor.pk,
                "date": "2099-03-25",
                "time_slot": "12:15",
                "reason": "",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Khung giờ đã chọn không hợp lệ.")

    def test_public_booking_rejects_taken_slot(self):
        Appointment.objects.create(
            patient=Patient.objects.create(full_name="Existing Patient", phone="0900777888"),
            doctor=self.doctor,
            date=date(2099, 3, 25),
            time_slot=time(9, 0),
            status=AppointmentStatus.CONFIRMED,
        )

        response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "Public Patient",
                "phone": "0900666999",
                "doctor": self.doctor.pk,
                "date": "2099-03-25",
                "time_slot": "09:00",
                "reason": "",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Khung giờ này đã có người đặt. Vui lòng chọn giờ khác.")

    def test_public_booking_with_any_doctor_assigns_available_doctor(self):
        response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "Public Patient",
                "phone": "0900123456",
                "doctor": "",
                "date": "2099-03-25",
                "time_slot": "09:30",
                "reason": "Khám tổng quát",
                "notes": "",
            },
        )

        self.assertRedirects(response, reverse("booking-success"))
        appointment = Appointment.objects.get(patient__phone="0900123456")
        self.assertIn(appointment.doctor, [self.doctor, self.second_doctor])

    def test_public_booking_with_any_doctor_rejects_when_all_doctors_busy(self):
        Appointment.objects.create(
            patient=Patient.objects.create(full_name="Existing Patient One", phone="0900777001"),
            doctor=self.doctor,
            date=date(2099, 3, 25),
            time_slot=time(9, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        Appointment.objects.create(
            patient=Patient.objects.create(full_name="Existing Patient Two", phone="0900777002"),
            doctor=self.second_doctor,
            date=date(2099, 3, 25),
            time_slot=time(9, 0),
            status=AppointmentStatus.CONFIRMED,
        )

        response = self.client.post(
            reverse("public-booking"),
            {
                "full_name": "Public Patient",
                "phone": "0900123999",
                "doctor": "",
                "date": "2099-03-25",
                "time_slot": "09:00",
                "reason": "",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Khung giờ này hiện không còn bác sĩ trống. Vui lòng chọn giờ khác.")


class AppointmentDetailViewTests(TestCase):
    def setUp(self):
        self.receptionist = CustomUser.objects.create_user(
            username="reception-detail",
            password="secret123",
            phone="0900111333",
            role=UserRole.RECEPTIONIST,
        )
        self.doctor = CustomUser.objects.create_user(
            username="doctor-detail",
            password="secret123",
            phone="0900111444",
            role=UserRole.DOCTOR,
        )
        self.patient = Patient.objects.create(full_name="Detail Patient", phone="0900111555")
        self.service = Service.objects.create(
            name="Điều trị tủy",
            price="2200000.00",
            estimated_duration="01:30:00",
        )

    def test_internal_appointment_detail_renders_treatment_and_invoice(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2026, 3, 26),
            time_slot=time(9, 30),
            status=AppointmentStatus.COMPLETED,
        )
        tooth = Tooth.objects.get(patient=self.patient, tooth_number=26)
        tooth.status = ToothStatus.CAVITY
        tooth.save(update_fields=["status", "updated_at"])
        plan = TreatmentPlan.objects.create(
            appointment=appointment,
            diagnosis="Viêm tủy răng 26",
            notes="Đã xử lý và hẹn tái khám.",
            status=TreatmentPlanStatus.COMPLETED,
            resulting_tooth_status=ToothStatus.TREATED,
        )
        plan.services.add(self.service)
        plan.teeth.add(tooth)
        invoice = Invoice.objects.get(treatment_plan=plan)

        self.client.login(username="reception-detail", password="secret123")
        response = self.client.get(reverse("appointment-detail", args=[appointment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hồ sơ điều trị")
        self.assertContains(response, "Viêm tủy răng 26")
        self.assertContains(response, "Điều trị tủy")
        self.assertContains(response, f"Răng {tooth.tooth_number}")
        self.assertContains(response, f"#{invoice.pk}")

    def test_internal_appointment_detail_handles_missing_treatment_and_invoice(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2026, 3, 27),
            time_slot=time(14, 0),
            status=AppointmentStatus.COMPLETED,
        )

        self.client.login(username="reception-detail", password="secret123")
        response = self.client.get(reverse("appointment-detail", args=[appointment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chưa có dữ liệu điều trị cho lịch hẹn này.")
        self.assertContains(response, "Chưa có dữ liệu hóa đơn cho lịch hẹn này.")


class AppointmentListFilterTests(TestCase):
    def setUp(self):
        self.receptionist = CustomUser.objects.create_user(
            username="reception-filter",
            password="secret123",
            phone="0900990001",
            role=UserRole.RECEPTIONIST,
        )
        self.first_doctor = CustomUser.objects.create_user(
            username="doctor-filter-1",
            password="secret123",
            phone="0900990002",
            role=UserRole.DOCTOR,
        )
        self.second_doctor = CustomUser.objects.create_user(
            username="doctor-filter-2",
            password="secret123",
            phone="0900990003",
            role=UserRole.DOCTOR,
        )
        self.first_patient = Patient.objects.create(full_name="Nguyễn Thị Mai", phone="0912000001")
        self.second_patient = Patient.objects.create(full_name="Trần Quốc Bảo", phone="0912000002")

        Appointment.objects.create(
            patient=self.first_patient,
            doctor=self.first_doctor,
            date=date(2026, 3, 20),
            time_slot=time(9, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        Appointment.objects.create(
            patient=self.second_patient,
            doctor=self.second_doctor,
            date=date(2026, 3, 21),
            time_slot=time(10, 0),
            status=AppointmentStatus.CANCELLED,
        )

        self.client.login(username="reception-filter", password="secret123")

    def test_appointment_list_filters_by_doctor_and_status(self):
        response = self.client.get(
            reverse("appointment-list"),
            {"doctor": self.first_doctor.pk, "status": AppointmentStatus.CONFIRMED},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nguyễn Thị Mai")
        self.assertNotContains(response, "Trần Quốc Bảo")

    def test_appointment_list_filters_by_search_keyword(self):
        response = self.client.get(reverse("appointment-list"), {"q": "0912000002"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trần Quốc Bảo")
        self.assertNotContains(response, "Nguyễn Thị Mai")
