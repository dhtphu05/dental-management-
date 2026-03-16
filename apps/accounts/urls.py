from django.urls import path

from apps.accounts.views import DashboardView, PatientAppointmentDetailView, PatientHistoryView
from apps.accounts.views_design import DesignSystemView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("my-history/", PatientHistoryView.as_view(), name="patient-history"),
    path("my-history/<int:pk>/", PatientAppointmentDetailView.as_view(), name="patient-history-detail"),
    path("design-system/", DesignSystemView.as_view(), name="design-system"),
]
