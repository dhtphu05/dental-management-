from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import CustomUser, UserRole
from apps.billing.models import Invoice
from apps.clinical.models import Service, Tooth, ToothStatus, TreatmentPlan, TreatmentPlanStatus
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentStatus


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
