from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import CustomUser, UserRole
from apps.accounts.templatetags.currency import duration_vi, vi_date, vi_date_long, vi_datetime, vi_time
from apps.billing.models import Invoice
from apps.clinical.forms import ServiceForm
from apps.clinical.models import Service, Tooth, ToothStatus, TreatmentPlan, TreatmentPlanStatus
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentStatus


class ServiceFormTests(TestCase):
    def test_duration_filter_formats_minutes_and_hours(self):
        self.assertEqual(duration_vi(timedelta(minutes=30)), "30 phút")
        self.assertEqual(duration_vi(timedelta(minutes=90)), "1 giờ 30 phút")

    def test_vietnamese_date_and_time_filters(self):
        self.assertEqual(vi_date(date(2026, 3, 17)), "17/03/2026")
        self.assertEqual(vi_date_long(date(2026, 3, 17)), "Thứ ba, 17/03/2026")
        self.assertEqual(vi_time(time(9, 30)), "09:30")
        self.assertEqual(vi_datetime(datetime(2026, 3, 17, 9, 30)), "17/03/2026 09:30")

    def test_service_form_saves_duration_from_minutes(self):
        form = ServiceForm(
            data={
                "name": "Cạo vôi răng",
                "price": "300000",
                "duration_minutes": "45",
                "description": "Làm sạch mảng bám và đánh bóng bề mặt răng.",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        service = form.save()

        self.assertEqual(service.estimated_duration, timedelta(minutes=45))

    def test_service_form_rejects_duplicate_name_case_insensitive(self):
        Service.objects.create(
            name="Cạo vôi răng",
            price=Decimal("300000.00"),
            estimated_duration=timedelta(minutes=30),
        )

        form = ServiceForm(
            data={
                "name": "  cạo vôi răng  ",
                "price": "350000",
                "duration_minutes": "40",
                "description": "Mô tả dịch vụ đủ dài để hợp lệ.",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Tên dịch vụ này đã tồn tại.", form.errors["name"])

    def test_service_form_rejects_invalid_price_and_short_description(self):
        form = ServiceForm(
            data={
                "name": "Trám răng",
                "price": "0",
                "duration_minutes": "10",
                "description": "Quá ngắn",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Giá dịch vụ phải lớn hơn 0.", form.errors["price"])
        self.assertIn("Mô tả nên có ít nhất 10 ký tự hoặc để trống.", form.errors["description"])


class TreatmentPlanAutomationTests(TestCase):
    def setUp(self):
        self.doctor = CustomUser.objects.create_user(
            username="doctor1",
            password="secret123",
            phone="0900000100",
            role=UserRole.DOCTOR,
        )
        self.patient = Patient.objects.create(full_name="Patient One", phone="0900000101")
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2026, 3, 22),
            time_slot=time(10, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        self.tooth = Tooth.objects.get(patient=self.patient, tooth_number=11)
        self.tooth.status = ToothStatus.CAVITY
        self.tooth.save(update_fields=["status"])
        self.service = Service.objects.create(
            name="Tram rang",
            price=Decimal("500000.00"),
            estimated_duration=timedelta(minutes=45),
        )

    def test_patient_gets_default_odontogram(self):
        self.assertEqual(Tooth.objects.filter(patient=self.patient).count(), 32)

    def test_completed_treatment_updates_tooth_and_invoice(self):
        plan = TreatmentPlan.objects.create(
            appointment=self.appointment,
            diagnosis="Sau rang",
            status=TreatmentPlanStatus.PLANNED,
            resulting_tooth_status=ToothStatus.TREATED,
        )
        plan.teeth.add(self.tooth)
        plan.services.add(self.service)

        plan.status = TreatmentPlanStatus.COMPLETED
        plan.save()

        self.tooth.refresh_from_db()
        self.appointment.refresh_from_db()
        invoice = Invoice.objects.get(treatment_plan=plan)

        self.assertEqual(self.tooth.status, ToothStatus.TREATED)
        self.assertEqual(self.appointment.status, AppointmentStatus.COMPLETED)
        self.assertEqual(invoice.total_amount, Decimal("500000.00"))
        self.assertEqual(invoice.status, "issued")
