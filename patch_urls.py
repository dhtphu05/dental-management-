import re

with open("apps/scheduling/urls.py", "r") as f:
    content = f.read()

# Add imports for Calendar and API views
new_imports = """
from apps.scheduling.views import AppointmentCalendarView
from apps.scheduling.api_views import AppointmentEventsAPIView
"""

# Inject before `urlpatterns = [`
if "AppointmentCalendarView" not in content:
    content = content.replace("urlpatterns = [", new_imports + "\nurlpatterns = [")

# Add the urls
new_urls = """    path("calendar/", AppointmentCalendarView.as_view(), name="appointment-calendar"),
    path("api/events/", AppointmentEventsAPIView.as_view(), name="api-appointment-events"),
"""
if "appointment-calendar" not in content:
    content = content.replace("urlpatterns = [", "urlpatterns = [\n" + new_urls)

with open("apps/scheduling/urls.py", "w") as f:
    f.write(content)
