from datetime import datetime, timedelta
from decimal import Decimal

from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole
from apps.clinical.forms import ServiceForm, TreatmentPlanForm
from apps.clinical.models import Service, ToothStatus, TreatmentPlan
from apps.scheduling.models import Appointment


class ServiceAccessMixin(RoleRequiredMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)


class ServiceListView(ServiceAccessMixin, ListView):
    model = Service
    template_name = "clinical/service_list.html"
    context_object_name = "services"


class ServiceCreateView(ServiceAccessMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("service-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Thêm dịch vụ"
        context["page_subtitle"] = "Thiết lập tên dịch vụ, đơn giá và thời gian thực hiện theo cách bệnh nhân dễ hiểu."
        context["form_variant"] = "service"
        return context


class ServiceUpdateView(ServiceAccessMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("service-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cập nhật dịch vụ"
        context["page_subtitle"] = "Điều chỉnh thông tin dịch vụ đang áp dụng tại phòng khám."
        context["form_variant"] = "service"
        return context


class ServiceDeleteView(ServiceAccessMixin, DeleteView):
    model = Service
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("service-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Xóa dịch vụ"
        return context


class DoctorTreatmentPlanUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.ADMIN)
    model = TreatmentPlan
    form_class = TreatmentPlanForm
    template_name = "clinical/treatment_plan_form.html"

    def get_object(self, queryset=None):
        appointment_queryset = Appointment.objects.select_related("patient", "doctor")
        filters = {"pk": self.kwargs["appointment_id"]}
        if self.request.user.role == UserRole.DOCTOR:
            filters["doctor"] = self.request.user
        appointment = get_object_or_404(appointment_queryset, **filters)
        treatment_plan, _ = TreatmentPlan.objects.get_or_create(
            appointment=appointment,
            defaults={"diagnosis": "Chưa có chẩn đoán."},
        )
        return treatment_plan

    def get_success_url(self):
        from django.urls import reverse
        return reverse("appointment-detail", kwargs={"pk": self.object.appointment.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teeth = list(self.object.appointment.patient.teeth.order_by("tooth_number"))
        appointment_start = datetime.combine(self.object.appointment.date, self.object.appointment.time_slot)
        selected_service_ids = {
            str(service_id) for service_id in self.object.services.values_list("id", flat=True)
        }
        if self.request.method == "POST":
            selected_service_ids = set(self.request.POST.getlist("services"))
        context["odontogram_sections"] = [
            {"label": "Cung hàm trên phải", "teeth": [tooth for tooth in teeth if 11 <= tooth.tooth_number <= 18]},
            {"label": "Cung hàm trên trái", "teeth": [tooth for tooth in teeth if 21 <= tooth.tooth_number <= 28]},
            {"label": "Cung hàm dưới trái", "teeth": [tooth for tooth in teeth if 31 <= tooth.tooth_number <= 38]},
            {"label": "Cung hàm dưới phải", "teeth": [tooth for tooth in teeth if 41 <= tooth.tooth_number <= 48]},
        ]
        context["tooth_state_options"] = [
            {"value": ToothStatus.CAVITY, "label": "Sâu răng"},
            {"value": ToothStatus.TREATED, "label": "Trám"},
            {"value": ToothStatus.MISSING, "label": "Nhổ"},
            {"value": ToothStatus.NORMAL, "label": "Bình thường"},
        ]
        context["tooth_status_labels"] = dict(ToothStatus.choices)
        context["tooth_states_data"] = (
            {
                str(tooth.pk): {
                    "status": tooth.status,
                    "number": tooth.tooth_number,
                }
                for tooth in teeth
            }
        )
        context["service_cards"] = [
            {
                "id": str(service.pk),
                "name": service.name,
                "description": service.description,
                "price": service.price,
                "duration": service.estimated_duration,
                "duration_minutes": int(service.estimated_duration.total_seconds() // 60),
                "estimated_end": (appointment_start + service.estimated_duration).time().replace(second=0, microsecond=0),
                "checked": str(service.pk) in selected_service_ids,
            }
            for service in self.form_class.base_fields["services"].queryset.order_by("name")
        ]
        initial_total_duration = sum(
            (card["duration"] for card in context["service_cards"] if card["checked"]),
            timedelta(),
        )
        context["selected_services_count"] = sum(1 for card in context["service_cards"] if card["checked"])
        context["selected_services_total"] = sum(
            (card["price"] for card in context["service_cards"] if card["checked"]),
            Decimal("0"),
        )
        context["selected_services_duration"] = initial_total_duration
        context["estimated_finish_time"] = (
            (appointment_start + initial_total_duration).time().replace(second=0, microsecond=0)
            if initial_total_duration
            else self.object.appointment.time_slot
        )
        context["is_clinical_staff"] = self.request.user.role in {UserRole.RECEPTIONIST, UserRole.ADMIN}
        return context
