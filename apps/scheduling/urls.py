from django.urls import path

from apps.scheduling.views import (
    AppointmentCreateView,
    AppointmentDeleteView,
    AppointmentDetailView,
    AppointmentListView,
    AppointmentUpdateView,
    BookingAccountCreateView,
    BookingSuccessView,
    PublicBookingView,
)


from apps.scheduling.views import AppointmentCalendarView
from apps.scheduling.api_views import AppointmentEventsAPIView, AppointmentCreateAPIView, PatientSearchAPIView, AppointmentUpdateAPIView

urlpatterns = [
    path("calendar/", AppointmentCalendarView.as_view(), name="appointment-calendar"),
            path("api/patients/search/", PatientSearchAPIView.as_view(), name="api-patient-search"),
    path("api/events/create/", AppointmentCreateAPIView.as_view(), name="api-appointment-create"),
    path("api/events/<int:pk>/update/", AppointmentUpdateAPIView.as_view(), name="api-appointment-update"),
    path("api/events/", AppointmentEventsAPIView.as_view(), name="api-appointment-events"),

    path("booking/", PublicBookingView.as_view(), name="public-booking"),
    path("booking/success/", BookingSuccessView.as_view(), name="booking-success"),
    path("booking/create-account/", BookingAccountCreateView.as_view(), name="booking-create-account"),
    path("", AppointmentListView.as_view(), name="appointment-list"),
    path("create/", AppointmentCreateView.as_view(), name="appointment-create"),
    path("<int:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
    path("<int:pk>/edit/", AppointmentUpdateView.as_view(), name="appointment-update"),
    path("<int:pk>/delete/", AppointmentDeleteView.as_view(), name="appointment-delete"),
]
