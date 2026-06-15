'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Character counters
  attachCounter('compose-textarea', 'compose-counter', 280);
  attachCounter('comment-textarea', 'comment-counter', 280);
  attachCounter('bio-textarea',     'bio-counter',     160);

  // Auto-dismiss flash messages after 4 s
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 4000);
  });
});

function attachCounter(textareaId, counterId, max) {
  const textarea = document.getElementById(textareaId);
  const counter  = document.getElementById(counterId);
  if (!textarea || !counter) return;

  const span = counter.querySelector('.count');
  if (!span) return;

  function refresh() {
    const remaining = max - textarea.value.length;
    span.textContent = remaining;
    counter.classList.remove('warn', 'danger');
    if (remaining < 0)  counter.classList.add('danger');
    else if (remaining <= 20) counter.classList.add('warn');
  }

  textarea.addEventListener('input', refresh);
  refresh();
}
