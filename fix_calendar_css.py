import re

with open("templates/scheduling/calendar.html", "r") as f:
    text = f.read()

# Fix layout for the phone field
# Previously we had <div class="[&>input]... "> {{field}} </div> 
# Which makes all inputs full width.
# We wrapped the input in a flex container so flex children should grow.
text = text.replace(
    'phoneInput.outerHTML = \'<div class="flex gap-2">\' + parentHTML + \'</div>\';',
    'phoneInput.outerHTML = \'<div class="flex gap-2 relative w-full">\' + parentHTML.replace(/class="/, \'class="w-full \') + \'</div>\';'
)

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(text)
