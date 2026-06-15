'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash messages
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 6000);
  });

  // Clickable table rows
  document.querySelectorAll('tr.inc-row[data-href]').forEach(row => {
    row.addEventListener('click', e => {
      if (e.target.closest('a,button,form,select')) return;
      window.location.href = row.dataset.href;
    });
  });

  // Confirm destructive forms
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // Bar chart animation
  document.querySelectorAll('.bar-fill[data-pct]').forEach(bar => {
    setTimeout(() => { bar.style.width = bar.dataset.pct + '%'; }, 100);
  });

  // Live MTTR / metrics refresh (every 60s)
  setInterval(refreshMetrics, 60000);

  // Status change modal-less inline submit
  document.querySelectorAll('select.status-select').forEach(sel => {
    sel.addEventListener('change', () => {
      sel.closest('form').submit();
    });
  });
});

function refreshMetrics() {
  fetch('/api/metrics')
    .then(r => r.json())
    .then(data => {
      const el = document.getElementById('live-open');
      if (el) el.textContent = data.total_open;
      ['critical','high','medium','low'].forEach(s => {
        const e = document.getElementById('live-' + s);
        if (e) e.textContent = data.by_severity[s] || 0;
      });
    })
    .catch(() => {});
}
