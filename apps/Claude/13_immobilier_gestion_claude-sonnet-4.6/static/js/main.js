'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash messages
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });

  // Photo preview for any file input with data-preview target
  document.querySelectorAll('input[type="file"][data-preview]').forEach(input => {
    const container = document.getElementById(input.dataset.preview);
    if (!container) return;
    input.addEventListener('change', () => {
      container.innerHTML = '';
      Array.from(input.files).forEach(file => {
        if (!file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = e => {
          const img = document.createElement('img');
          img.src = e.target.result;
          img.className = 'preview-thumb';
          container.appendChild(img);
        };
        reader.readAsDataURL(file);
      });
    });
  });

  // Upload zone click
  document.querySelectorAll('.upload-zone').forEach(zone => {
    zone.addEventListener('click', () => {
      const input = zone.querySelector('input[type="file"]');
      if (input) input.click();
    });
  });

  // Confirm delete forms
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // Auto-fill rent amount from selected lease in payment form
  const leaseSelect = document.getElementById('lease-select');
  const amountInput = document.getElementById('amount-input');
  if (leaseSelect && amountInput) {
    leaseSelect.addEventListener('change', () => {
      const opt = leaseSelect.selectedOptions[0];
      if (opt && opt.dataset.rent) amountInput.value = opt.dataset.rent;
    });
  }
});
