import re

with open("templates/scheduling/calendar.html", "r") as f:
    content = f.read()

# Fix the block names
content = content.replace("{% block extra_css %}", "{% block extra_head %}")
content = content.replace("{% block extra_js %}", "{% block extra_scripts %}")

# Add selectable and select callback to FullCalendar options
fullcalendar_options = """      slotMaxTime: '20:00:00',
      expandRows: true,
      selectable: true,
      select: function(info) {
        // Redirect to create appointment page with pre-filled date/time
        // We can pass start date and time as query params if the create view supports it
        // Or at least just navigate to the create page
        let createUrl = "{% url 'appointment-create' %}";
        // Convert ISO start string to local components if needed
        window.location.href = createUrl;
      },
      eventClick: function(info) {"""

content = content.replace("slotMaxTime: '20:00:00',\n      expandRows: true,\n      eventClick: function(info) {", fullcalendar_options)

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(content)
