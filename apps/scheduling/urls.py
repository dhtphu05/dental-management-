from django.urls import path

from apps.scheduling.views import (
    AppointmentCreateView,
    AppointmentDeleteView,
    AppointmentDetailView,
    AppointmentListView,
    AppointmentUpdateView,
)

urlpatterns = [
    path("", AppointmentListView.as_view(), name="appointment-list"),
    path("create/", AppointmentCreateView.as_view(), name="appointment-create"),
    path("<int:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
    path("<int:pk>/edit/", AppointmentUpdateView.as_view(), name="appointment-update"),
    path("<int:pk>/delete/", AppointmentDeleteView.as_view(), name="appointment-delete"),
]
