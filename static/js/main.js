/* ============================================================
   JobPortal Pro – Main JS
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  // Auto-dismiss flash alerts after 5 seconds
  document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // File input size validation (max 5 MB)
  document.querySelectorAll('input[type="file"]').forEach(function (input) {
    input.addEventListener('change', function () {
      const maxBytes = 5 * 1024 * 1024;
      Array.from(this.files).forEach(function (file) {
        if (file.size > maxBytes) {
          alert('File "' + file.name + '" exceeds the 5 MB limit.');
          input.value = '';
        }
      });
    });
  });

  // Confirm delete forms
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(form.dataset.confirm || 'Are you sure?')) {
        e.preventDefault();
      }
    });
  });

  // Character counter for SMS textarea
  const smsTextarea = document.querySelector('textarea[name="message"][maxlength]');
  if (smsTextarea) {
    const counter = document.createElement('div');
    counter.className = 'form-text text-end';
    smsTextarea.parentNode.appendChild(counter);
    function updateCounter() {
      const remaining = parseInt(smsTextarea.getAttribute('maxlength')) - smsTextarea.value.length;
      counter.textContent = remaining + ' characters remaining';
      counter.className = 'form-text text-end ' + (remaining < 20 ? 'text-danger' : 'text-muted');
    }
    smsTextarea.addEventListener('input', updateCounter);
    updateCounter();
  }

  // Dynamic city loader (shared helper used by pages that didn't include inline JS)
  window.loadCities = function (districtValue, citySelectId, selectedCity) {
    const citySelect = document.getElementById(citySelectId);
    if (!citySelect) return;
    citySelect.innerHTML = '<option value="">Any City</option>';
    if (!districtValue) return;
    fetch('/get-cities?district=' + encodeURIComponent(districtValue))
      .then(function (r) { return r.json(); })
      .then(function (cities) {
        cities.forEach(function (c) {
          const opt = document.createElement('option');
          opt.value = c.name;
          opt.textContent = c.name;
          if (c.name === selectedCity) opt.selected = true;
          citySelect.appendChild(opt);
        });
      })
      .catch(function (err) { console.warn('City load failed:', err); });
  };

  // Activate tooltips everywhere
  document.querySelectorAll('[title]').forEach(function (el) {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });

  // Highlight active nav link
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active', 'fw-semibold');
    }
  });

});
