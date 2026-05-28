with open("apps/scheduling/views.py", "r") as f:
    text = f.read()

text = text.replace("class AppointmentUpdateView, TemplateView(AppointmentAccessMixin, UpdateView, TemplateView):", "class AppointmentUpdateView(AppointmentAccessMixin, UpdateView):")

with open("apps/scheduling/views.py", "w") as f:
    f.write(text)
