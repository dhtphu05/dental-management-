import re

with open("templates/scheduling/calendar.html", "r") as f:
    text = f.read()

# Add a hint label for search near "phone", but let's just intercept the phone loop.
# actually, let's just add the JS logic to listen to phone blur.
search_js = """
  // Patient auto-search logic
  document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.querySelector('input[name="phone"]');
    if (phoneInput) {
      // Add search button inline next to input
      const container = phoneInput.parentElement;
      container.classList.add('relative');
      
      const searchBtn = document.createElement('button');
      searchBtn.type = 'button';
      searchBtn.className = 'absolute right-2 top-1/2 -translate-y-1/2 text-primary-500 hover:text-primary-700 bg-white p-1 rounded font-semibold text-xs';
      searchBtn.innerHTML = '<i data-lucide="search" class="w-4 h-4 inline-block"></i> Tìm';
      
      let parentHTML = phoneInput.outerHTML;
      phoneInput.outerHTML = '<div class="flex gap-2">' + parentHTML + '</div>';
      
      // we need to reselect after outerHTML
      const newPhoneInput = document.querySelector('input[name="phone"]');
      const innerContainer = newPhoneInput.parentElement;
      innerContainer.appendChild(searchBtn);
      
      // Also add a little status text
      const statusText = document.createElement('div');
      statusText.className = 'text-xs mt-1 min-h-[20px]';
      innerContainer.parentElement.appendChild(statusText);

      function performSearch() {
        const phone = newPhoneInput.value.trim();
        if (phone.length < 9) return;
        
        statusText.innerHTML = '<span class="text-slate-500">Đang tìm kiếm...</span>';
        
        // Search API call
        fetch(`{% url 'api-patient-search' %}?phone=${phone}`)
          .then(res => res.json())
          .then(data => {
            const nameInput = document.querySelector('input[name="full_name"]');
            if (data.status === 'success') {
              statusText.innerHTML = '<span class="text-emerald-600 font-medium"><i data-lucide="check-circle" class="w-3 h-3 inline-block mr-1"></i>Đã tìm thấy Bệnh nhân cũ</span>';
              if (nameInput) {
                nameInput.value = data.data.full_name;
                nameInput.classList.add('bg-emerald-50');
                setTimeout(() => nameInput.classList.remove('bg-emerald-50'), 1000);
              }
            } else if (data.status === 'not_found') {
              statusText.innerHTML = '<span class="text-primary-600 font-medium"><i data-lucide="info" class="w-3 h-3 inline-block mr-1"></i>Bệnh nhân mới. Hãy nhập tên.</span>';
              if (nameInput && !nameInput.value) {
                nameInput.focus();
              }
            } else {
              statusText.innerHTML = `<span class="text-rose-600">${data.message || 'Lỗi tìm kiếm'}</span>`;
            }
            lucide.createIcons();
          })
          .catch(err => {
            statusText.innerHTML = '<span class="text-rose-600">Lỗi kết nối</span>';
          });
      }

      searchBtn.addEventListener('click', performSearch);
      
      // also search on blur if they typed something
      newPhoneInput.addEventListener('blur', function() {
         if (newPhoneInput.value.trim().length >= 9) performSearch();
      });
      
      // Enter key on phone prevents submit and triggers search
      newPhoneInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          performSearch();
        }
      });
    }
  });
"""

text = text.replace("function submitAppointmentForm(event) {", search_js + "\n  function submitAppointmentForm(event) {")

with open("templates/scheduling/calendar.html", "w") as f:
    f.write(text)
