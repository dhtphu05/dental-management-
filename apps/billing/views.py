from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole
from apps.billing.forms import InvoiceForm
from apps.billing.models import Invoice


class InvoiceAccessMixin(RoleRequiredMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)


class InvoiceListView(InvoiceAccessMixin, ListView):
    model = Invoice
    template_name = "billing/invoice_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        return Invoice.objects.select_related(
            "treatment_plan__appointment__patient",
            "treatment_plan__appointment__doctor",
        ).order_by("-issued_at")


class InvoiceDetailView(InvoiceAccessMixin, DetailView):
    model = Invoice
    template_name = "billing/invoice_detail.html"
    context_object_name = "invoice"


class InvoiceUpdateView(InvoiceAccessMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("invoice-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cap nhat hoa don"
        return context


class InvoiceDeleteView(InvoiceAccessMixin, DeleteView):
    model = Invoice
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("invoice-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Xoa hoa don"
        return context
