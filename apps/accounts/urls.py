from django.urls import path

from apps.accounts.views import (
    DashboardView,
    LandingPageView,
    PatientAppointmentDetailView,
    PatientHistoryView,
    PatientRegisterView,
    PatientTeethView,
)
from apps.accounts.views_design import DesignSystemView

urlpatterns = [
    path("", LandingPageView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("register/", PatientRegisterView.as_view(), name="patient-register"),
    path("my-history/", PatientHistoryView.as_view(), name="patient-history"),
    path("my-history/<int:pk>/", PatientAppointmentDetailView.as_view(), name="patient-history-detail"),
    path("my-teeth/", PatientTeethView.as_view(), name="patient-teeth"),
    path("design-system/", DesignSystemView.as_view(), name="design-system"),
]
