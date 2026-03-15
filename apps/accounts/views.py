from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.accounts.models import UserRole
from apps.scheduling.models import Appointment
from apps.billing.models import Invoice
from apps.billing.models import InvoiceStatus
from apps.clinical.models import Service
from apps.patients.models import Patient


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_template_names(self):
        if self.request.user.role == UserRole.DOCTOR:
            return ["doctor_dashboard.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["role"] = user.role

        if user.role == UserRole.PATIENT and hasattr(user, "patient_profile"):
            patient = user.patient_profile
            context["upcoming_appointments"] = patient.appointments.exclude(status="cancelled").order_by("date", "time_slot")[:5]
            context["history"] = patient.appointments.filter(status="completed").select_related("treatment_plan").order_by("-date", "-time_slot")[:10]
        elif user.role == UserRole.DOCTOR:
            today = timezone.localdate()
            doctor_appointments = Appointment.objects.filter(doctor=user).select_related("patient")
            context["upcoming_appointments"] = doctor_appointments.exclude(status="cancelled").order_by("date", "time_slot")[:10]
            context["today_appointments"] = doctor_appointments.filter(date=today).exclude(status="cancelled").order_by("time_slot")
            context["doctor_patient_count"] = Patient.objects.filter(appointments__doctor=user).distinct().count()
            context["doctor_revenue"] = (
                Invoice.objects.filter(
                    treatment_plan__appointment__doctor=user,
                    status__in=[InvoiceStatus.ISSUED, InvoiceStatus.PAID],
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )
            context["today_appointment_count"] = context["today_appointments"].count()
            chart_labels = []
            chart_values = []
            for offset in range(6, -1, -1):
                current_day = today - timedelta(days=offset)
                chart_labels.append(current_day.strftime("%d/%m"))
                chart_values.append(
                    doctor_appointments.filter(date=current_day).exclude(status="cancelled").count()
                )
            context["doctor_chart_labels"] = chart_labels
            context["doctor_chart_values"] = chart_values
            context["today"] = today
        else:
            context["upcoming_appointments"] = Appointment.objects.exclude(status="cancelled").select_related("patient", "doctor").order_by("date", "time_slot")[:10]
            context["patient_count"] = Patient.objects.count()
            context["appointment_count"] = Appointment.objects.count()
            context["service_count"] = Service.objects.count()
            context["invoice_count"] = Invoice.objects.count()

        return context
