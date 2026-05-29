from datetime import date, time

from django.contrib.auth import login
from django.shortcuts import redirect
from django.http import QueryDict
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView, TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import CustomUser, UserRole
from apps.scheduling.account_forms import BookingAccountCreateForm
from apps.scheduling.forms import AppointmentForm, SidebarAppointmentForm, PublicBookingForm
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
        doctor_ids = list(
            PublicBookingForm.base_fields["doctor"].queryset.values_list("id", flat=True)
        )
        return {
            "slot_times": [slot.strftime("%H:%M") for slot in self.SLOT_TIMES],
            "booked_slots": self.get_booked_slots_lookup(),
            "doctor_ids": [str(doctor_id) for doctor_id in doctor_ids],
            "today": date.today().isoformat(),
            "booking_steps": [
                {"number": 1, "title": "Thông tin", "description": "Khách hàng"},
                {"number": 2, "title": "Khung giờ", "description": "Chọn lịch hẹn"},
                {"number": 3, "title": "Xác nhận", "description": "Kiểm tra trước khi gửi"},
            ],
        }


class AppointmentListView(AppointmentAccessMixin, ListView):
    model = Appointment
    template_name = "scheduling/appointment_list.html"
    context_object_name = "appointments"

    def get_queryset(self):
        queryset = (
            Appointment.objects.select_related(
                "patient",
                "doctor",
                "treatment_plan",
                "treatment_plan__invoice",
            )
            .order_by("-date", "-time_slot")
        )
        search = (self.request.GET.get("q") or "").strip()
        doctor_id = self.request.GET.get("doctor")
        status = self.request.GET.get("status")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if search:
            queryset = queryset.filter(
                Q(patient__full_name__icontains=search)
                | Q(patient__phone__icontains=search)
            )
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctors = CustomUser.objects.filter(role=UserRole.DOCTOR).order_by(
            "first_name", "last_name", "username"
        )
        DOCTOR_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#eab308", "#14b8a6", "#06b6d4", "#6366f1", "#10b981", "#ef4444"]
        
        doctor_info = []
        for doc in doctors:
            color = DOCTOR_COLORS[doc.id % len(DOCTOR_COLORS)]
            doctor_info.append({
                "id": doc.id,
                "name": f"BS. {doc.last_name} {doc.first_name}".strip() if doc.first_name else doc.username,
                "color": color
            })
        context["doctor_options"] = doctor_info
        context["status_options"] = AppointmentStatus.choices
        context["active_filters"] = {
            "q": self.request.GET.get("q", ""),
            "doctor": self.request.GET.get("doctor", ""),
            "status": self.request.GET.get("status", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
        }
        context["active_filter_count"] = sum(1 for value in context["active_filters"].values() if value)
        context["appointment_result_count"] = context["appointments"].count()
        return context


class AppointmentDetailView(AppointmentAccessMixin, DetailView):
    model = Appointment
    template_name = "scheduling/appointment_detail.html"
    context_object_name = "appointment"

    def get_queryset(self):
        return Appointment.objects.select_related(
            "patient",
            "doctor",
            "treatment_plan",
            "treatment_plan__invoice",
        ).prefetch_related(
            "treatment_plan__services",
            "treatment_plan__teeth",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        treatment_plan = getattr(self.object, "treatment_plan", None)
        invoice = getattr(treatment_plan, "invoice", None) if treatment_plan else None
        context["treatment_plan"] = treatment_plan
        context["invoice"] = invoice
        return context


class PublicBookingView(BookingSlotMixin, FormView):
    template_name = "scheduling/booking_page.html"
    form_class = PublicBookingForm
    success_url = reverse_lazy("dashboard")

    def get_patient_prefill(self):
        if not self.request.user.is_authenticated or self.request.user.role != UserRole.PATIENT:
            return {}

        patient = getattr(self.request.user, "patient_profile", None)
        if patient is None:
            return {}

        return {
            "full_name": patient.full_name,
            "phone": patient.phone,
        }

    def get_initial(self):
        initial = {"date": date.today().isoformat()}
        initial.update(self.get_patient_prefill())
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET":
            initial = kwargs.get("initial", {}).copy()
            for field, value in self.get_patient_prefill().items():
                if value:
                    initial[field] = value
            for field in ["full_name", "phone", "doctor", "date", "time_slot", "reason", "notes"]:
                value = self.request.GET.get(field)
                if value:
                    initial[field] = value
            if initial:
                kwargs["initial"] = initial
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_booking_context())
        context["page_title"] = "Đặt lịch hẹn"
        context["public_booking"] = True
        form = context.get("form")
        error_step = 1
        if self.request.method == "POST" and form and form.errors:
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

    def get_initial(self):
        initial = super().get_initial()
        # Parse query params like ?date=2026-05-28&time=14:30
        if self.request.GET.get('date'):
            initial['date'] = self.request.GET.get('date')
        if self.request.GET.get('time'):
            # Convert simple time string if needed, or stick to what the form expects
            initial['time_slot'] = self.request.GET.get('time')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Thêm lịch hẹn"
        return context

class AppointmentUpdateView(AppointmentAccessMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("appointment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cập nhật lịch hẹn"
        return context


class AppointmentDeleteView(AppointmentAccessMixin, DeleteView):
    model = Appointment
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("appointment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Xóa lịch hẹn"
        return context


class AppointmentCalendarView(AppointmentAccessMixin, TemplateView):
    template_name = "scheduling/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Lịch tuần"
        doctors = CustomUser.objects.filter(role=UserRole.DOCTOR).order_by(
            "first_name", "last_name", "username"
        )
        DOCTOR_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#eab308", "#14b8a6", "#06b6d4", "#6366f1", "#10b981", "#ef4444"]
        
        doctor_info = []
        for doc in doctors:
            color = DOCTOR_COLORS[doc.id % len(DOCTOR_COLORS)]
            doctor_info.append({
                "id": doc.id,
                "name": f"BS. {doc.last_name} {doc.first_name}".strip() if doc.first_name else doc.username,
                "color": color
            })
        context["doctor_options"] = doctor_info
        from apps.scheduling.forms import AppointmentForm, SidebarAppointmentForm
        # Provide an empty form for the sidebar
        context["form"] = SidebarAppointmentForm()
        return context

