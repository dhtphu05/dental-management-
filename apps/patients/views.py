from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole
from apps.patients.forms import PatientForm
from apps.patients.models import Patient


class PatientAccessMixin(RoleRequiredMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)


class PatientListView(PatientAccessMixin, ListView):
    model = Patient
    template_name = "patients/patient_list.html"
    context_object_name = "patients"


class PatientDetailView(PatientAccessMixin, DetailView):
    model = Patient
    template_name = "patients/patient_detail.html"
    context_object_name = "patient"


class PatientCreateView(PatientAccessMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("patient-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Thêm bệnh nhân"
        return context


class PatientUpdateView(PatientAccessMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("patient-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cập nhật bệnh nhân"
        return context


class PatientDeleteView(PatientAccessMixin, DeleteView):
    model = Patient
    template_name = "shared/confirm_delete.html"
    success_url = reverse_lazy("patient-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Xóa bệnh nhân"
        return context
