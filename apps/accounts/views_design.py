from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DesignSystemView(LoginRequiredMixin, TemplateView):
    template_name = "design_system.html"
