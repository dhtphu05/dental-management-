with open("apps/scheduling/urls.py", "r") as f:
    text = f.read()

text = text.replace(
    "from apps.scheduling.api_views import AppointmentEventsAPIView", 
    "from apps.scheduling.api_views import AppointmentEventsAPIView, AppointmentCreateAPIView"
)

new_url = '    path("api/events/create/", AppointmentCreateAPIView.as_view(), name="api-appointment-create"),'
if "api-appointment-create" not in text:
    text = text.replace('path("api/events/",', new_url + '\n    path("api/events/",')

with open("apps/scheduling/urls.py", "w") as f:
    f.write(text)
