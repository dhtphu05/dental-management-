from datetime import date, time

from django.contrib.auth import login
from django.shortcuts import redirect
from django.http import QueryDict
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole
from apps.scheduling.account_forms import BookingAccountCreateForm
from apps.scheduling.forms import AppointmentForm, PublicBookingForm
from apps.scheduling.models import Appointment, AppointmentStatus


class AppointmentAccessMixin(RoleRequiredMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)


class BookingSlotMixin:
    SLOT_TIMES = [
        time(8, 0), time(8, 30), time(9, 0), time(9, 30),
        time(10, 0), time(10, 30), time(13, 0), time(13, 30),
        time(14, 0), time(14, 30), time(15, 0), time(15, 30),
    ]

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

    def get_booking_context(self):
        return {
            "slot_times": [slot.strftime("%H:%M") for slot in self.SLOT_TIMES],
            "booked_slots": self.get_booked_slots_lookup(),
            "today": date.today().isoformat(),
            "booking_steps": [
                {"number": 1, "title": "Thong tin", "description": "Khach hang"},
                {"number": 2, "title": "Khung gio", "description": "Chon lich hen"},
                {"number": 3, "title": "Tai khoan", "description": "Tao tai khoan va xac nhan"},
            ],
        }


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


class PublicBookingView(BookingSlotMixin, FormView):
    template_name = "scheduling/booking_page.html"
    form_class = PublicBookingForm
    success_url = reverse_lazy("dashboard")

    def get_initial(self):
        return {"date": date.today().isoformat()}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET" and self.request.GET:
            data = QueryDict("", mutable=True)
            for field in ["full_name", "phone", "doctor", "date", "time_slot", "reason", "notes"]:
                value = self.request.GET.get(field)
                if value:
                    data[field] = value
            if data:
                kwargs["data"] = data
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_booking_context())
        context["page_title"] = "Đặt lịch hẹn"
        context["public_booking"] = True
        form = context.get("form")
        error_step = 1
        if form and form.errors:
            if "time_slot" in form.errors:
                error_step = 2
        context["booking_error_step"] = error_step
        return context

    def form_valid(self, form):
        appointment = form.save()
        self.request.session["just_booked_appointment_id"] = appointment.pk
        return redirect("booking-success")


class BookingSuccessView(DetailView):
    model = Appointment
    template_name = "scheduling/booking_success.html"
    context_object_name = "appointment"

    def get_object(self, queryset=None):
        appointment_id = self.request.session.get("just_booked_appointment_id")
        if not appointment_id:
            return redirect("public-booking")
        return Appointment.objects.select_related("patient", "doctor").get(pk=appointment_id)

    def render_to_response(self, context, **response_kwargs):
        if not isinstance(context.get("appointment"), Appointment):
            return context["appointment"]
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_account"] = self.object.patient.user_id is None
        return context


class BookingAccountCreateView(FormView):
    template_name = "scheduling/booking_account_create.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        appointment_id = request.session.get("just_booked_appointment_id")
        if not appointment_id:
            return redirect("public-booking")
        self.appointment = Appointment.objects.select_related("patient", "doctor").get(pk=appointment_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["patient"] = self.appointment.patient
        return kwargs

    def get_form_class(self):
        return BookingAccountCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["appointment"] = self.appointment
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class AppointmentCreateView(AppointmentAccessMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("appointment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Them lich hen"
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
