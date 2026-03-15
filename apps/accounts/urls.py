from django.urls import path

from apps.accounts.views import DashboardView
from apps.accounts.views_design import DesignSystemView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("design-system/", DesignSystemView.as_view(), name="design-system"),
]
