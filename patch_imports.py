import re

with open("apps/scheduling/views.py", "r") as f:
    content = f.read()

imports_to_add = [
    ("from django.views.generic import ", "TemplateView"),
    ("from apps.accounts.models import ", "UserRole"),
    ("from apps.accounts.models import ", "CustomUser")
]

for base, imp in imports_to_add:
    if imp not in content:
        # crude replacement
        search_pattern = base + "(.*)"
        match = re.search(search_pattern, content)
        if match:
            part = match.group(1)
            content = content.replace(base + part, base + part + f", {imp}")
        else:
            content = f"{base}{imp}\n" + content

with open("apps/scheduling/views.py", "w") as f:
    f.write(content)
