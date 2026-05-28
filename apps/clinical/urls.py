from django.urls import path

from apps.clinical.views import (
    DoctorTreatmentPlanUpdateView,
    ServiceCreateView,
    ServiceDeleteView,
    ServiceListView,
    ServiceUpdateView,
)
from apps.clinical.api_views import ToothUpdateAPIView

urlpatterns = [
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("services/create/", ServiceCreateView.as_view(), name="service-create"),
    path("services/<int:pk>/edit/", ServiceUpdateView.as_view(), name="service-update"),
    path("services/<int:pk>/delete/", ServiceDeleteView.as_view(), name="service-delete"),
    path("appointments/<int:appointment_id>/treatment-plan/", DoctorTreatmentPlanUpdateView.as_view(), name="doctor-treatment-plan"),
    path("api/teeth/<int:pk>/update/", ToothUpdateAPIView.as_view(), name="api-tooth-update"),
]
