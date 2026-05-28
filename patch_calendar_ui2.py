import re

with open("templates/scheduling/calendar.html", "r") as f:
    text = f.read()

# Add standard form styles natively to the inputs rendered by django.
styled_fields = """
                <div class="mt-1">
                    {{ field }}
                </div>
"""

# Let's see the current drawer loop:
# {% for field in form %}
#    <div>
#        <label class="mb-2 block text-sm font-semibold text-[var(--color-ink-700)]" for="{{ field.id_for_label }}">{{ field.label }}</label>
#        {{ field }}

text = text.replace(
    '{{ field }}',
    """<div class="[&>input]:form-input [&>select]:form-select [&>textarea]:form-textarea w-full">
                  {{ field }}
                </div>"""
)

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(text)
