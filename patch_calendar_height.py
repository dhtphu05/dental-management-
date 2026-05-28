import re

with open("templates/scheduling/calendar.html", "r") as f:
    text = f.read()

# Remove expandRows and explicitly set a height in CSS or JS
new_css = """
  #calendar {
    min-height: 700px;
  }
</style>"""
text = text.replace("</style>", new_css)

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(text)
