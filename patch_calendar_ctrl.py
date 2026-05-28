import re

with open("apps/scheduling/views.py", "r") as f:
    text = f.read()

# Update Calendar View to use SidebarAppointmentForm
text = text.replace(
    "from apps.scheduling.forms import AppointmentForm",
    "from apps.scheduling.forms import AppointmentForm, SidebarAppointmentForm"
)
text = text.replace('context["form"] = AppointmentForm()', 'context["form"] = SidebarAppointmentForm()')

with open("apps/scheduling/views.py", "w") as f:
    f.write(text)
