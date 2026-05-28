with open("apps/scheduling/views.py", "r") as f:
    content = f.read()

new_create_view = """class AppointmentCreateView(AppointmentAccessMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("appointment-list")

    def get_initial(self):
        initial = super().get_initial()
        # Parse query params like ?date=2026-05-28&time=14:30
        if self.request.GET.get('date'):
            initial['date'] = self.request.GET.get('date')
        if self.request.GET.get('time'):
            # Convert simple time string if needed, or stick to what the form expects
            initial['time_slot'] = self.request.GET.get('time')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Thêm lịch hẹn"
        return context
"""

import re
# Regex to replace the original AppointmentCreateView
content = re.sub(
    r'class AppointmentCreateView\(AppointmentAccessMixin, CreateView\):[\s\S]*?(?=class \w+|$)',
    new_create_view + '\n',
    content
)

with open("apps/scheduling/views.py", "w") as f:
    f.write(content)
