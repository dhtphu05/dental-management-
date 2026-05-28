import re

with open("templates/scheduling/calendar.html", "r") as f:
    text = f.read()

drawer_html = """
<!-- Create Appointment Drawer (Sidebar) -->
<div id="create-drawer" class="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white shadow-2xl transform translate-x-full transition-transform duration-300 ease-in-out pointer-events-auto flex flex-col hidden">
  <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50 relative shrink-0">
    <h2 class="text-xl font-bold text-slate-900 flex items-center gap-2">
      <i data-lucide="calendar-plus" class="h-5 w-5 text-primary-500"></i>
      Thêm lịch hẹn
    </h2>
    <button type="button" onclick="closeCreateDrawer()" class="p-2 rounded-lg hover:bg-slate-200 text-slate-500 transition-colors">
      <i data-lucide="x" class="h-5 w-5"></i>
    </button>
  </div>
  <div class="p-6 overflow-y-auto grow">
    <form id="drawer-form" onsubmit="submitAppointmentForm(event)">
      <div id="drawer-errors" class="mb-4 rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700 hidden"></div>
      
      <div class="grid gap-5">
        {% for field in form %}
            <div>
                <label class="mb-2 block text-sm font-semibold text-[var(--color-ink-700)]" for="{{ field.id_for_label }}">{{ field.label }}</label>
                {{ field }}
                {% if field.help_text %}<div class="mt-1 text-xs text-[var(--color-ink-500)]">{{ field.help_text }}</div>{% endif %}
            </div>
        {% endfor %}
      </div>
      
      <div class="mt-8 flex gap-3">
        <button type="submit" class="btn btn-primary w-full flex justify-center items-center gap-2">
          <i data-lucide="save" class="h-4 w-4"></i> Lưu lịch hẹn
        </button>
      </div>
    </form>
  </div>
</div>
<!-- End Drawer -->
"""

# Insert drawer_html before {% endblock %} of content
text = text.replace("<!-- Modal for Event Details (Tailwind styled) -->", drawer_html + "\n<!-- Modal for Event Details (Tailwind styled) -->")

# Change "Thêm lịch hẹn" button to open drawer
text = text.replace('href="{% url \'appointment-create\' %}" class="btn btn-primary', 'href="javascript:void(0)" onclick="openCreateDrawer()" class="btn btn-primary')

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(text)
