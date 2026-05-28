with open("templates/doctor_dashboard.html", "r") as f:
    content = f.read()

sidebar_link = """            <a class="doctor-sidebar-link" href="{% url 'appointment-calendar' %}">
                <i data-lucide="calendar" class="icon-md"></i>
                <span class="doctor-sidebar-text">Lịch biểu Calendar</span>
            </a>
"""

if "appointment-calendar" not in content:
    target = """<span class="doctor-sidebar-text">Lịch hẹn</span>
            </a>"""
    content = content.replace(target, target + "\n" + sidebar_link)

with open("templates/doctor_dashboard.html", "w") as f:
    f.write(content)
