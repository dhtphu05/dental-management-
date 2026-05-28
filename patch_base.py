with open("templates/base.html", "r") as f:
    content = f.read()

nav_link = """<a class="nav-link" href="{% url 'appointment-calendar' %}"><i data-lucide="calendar" class="icon-sm"></i>Lịch biểu</a>"""

if "appointment-calendar" not in content:
    # insert it right after the appointment-list nav link
    target = """<a class="nav-link" href="{% url 'appointment-list' %}"><i data-lucide="calendar-days" class="icon-sm"></i>Lịch hẹn</a>"""
    content = content.replace(target, target + "\n                    " + nav_link)

with open("templates/base.html", "w") as f:
    f.write(content)
