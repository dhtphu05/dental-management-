from django.urls import path

from apps.patients.views import (
    PatientCreateView,
    PatientDeleteView,
    PatientDetailView,
    PatientListView,
    PatientUpdateView,
)

urlpatterns = [
    path("", PatientListView.as_view(), name="patient-list"),
    path("create/", PatientCreateView.as_view(), name="patient-create"),
    path("<int:pk>/", PatientDetailView.as_view(), name="patient-detail"),
    path("<int:pk>/edit/", PatientUpdateView.as_view(), name="patient-update"),
    path("<int:pk>/delete/", PatientDeleteView.as_view(), name="patient-delete"),
]
