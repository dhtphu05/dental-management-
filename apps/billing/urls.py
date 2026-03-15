from django.urls import path

from apps.billing.views import InvoiceDeleteView, InvoiceDetailView, InvoiceListView, InvoiceUpdateView

urlpatterns = [
    path("", InvoiceListView.as_view(), name="invoice-list"),
    path("<int:pk>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("<int:pk>/edit/", InvoiceUpdateView.as_view(), name="invoice-update"),
    path("<int:pk>/delete/", InvoiceDeleteView.as_view(), name="invoice-delete"),
]
