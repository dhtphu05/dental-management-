import re

with open("apps/scheduling/views.py", "r") as f:
    content = f.read()

# Append AppointmentCalendarView at the end
new_view = """
class AppointmentCalendarView(AppointmentAccessMixin, TemplateView):
    template_name = "scheduling/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Lịch tuần"
        context["doctor_options"] = CustomUser.objects.filter(role=UserRole.DOCTOR).order_by(
            "first_name", "last_name", "username"
        )
        return context
"""

if "AppointmentCalendarView" not in content:
    with open("apps/scheduling/views.py", "a") as f:
        f.write("\n" + new_view + "\n")
