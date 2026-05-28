from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import CustomUser, UserRole
from apps.billing.forms import InvoiceForm
from apps.billing.models import Invoice, InvoiceStatus
from apps.clinical.models import TreatmentPlan, TreatmentPlanStatus
from apps.scheduling.models import Appointment


class InvoiceAccessMixin(RoleRequiredMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)


class InvoiceListView(InvoiceAccessMixin, ListView):
    model = Invoice
    template_name = "billing/invoice_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        queryset = Invoice.objects.select_related(
            "treatment_plan__appointment__patient",
            "treatment_plan__appointment__doctor",
        ).order_by("-issued_at")
        search = (self.request.GET.get("q") or "").strip()
        doctor_id = self.request.GET.get("doctor")
        status = self.request.GET.get("status")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if search:
            queryset = queryset.filter(
                Q(treatment_plan__appointment__patient__full_name__icontains=search)
                | Q(treatment_plan__appointment__patient__phone__icontains=search)
            )
        if doctor_id:
            queryset = queryset.filter(treatment_plan__appointment__doctor_id=doctor_id)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(issued_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issued_at__date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_queryset = self.get_queryset()
        status_counts = {
            row["status"]: row["count"]
            for row in invoice_queryset.order_by().values("status").annotate(count=Count("id"))
        }
        paid_total = (
            invoice_queryset.filter(status="paid").aggregate(total=Sum("total_amount"))["total"] or 0
        )
        issued_total = (
            invoice_queryset.exclude(status="draft").aggregate(total=Sum("total_amount"))["total"] or 0
        )
        context["invoice_stats"] = [
            {
                "label": "Tổng hóa đơn",
                "value": invoice_queryset.count(),
                "icon": "receipt-text",
                "tone": "Tất cả",
            },
            {
                "label": "Bản nháp",
                "value": status_counts.get("draft", 0),
                "icon": "file-clock",
                "tone": "Chờ xử lý",
            },
            {
                "label": "Đã phát hành",
                "value": status_counts.get("issued", 0),
                "icon": "files",
                "tone": "Sẵn sàng thu",
            },
            {
                "label": "Đã thanh toán",
                "value": status_counts.get("paid", 0),
                "icon": "badge-check",
                "tone": "Hoàn tất",
            },
        ]
        context["invoice_totals"] = {
            "paid_total": paid_total,
            "issued_total": issued_total,
        }
        context["doctor_options"] = CustomUser.objects.filter(role=UserRole.DOCTOR).order_by(
            "first_name", "last_name", "username"
        )
        context["status_options"] = InvoiceStatus.choices
        context["active_filters"] = {
            "q": self.request.GET.get("q", ""),
            "doctor": self.request.GET.get("doctor", ""),
            "status": self.request.GET.get("status", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
        }
        context["active_filter_count"] = sum(1 for value in context["active_filters"].values() if value)
        context["invoice_result_count"] = invoice_queryset.count()
        return context


class InvoiceDetailView(InvoiceAccessMixin, DetailView):
    model = Invoice
    template_name = "billing/invoice_detail.html"
    context_object_name = "invoice"

    def get_queryset(self):
        return Invoice.objects.select_related(
            "treatment_plan__appointment__patient",
            "treatment_plan__appointment__doctor",
        ).prefetch_related(
            "treatment_plan__services",
            "treatment_plan__teeth",
        )


class InvoiceGenerateView(RoleRequiredMixin, View):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST)

    def get(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment.objects.select_related("patient", "doctor"),
            pk=appointment_id,
        )
        treatment_plan, _ = TreatmentPlan.objects.get_or_create(
            appointment=appointment,
            defaults={"diagnosis": "Chưa có chẩn đoán."},
        )
        invoice, _ = Invoice.objects.get_or_create(treatment_plan=treatment_plan)
        invoice.total_amount = sum(service.price for service in treatment_plan.services.all())
        if treatment_plan.status == TreatmentPlanStatus.COMPLETED:
            invoice.status = "issued"
        invoice.save()
        return redirect("invoice-detail", pk=invoice.pk)


class InvoiceUpdateView(InvoiceAccessMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("invoice-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cập nhật hóa đơn"
        return context


class InvoiceDeleteView(InvoiceAccessMixin, DeleteView):
    model = Invoice
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("invoice-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Xóa hóa đơn"
        return context
