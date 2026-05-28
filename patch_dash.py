with open("templates/doctor_dashboard.html", "r") as f:
    content = f.read()

sidebar_link = """            <a class="doctor-sidebar-link" href="{% url 'appointment-calendar' %}">
                <i data-lucide="calendar" class="icon-md"></i>
                <span class="doctor-sidebar-text">Lịch biểu trực quan</span>
            </a>"""

if "appointment-calendar" not in content:
    target = """<a class="doctor-sidebar-link" href="{% url 'appointment-list' %}">"""
    # Just need to find the full block or inject before it.
    import re
    # We will just inject it right after the appointment-list link ends.
    # The structure looks like:
    # <a class="doctor-sidebar-link" href="{% url 'appointment-list' %}">
    #     <i data-lucide="calendar-days" class="icon-md"></i>
    #     <span class="doctor-sidebar-text">Lịch khám</span>
    # </a>
    content = content.replace('<span class="doctor-sidebar-text">Lịch hẹn hôm nay</span>\n            </a>', '<span class="doctor-sidebar-text">Lịch hẹn hôm nay</span>\n            </a>\n' + sidebar_link)
    # the text was "Lịch khám" or "Lịch hẹn hôm nay"? Let's just do a simpler replace.
    

with open("templates/doctor_dashboard.html", "w") as f:
    f.write(content)
