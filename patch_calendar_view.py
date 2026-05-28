import re

with open("apps/scheduling/views.py", "r") as f:
    content = f.read()

new_view = """class AppointmentCalendarView(AppointmentAccessMixin, TemplateView):
    template_name = "scheduling/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Lịch tuần"
        context["doctor_options"] = CustomUser.objects.filter(role=UserRole.DOCTOR).order_by(
            "first_name", "last_name", "username"
        )
        from apps.scheduling.forms import AppointmentForm
        # Provide an empty form for the sidebar
        context["form"] = AppointmentForm()
        return context
"""

content = re.sub(
    r'class AppointmentCalendarView\(AppointmentAccessMixin, TemplateView\):[\s\S]*?(?=return context\n)',
    new_view.replace('return context\n', ''),
    content
)

with open("apps/scheduling/views.py", "w") as f:
    f.write(content)
