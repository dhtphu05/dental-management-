with open("templates/scheduling/calendar.html", "r") as f:
    text = f.read()

text = text.replace("expandRows: true,", "expandRows: true,\n      height: 800,")

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(text)
