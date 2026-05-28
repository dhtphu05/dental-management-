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
                "duration_minutes": "30",
                "description": "Làm sạch mảng bám và đánh bóng răng.",
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

    def test_invoice_detail_view_renders_structured_sections(self):
        patient = Patient.objects.create(full_name="Patient Invoice", phone="0900555555")
        service = Service.objects.create(
            name="Tẩy trắng răng",
            price=Decimal("1200000.00"),
            estimated_duration=timedelta(minutes=90),
        )
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.doctor,
            date=date(2026, 3, 24),
            time_slot=time(15, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        plan = TreatmentPlan.objects.create(
            appointment=appointment,
            diagnosis="Nhiễm màu răng cửa",
            status=TreatmentPlanStatus.COMPLETED,
        )
        plan.services.add(service)
        invoice = Invoice.objects.get(treatment_plan=plan)

        response = self.client.get(reverse("invoice-detail", args=[invoice.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chi tiết dịch vụ")
        self.assertContains(response, "Hồ sơ điều trị liên quan")
        self.assertContains(response, "Tẩy trắng răng")
        self.assertContains(response, "1.200.000 VNĐ")
        self.assertContains(response, "Xuất hóa đơn")

    def test_invoice_list_shows_statistics_cards(self):
        first_patient = Patient.objects.create(full_name="Patient Stats One", phone="0900544444")
        second_patient = Patient.objects.create(full_name="Patient Stats Two", phone="0900533333")
        third_patient = Patient.objects.create(full_name="Patient Stats Three", phone="0900522222")
        service = Service.objects.create(
            name="Điều trị tủy",
            price=Decimal("800000.00"),
            estimated_duration=timedelta(minutes=60),
        )

        first_appointment = Appointment.objects.create(
            patient=first_patient,
            doctor=self.doctor,
            date=date(2026, 3, 25),
            time_slot=time(9, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        second_appointment = Appointment.objects.create(
            patient=second_patient,
            doctor=self.doctor,
            date=date(2026, 3, 26),
            time_slot=time(10, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        third_appointment = Appointment.objects.create(
            patient=third_patient,
            doctor=self.doctor,
            date=date(2026, 3, 27),
            time_slot=time(11, 0),
            status=AppointmentStatus.CONFIRMED,
        )

        first_plan = TreatmentPlan.objects.create(appointment=first_appointment, diagnosis="Viêm tủy")
        second_plan = TreatmentPlan.objects.create(appointment=second_appointment, diagnosis="Khám định kỳ")
        third_plan = TreatmentPlan.objects.create(appointment=third_appointment, diagnosis="Tái khám")
        first_plan.services.add(service)
        second_plan.services.add(service)
        third_plan.services.add(service)

        first_invoice = Invoice.objects.get(treatment_plan=first_plan)
        first_invoice.status = "paid"
        first_invoice.save(update_fields=["status", "updated_at"])

        second_invoice = Invoice.objects.get(treatment_plan=second_plan)
        second_invoice.status = "issued"
        second_invoice.save(update_fields=["status", "updated_at"])

        third_invoice = Invoice.objects.get(treatment_plan=third_plan)
        third_invoice.status = "paid"
        third_invoice.save(update_fields=["status", "updated_at"])

        response = self.client.get(reverse("invoice-list"))

        self.assertEqual(response.status_code, 200)
        paid_stat = next(stat for stat in response.context["invoice_stats"] if stat["label"] == "Đã thanh toán")
        issued_stat = next(stat for stat in response.context["invoice_stats"] if stat["label"] == "Đã phát hành")
        self.assertEqual(paid_stat["value"], 2)
        self.assertEqual(issued_stat["value"], 1)
        self.assertContains(response, "Tổng hóa đơn")
        self.assertContains(response, "Đã thanh toán")
        self.assertContains(response, "Đã phát hành")
        self.assertContains(response, "800.000 VNĐ")
        self.assertContains(response, "Thời gian")

    def test_appointment_pages_link_to_invoice_when_available(self):
        patient = Patient.objects.create(full_name="Patient Link", phone="0900444444")
        service = Service.objects.create(
            name="Nhổ răng khôn",
            price=Decimal("2000000.00"),
            estimated_duration=timedelta(minutes=60),
        )
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.doctor,
            date=date(2026, 3, 26),
            time_slot=time(16, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        plan = TreatmentPlan.objects.create(
            appointment=appointment,
            diagnosis="Răng khôn mọc lệch",
            status=TreatmentPlanStatus.COMPLETED,
        )
        plan.services.add(service)
        invoice = Invoice.objects.get(treatment_plan=plan)

        list_response = self.client.get(reverse("appointment-list"))
        detail_response = self.client.get(reverse("appointment-detail", args=[appointment.pk]))

        self.assertContains(list_response, reverse("invoice-detail", args=[invoice.pk]))
        self.assertContains(detail_response, reverse("invoice-detail", args=[invoice.pk]))

    def test_invoice_list_filters_by_status_and_doctor(self):
        second_doctor = CustomUser.objects.create_user(
            username="doctor-invoice-filter",
            password="secret123",
            phone="0900432123",
            role=UserRole.DOCTOR,
        )
        first_patient = Patient.objects.create(full_name="Patient Filter One", phone="0900411111")
        second_patient = Patient.objects.create(full_name="Patient Filter Two", phone="0900422222")
        service = Service.objects.create(
            name="Trám răng",
            price=Decimal("500000.00"),
            estimated_duration=timedelta(minutes=45),
        )

        first_appointment = Appointment.objects.create(
            patient=first_patient,
            doctor=self.doctor,
            date=date(2026, 3, 24),
            time_slot=time(8, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        second_appointment = Appointment.objects.create(
            patient=second_patient,
            doctor=second_doctor,
            date=date(2026, 3, 24),
            time_slot=time(9, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        first_plan = TreatmentPlan.objects.create(appointment=first_appointment, diagnosis="Mẻ răng")
        second_plan = TreatmentPlan.objects.create(appointment=second_appointment, diagnosis="Sâu răng")
        first_plan.services.add(service)
        second_plan.services.add(service)
        first_invoice = Invoice.objects.get(treatment_plan=first_plan)
        second_invoice = Invoice.objects.get(treatment_plan=second_plan)
        first_invoice.status = "paid"
        first_invoice.save(update_fields=["status", "updated_at"])
        second_invoice.status = "issued"
        second_invoice.save(update_fields=["status", "updated_at"])

        response = self.client.get(
            reverse("invoice-list"),
            {"doctor": self.doctor.pk, "status": "paid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Patient Filter One")
        self.assertNotContains(response, "Patient Filter Two")

    def test_invoice_list_filters_by_search_keyword(self):
        patient = Patient.objects.create(full_name="Lê Hoàng Nam", phone="0900400000")
        service = Service.objects.create(
            name="Cạo vôi răng",
            price=Decimal("250000.00"),
            estimated_duration=timedelta(minutes=30),
        )
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.doctor,
            date=date(2026, 3, 24),
            time_slot=time(10, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        plan = TreatmentPlan.objects.create(appointment=appointment, diagnosis="Khám định kỳ")
        plan.services.add(service)

        response = self.client.get(reverse("invoice-list"), {"q": "0900400000"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lê Hoàng Nam")

    def test_receptionist_can_open_treatment_plan_from_appointment(self):
        patient = Patient.objects.create(full_name="Patient Service", phone="0900333444")
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.doctor,
            date=date(2026, 3, 27),
            time_slot=time(10, 30),
            status=AppointmentStatus.PENDING,
        )

        response = self.client.get(reverse("doctor-treatment-plan", args=[appointment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cập nhật dịch vụ và liệu trình")
        self.assertContains(response, "Lưu dịch vụ và liệu trình")

    def test_appointment_list_shows_add_service_action_for_receptionist(self):
        patient = Patient.objects.create(full_name="Patient Queue", phone="0900222111")
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.doctor,
            date=date(2026, 3, 28),
            time_slot=time(11, 0),
            status=AppointmentStatus.CONFIRMED,
        )

        response = self.client.get(reverse("appointment-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("doctor-treatment-plan", args=[appointment.pk]))
        self.assertContains(response, "Thêm dịch vụ")

    def test_receptionist_can_generate_invoice_from_appointment(self):
        patient = Patient.objects.create(full_name="Patient Invoice Flow", phone="0900111222")
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.doctor,
            date=date(2026, 3, 29),
            time_slot=time(14, 30),
            status=AppointmentStatus.CONFIRMED,
        )

        response = self.client.get(reverse("invoice-generate", args=[appointment.pk]))

        treatment_plan = TreatmentPlan.objects.get(appointment=appointment)
        invoice = Invoice.objects.get(treatment_plan=treatment_plan)
        self.assertRedirects(response, reverse("invoice-detail", args=[invoice.pk]))


class LandingPageTests(TestCase):
    def test_homepage_is_public_and_has_booking_and_login_actions(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phòng khám Thiên Phú")
        self.assertContains(response, reverse("public-booking"))
        self.assertContains(response, reverse("login"))
        self.assertContains(response, reverse("patient-register"))


class PatientRegistrationFlowTests(TestCase):
    def test_register_page_is_public(self):
        response = self.client.get(reverse("patient-register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Đăng ký bệnh nhân")

    def test_patient_can_register_and_is_logged_in(self):
        response = self.client.post(
            reverse("patient-register"),
            {
                "full_name": "Đoàn Hoàng Thiên Phú",
                "phone": "0385544194",
                "password1": "Dental@123",
                "password2": "Dental@123",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        user = CustomUser.objects.get(phone="0385544194")
        patient = Patient.objects.get(phone="0385544194")
        self.assertEqual(user.role, UserRole.PATIENT)
        self.assertEqual(user.username, "0385544194")
        self.assertEqual(patient.user, user)
        self.assertEqual(patient.full_name, "Đoàn Hoàng Thiên Phú")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_patient_cannot_register_with_existing_patient_phone(self):
        CustomUser.objects.create_user(
            username="0912111222",
            password="secret123",
            phone="0912111222",
            role=UserRole.PATIENT,
        )

        response = self.client.post(
            reverse("patient-register"),
            {
                "full_name": "Bệnh nhân trùng số",
                "phone": "0912111222",
                "password1": "Dental@123",
                "password2": "Dental@123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Số điện thoại này đã có tài khoản bệnh nhân.")

    def test_patient_registration_rejects_invalid_full_name(self):
        response = self.client.post(
            reverse("patient-register"),
            {
                "full_name": "1234",
                "phone": "0912345678",
                "password1": "Dental@123",
                "password2": "Dental@123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Họ và tên chỉ được chứa chữ cái và khoảng trắng hợp lệ.")

    def test_patient_registration_rejects_invalid_phone(self):
        response = self.client.post(
            reverse("patient-register"),
            {
                "full_name": "Nguyễn Văn A",
                "phone": "03855abc94",
                "password1": "Dental@123",
                "password2": "Dental@123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Số điện thoại chỉ được chứa chữ số.")

    def test_patient_registration_rejects_weak_password(self):
        response = self.client.post(
            reverse("patient-register"),
            {
                "full_name": "Nguyễn Văn A",
                "phone": "0912345678",
                "password1": "12345678",
                "password2": "12345678",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mật khẩu không được chỉ gồm chữ số.")

    def test_patient_cannot_register_with_internal_staff_phone(self):
        CustomUser.objects.create_user(
            username="doctor-existing",
            password="secret123",
            phone="0900123456",
            role=UserRole.DOCTOR,
        )

        response = self.client.post(
            reverse("patient-register"),
            {
                "full_name": "Bệnh nhân mới",
                "phone": "0900123456",
                "password1": "Dental@123",
                "password2": "Dental@123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Số điện thoại này đang được dùng cho tài khoản nội bộ.")


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

    def test_authenticated_patient_booking_prefills_name_and_phone(self):
        self.client.login(username="0912999888", password="secret123")

        response = self.client.get(reverse("public-booking"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Patient History"')
        self.assertContains(response, 'value="0912999888"')

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

    def test_patient_can_view_own_teeth_status_page(self):
        crown_tooth = Tooth.objects.get(patient=self.patient, tooth_number=21)
        crown_tooth.status = ToothStatus.CROWN
        crown_tooth.notes = "Răng sứ thẩm mỹ"
        crown_tooth.save(update_fields=["status", "notes", "updated_at"])

        self.client.login(username="0912999888", password="secret123")
        response = self.client.get(reverse("patient-teeth"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tình trạng răng của bạn")
        self.assertContains(response, "Răng sứ")
        self.assertContains(response, "21")
        self.assertContains(response, "Răng sứ thẩm mỹ")

    def test_non_patient_cannot_view_patient_teeth_page(self):
        receptionist = CustomUser.objects.create_user(
            username="reception-teeth",
            password="secret123",
            phone="0900666000",
            role=UserRole.RECEPTIONIST,
        )
        self.client.login(username="reception-teeth", password="secret123")

        response = self.client.get(reverse("patient-teeth"))

        self.assertEqual(response.status_code, 403)
