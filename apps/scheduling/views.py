from datetime import date, time

from django.http import QueryDict
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole
from apps.scheduling.forms import AppointmentForm, BookingAppointmentForm
from apps.scheduling.models import Appointment, AppointmentStatus


class AppointmentAccessMixin(RoleRequiredMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)


class AppointmentListView(AppointmentAccessMixin, ListView):
    model = Appointment
    template_name = "scheduling/appointment_list.html"
    context_object_name = "appointments"

    def get_queryset(self):
        return (
            Appointment.objects.select_related("patient", "doctor")
            .order_by("-date", "-time_slot")
        )


class AppointmentDetailView(AppointmentAccessMixin, DetailView):
    model = Appointment
    template_name = "scheduling/appointment_detail.html"
    context_object_name = "appointment"


class AppointmentCreateView(AppointmentAccessMixin, CreateView):
    model = Appointment
    form_class = BookingAppointmentForm
    template_name = "scheduling/booking_page.html"
    success_url = reverse_lazy("appointment-list")

    SLOT_TIMES = [
        time(8, 0), time(8, 30), time(9, 0), time(9, 30),
        time(10, 0), time(10, 30), time(13, 0), time(13, 30),
        time(14, 0), time(14, 30), time(15, 0), time(15, 30),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Them lich hen"
        context["slot_times"] = [slot.strftime("%H:%M") for slot in self.SLOT_TIMES]
        context["booked_slots"] = self.get_booked_slots_lookup()
        context["today"] = date.today().isoformat()
        context["booking_steps"] = [
            {"number": 1, "title": "Thong tin", "description": "Benh nhan va bac si"},
            {"number": 2, "title": "Khung gio", "description": "Chon ngay va slot"},
            {"number": 3, "title": "Xac nhan", "description": "Kiem tra lan cuoi"},
        ]
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["date"] = date.today().isoformat()
        patient_id = self.request.GET.get("patient")
        if patient_id:
            initial["patient"] = patient_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET" and self.request.GET:
            data = QueryDict("", mutable=True)
            for field in ["patient", "doctor", "date", "time_slot", "reason", "notes"]:
                value = self.request.GET.get(field)
                if value:
                    data[field] = value
            if data:
                kwargs["data"] = data
        return kwargs

    def form_valid(self, form):
        form.instance.status = AppointmentStatus.PENDING
        return super().form_valid(form)

    def get_booked_slots_lookup(self):
        lookup = {}
        appointments = Appointment.objects.exclude(status=AppointmentStatus.CANCELLED).values(
            "doctor_id", "date", "time_slot"
        )
        for appointment in appointments:
            doctor_id = str(appointment["doctor_id"])
            appointment_date = appointment["date"].isoformat()
            slot = appointment["time_slot"].strftime("%H:%M")
            lookup.setdefault(doctor_id, {}).setdefault(appointment_date, []).append(slot)
        return lookup


class AppointmentUpdateView(AppointmentAccessMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("appointment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cap nhat lich hen"
        return context


class AppointmentDeleteView(AppointmentAccessMixin, DeleteView):
    model = Appointment
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("appointment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Xoa lich hen"
        return context
