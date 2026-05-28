import re

with open("templates/scheduling/calendar.html", "r") as f:
    text = f.read()

drawer_js = """
  function openCreateDrawer(dateStr = '', timeStr = '') {
    const drawer = document.getElementById('create-drawer');
    drawer.classList.remove('hidden');
    // small timeout for transition
    setTimeout(() => {
      drawer.classList.remove('translate-x-full');
    }, 10);
    
    // Auto-fill dates if provided
    if (dateStr) {
      const dateInput = document.querySelector('input[type="date"][name="date"]');
      if (dateInput) dateInput.value = dateStr;
    }
    if (timeStr) {
      const timeInput = document.querySelector('input[type="time"][name="time_slot"]');
      if (timeInput) timeInput.value = timeStr;
    }
    lucide.createIcons();
  }

  function closeCreateDrawer() {
    const drawer = document.getElementById('create-drawer');
    drawer.classList.add('translate-x-full');
    setTimeout(() => {
      drawer.classList.add('hidden');
    }, 300);
  }

  function submitAppointmentForm(event) {
    event.preventDefault();
    const form = document.getElementById('drawer-form');
    const errBox = document.getElementById('drawer-errors');
    errBox.classList.add('hidden');
    errBox.innerHTML = '';
    
    const formData = new FormData(form);
    
    fetch("{% url 'api-appointment-create' %}", {
      method: "POST",
      body: formData,
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        closeCreateDrawer();
        form.reset();
        calendar.refetchEvents();
      } else {
        let errHtml = '';
        for (const [key, msgs] of Object.entries(data.errors)) {
          errHtml += `<div><strong>${key}</strong>: ${msgs.join(', ')}</div>`;
        }
        errBox.innerHTML = errHtml;
        errBox.classList.remove('hidden');
      }
    })
    .catch(err => {
      errBox.innerHTML = "Có lỗi xảy ra. Hãy kiểm tra lại kết nối.";
      errBox.classList.remove('hidden');
    });
  }
"""

# Replace the select event logic
new_select = """      select: function(info) {
        let dateStr = info.startStr.split('T')[0];
        let timeStr = info.startStr.includes('T') ? info.startStr.split('T')[1].substring(0, 5) : "";
        openCreateDrawer(dateStr, timeStr);
      },"""

text = re.sub(r'select: function\(info\) \{.*?\},', new_select, text, flags=re.DOTALL)
text = text.replace("let calendar;", "let calendar;\n" + drawer_js)

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(text)
