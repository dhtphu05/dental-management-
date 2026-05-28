with open("templates/scheduling/calendar.html", "r") as f:
    content = f.read()

# Make the select function pass parameters
new_select = """      select: function(info) {
        // Redirect to create appointment page with pre-filled date/time
        let createUrl = "{% url 'appointment-create' %}";
        let dateStr = info.startStr.split('T')[0];
        let timeStr = info.startStr.includes('T') ? info.startStr.split('T')[1].substring(0, 5) : "08:00";
        
        let url = new URL(createUrl, window.location.origin);
        url.searchParams.append('date', dateStr);
        url.searchParams.append('time', timeStr);
        window.location.href = url.toString();
      },"""

# Note, the fix_calendar replaced it before, so let's find the current select code
import re
content = re.sub(
    r'select: function\(info\) \{.*?\}(?=,\n\s*eventClick:)',
    new_select,
    content,
    flags=re.DOTALL
)

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(content)
