from datetime import timedelta

from django.db.models import Sum
from django.contrib.auth import login
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.accounts.forms import PatientRegistrationForm
from apps.accounts.backends import UsernameOrPatientPhoneBackend
from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import CustomUser, UserRole
from apps.billing.models import Invoice
from apps.billing.models import InvoiceStatus
from apps.clinical.models import Service, Tooth, ToothStatus
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentStatus


def appointment_record_queryset():
    return Appointment.objects.select_related(
        "patient",
        "doctor",
        "treatment_plan",
        "treatment_plan__invoice",
    ).prefetch_related(
        "treatment_plan__services",
        "treatment_plan__teeth",
    )


def attach_record_payload(appointments):
    payload = []
    for appointment in appointments:
        treatment_plan = getattr(appointment, "treatment_plan", None)
        invoice = getattr(treatment_plan, "invoice", None) if treatment_plan else None
        payload.append(
            {
                "appointment": appointment,
                "treatment_plan": treatment_plan,
                "invoice": invoice,
            }
        )
    return payload


def build_odontogram_sections(patient):
    teeth_by_number = {tooth.tooth_number: tooth for tooth in patient.teeth.all()}
    section_map = [
        ("Cung hàm trên bên phải", [11, 12, 13, 14, 15, 16, 17, 18]),
        ("Cung hàm trên bên trái", [21, 22, 23, 24, 25, 26, 27, 28]),
        ("Cung hàm dưới bên trái", [31, 32, 33, 34, 35, 36, 37, 38]),
        ("Cung hàm dưới bên phải", [41, 42, 43, 44, 45, 46, 47, 48]),
    ]
    return [
        {
            "label": label,
            "teeth": [teeth_by_number[number] for number in numbers if number in teeth_by_number],
        }
        for label, numbers in section_map
    ]


class LandingPageView(TemplateView):
    template_name = "landing_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["doctor_count"] = CustomUser.objects.filter(role=UserRole.DOCTOR).count()
        context["service_count"] = Service.objects.count()
        context["patient_count"] = Patient.objects.count()
        context["featured_services"] = Service.objects.order_by("name")[:4]
        return context


class PatientRegisterView(FormView):
    template_name = "registration/register.html"
    form_class = PatientRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend=f"{UsernameOrPatientPhoneBackend.__module__}.{UsernameOrPatientPhoneBackend.__name__}")
        return redirect("dashboard")


class DashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR, UserRole.PATIENT)
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
            records = appointment_record_queryset().filter(patient=patient)
            context["upcoming_appointments"] = records.exclude(status=AppointmentStatus.CANCELLED).order_by("date", "time_slot")[:5]
            context["history"] = attach_record_payload(
                records.filter(status=AppointmentStatus.COMPLETED).order_by("-date", "-time_slot")[:4]
            )
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


class PatientHistoryView(RoleRequiredMixin, ListView):
    allowed_roles = (UserRole.PATIENT,)
    template_name = "accounts/patient_history.html"
    context_object_name = "appointments"
    paginate_by = 5

    def get_queryset(self):
        queryset = (
            appointment_record_queryset()
            .filter(
                patient=self.request.user.patient_profile,
                status=AppointmentStatus.COMPLETED,
            )
            .order_by("-date", "-time_slot")
        )
        doctor_id = self.request.GET.get("doctor")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        invoice_status = self.request.GET.get("invoice_status")

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if invoice_status == "none":
            queryset = queryset.filter(treatment_plan__invoice__isnull=True)
        elif invoice_status:
            queryset = queryset.filter(treatment_plan__invoice__status=invoice_status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["records"] = attach_record_payload(context["appointments"])
        patient = self.request.user.patient_profile
        context["doctor_options"] = (
            CustomUser.objects.filter(
                doctor_appointments__patient=patient,
                doctor_appointments__status=AppointmentStatus.COMPLETED,
            )
            .distinct()
            .order_by("first_name", "last_name", "username")
        )
        context["invoice_status_options"] = [
            ("draft", "Bản nháp"),
            ("issued", "Đã phát hành"),
            ("paid", "Đã thanh toán"),
            ("none", "Chưa có hóa đơn"),
        ]
        context["active_filters"] = {
            "doctor": self.request.GET.get("doctor", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "invoice_status": self.request.GET.get("invoice_status", ""),
        }
        active_filter_count = sum(1 for value in context["active_filters"].values() if value)
        context["active_filter_count"] = active_filter_count
        query_string = self.request.GET.copy()
        query_string.pop("page", None)
        context["pagination_query"] = query_string.urlencode()
        return context


class PatientAppointmentDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = (UserRole.PATIENT,)
    template_name = "accounts/patient_appointment_detail.html"
    context_object_name = "appointment"

    def get_queryset(self):
        return (
            appointment_record_queryset()
            .filter(
                patient=self.request.user.patient_profile,
                status=AppointmentStatus.COMPLETED,
            )
            .order_by("-date", "-time_slot")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        treatment_plan = getattr(self.object, "treatment_plan", None)
        invoice = getattr(treatment_plan, "invoice", None) if treatment_plan else None
        context["treatment_plan"] = treatment_plan
        context["invoice"] = invoice
        return context


class PatientTeethView(RoleRequiredMixin, TemplateView):
    allowed_roles = (UserRole.PATIENT, UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.ADMIN)
    template_name = "accounts/patient_teeth.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == UserRole.PATIENT:
            patient = self.request.user.patient_profile
        else:
            patient_id = self.request.GET.get("patient_id")
            patient = get_object_or_404(Patient, pk=patient_id)
            
        teeth = patient.teeth.select_related('last_updated_by').all()
        context["patient"] = patient
        context["odontogram_sections"] = build_odontogram_sections(patient)
        context["tooth_status_summary"] = [
            {
                "label": ToothStatus.NORMAL.label,
                "value": teeth.filter(status=ToothStatus.NORMAL).count(),
                "class_name": "bg-slate-100 text-slate-600",
            },
            {
                "label": ToothStatus.CAVITY.label,
                "value": teeth.filter(status=ToothStatus.CAVITY).count(),
                "class_name": "bg-rose-100 text-rose-600",
            },
            {
                "label": ToothStatus.TREATED.label,
                "value": teeth.filter(status=ToothStatus.TREATED).count(),
                "class_name": "bg-sky-100 text-sky-600",
            },
            {
                "label": ToothStatus.MISSING.label,
                "value": teeth.filter(status=ToothStatus.MISSING).count(),
                "class_name": "bg-slate-200 text-slate-600",
            },
            {
                "label": ToothStatus.CROWN.label,
                "value": teeth.filter(status=ToothStatus.CROWN).count(),
                "class_name": "bg-amber-100 text-amber-700",
            },
        ]
        context["last_tooth_update"] = teeth.order_by("-updated_at").first()
        return context
