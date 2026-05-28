with open("apps/scheduling/urls.py", "r") as f:
    text = f.read()

text = text.replace(
    "from apps.scheduling.api_views import AppointmentEventsAPIView, AppointmentCreateAPIView", 
    "from apps.scheduling.api_views import AppointmentEventsAPIView, AppointmentCreateAPIView, PatientSearchAPIView"
)

new_url = '    path("api/patients/search/", PatientSearchAPIView.as_view(), name="api-patient-search"),'
if "api-patient-search" not in text:
    text = text.replace('path("api/events/create/",', new_url + '\n    path("api/events/create/",')

with open("apps/scheduling/urls.py", "w") as f:
    f.write(text)
