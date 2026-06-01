/* ═══════════════════════════════════════════════
   MediCore – Frontend Application Logic
   ═══════════════════════════════════════════════ */

let currentUser = null;
let currentRecordId = null;

// ─── API HELPER ────────────────────────────────
async function api(method, url, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin'
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const data = await res.json();
  if (!res.ok) throw { status: res.status, message: data.error || 'Erreur serveur' };
  return data;
}

// ─── TOAST ─────────────────────────────────────
function toast(msg, type = 'success') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ─── SCREENS ───────────────────────────────────
function showAuth()  {
  document.getElementById('auth-screen').classList.add('active');
  document.getElementById('app-screen').classList.remove('active');
}
function showApp() {
  document.getElementById('auth-screen').classList.remove('active');
  document.getElementById('app-screen').classList.add('active');
}

// ─── VIEWS ─────────────────────────────────────
function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const active = document.querySelector(`.nav-item[data-view="${id}"]`);
  if (active) active.classList.add('active');
}

// ─── SIDEBAR ───────────────────────────────────
function buildSidebar(user) {
  const nav = document.getElementById('sidebar-nav');
  const chip = document.getElementById('user-chip');
  chip.innerHTML = `<strong>${user.name}</strong>${user.role === 'doctor' ? 'Médecin' : 'Patient'}`;

  nav.innerHTML = '';
  if (user.role === 'doctor') {
    nav.innerHTML = `
      <button class="nav-item active" data-view="view-patients">
        <span class="nav-icon">👥</span> Liste des patients
      </button>
    `;
  } else {
    nav.innerHTML = `
      <button class="nav-item active" data-view="view-my-record">
        <span class="nav-icon">📋</span> Mon dossier
      </button>
    `;
  }

  nav.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const v = btn.dataset.view;
      if (v === 'view-patients') loadPatients();
      if (v === 'view-my-record') loadMyRecord();
      showView(v);
    });
  });
}

// ─── AUTH TABS ─────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`${btn.dataset.tab}-form`).classList.add('active');
  });
});

// Show/hide patient fields on role change
document.getElementById('reg-role').addEventListener('change', e => {
  document.getElementById('patient-fields').style.display = e.target.value === 'patient' ? '' : 'none';
});

// ─── LOGIN ─────────────────────────────────────
document.getElementById('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const errEl = document.getElementById('login-error');
  errEl.classList.add('hidden');
  try {
    const data = await api('POST', '/api/login', {
      email: document.getElementById('login-email').value,
      password: document.getElementById('login-password').value
    });
    currentUser = data;
    buildSidebar(data);
    showApp();
    if (data.role === 'doctor') { loadPatients(); showView('view-patients'); }
    else { loadMyRecord(); showView('view-my-record'); }
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  }
});

// ─── REGISTER ──────────────────────────────────
document.getElementById('register-form').addEventListener('submit', async e => {
  e.preventDefault();
  const errEl = document.getElementById('register-error');
  errEl.classList.add('hidden');
  const role = document.getElementById('reg-role').value;
  const body = {
    full_name: document.getElementById('reg-name').value,
    email: document.getElementById('reg-email').value,
    password: document.getElementById('reg-password').value,
    role
  };
  if (role === 'patient') {
    body.date_of_birth = document.getElementById('reg-dob').value;
    body.blood_type    = document.getElementById('reg-blood').value;
    body.allergies     = document.getElementById('reg-allergies').value;
    body.phone         = document.getElementById('reg-phone').value;
  }
  try {
    const data = await api('POST', '/api/register', body);
    currentUser = data;
    buildSidebar(data);
    showApp();
    if (data.role === 'doctor') { loadPatients(); showView('view-patients'); }
    else { loadMyRecord(); showView('view-my-record'); }
    toast('Bienvenue dans MediCore !');
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  }
});

// ─── LOGOUT ────────────────────────────────────
document.getElementById('logout-btn').addEventListener('click', async () => {
  await api('POST', '/api/logout');
  currentUser = null;
  showAuth();
});

// ─── LOAD PATIENTS (doctor) ────────────────────
async function loadPatients() {
  const grid = document.getElementById('patients-grid');
  grid.innerHTML = '<div class="loading">Chargement des patients…</div>';
  try {
    const patients = await api('GET', '/api/patients');
    renderPatients(patients);
  } catch { grid.innerHTML = '<div class="loading">Erreur lors du chargement.</div>'; }
}

function initials(name) {
  return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
}

function renderPatients(patients) {
  const grid = document.getElementById('patients-grid');
  if (!patients.length) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">👥</div><p>Aucun patient enregistré</p></div>';
    return;
  }
  grid.innerHTML = patients.map(p => `
    <div class="patient-card" data-id="${p.id}">
      <div class="card-avatar">${initials(p.name)}</div>
      <div class="card-name">${p.name}</div>
      <div class="card-email">${p.email}</div>
      <div class="card-tags">
        <span class="tag tag-blood">🩸 ${p.blood_type}</span>
        ${p.allergies ? `<span class="tag tag-allergy">⚠ Allergies</span>` : ''}
        <span class="tag tag-note">${p.age} ans</span>
      </div>
      <div class="card-stats">
        <div class="stat"><strong>${p.notes_count}</strong> note(s)</div>
        <div class="stat"><strong>${p.prescriptions_count}</strong> ordonnance(s)</div>
      </div>
    </div>
  `).join('');

  grid.querySelectorAll('.patient-card').forEach(card => {
    card.addEventListener('click', () => openRecord(card.dataset.id));
  });
}

// Search filter
document.getElementById('patient-search').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('.patient-card').forEach(card => {
    card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
});

// ─── OPEN RECORD (doctor) ──────────────────────
async function openRecord(recordId) {
  currentRecordId = recordId;
  const container = document.getElementById('record-content');
  container.innerHTML = '<div class="loading">Chargement du dossier…</div>';
  showView('view-record');
  try {
    const p = await api('GET', `/api/patients/${recordId}`);
    renderRecord(p, container, 'doctor');
  } catch { container.innerHTML = '<div class="loading">Erreur.</div>'; }
}

document.getElementById('back-to-list').addEventListener('click', () => {
  showView('view-patients');
});

// ─── LOAD MY RECORD (patient) ─────────────────
async function loadMyRecord() {
  const container = document.getElementById('my-record-content');
  container.innerHTML = '<div class="loading">Chargement de votre dossier…</div>';
  try {
    const res = await fetch('/api/patients/my-record', { credentials: 'same-origin' });
    const p = await res.json();
    renderRecord(p, container, 'patient');
  } catch { container.innerHTML = '<div class="loading">Erreur.</div>'; }
}

// ─── RENDER RECORD ─────────────────────────────
function renderRecord(p, container, role) {
  const allergyTags = p.allergies
    ? p.allergies.split(',').map(a => `<span class="allergy-tag">${a.trim()}</span>`).join('')
    : '<span style="color:var(--text-light);font-size:13px">Aucune allergie connue</span>';

  const editBtn = role === 'doctor'
    ? `<button class="btn-secondary" onclick="openEditModal(${JSON.stringify(p).replace(/"/g,'&quot;')})">✏ Modifier</button>`
    : `<button class="btn-secondary" onclick="openEditModal(${JSON.stringify(p).replace(/"/g,'&quot;')})">✏ Modifier mes infos</button>`;

  const addNoteBtn  = role === 'doctor' ? `<button class="btn-sage" onclick="openNoteModal(${p.id})">+ Ajouter une note</button>` : '';
  const addRxBtn    = role === 'doctor' ? `<button class="btn-sage" onclick="openRxModal(${p.id})">+ Ajouter une ordonnance</button>` : '';

  const notesHtml = p.notes.length ? p.notes.map(n => `
    <div class="note-card">
      <div class="note-header">
        <div>
          <div class="note-title">${n.title}</div>
          <div class="note-meta">Par ${n.doctor_name} · ${n.created_at}</div>
        </div>
        ${role === 'doctor' ? `<button class="btn-danger" onclick="deleteNote(${n.id}, ${p.id})">🗑</button>` : ''}
      </div>
      ${n.diagnosis ? `<div class="note-diagnosis">📋 ${n.diagnosis}</div>` : ''}
      <div class="note-content">${n.content}</div>
    </div>
  `).join('') : '<div class="empty-state"><div class="empty-icon">📝</div><p>Aucune note médicale</p></div>';

  const rxHtml = p.prescriptions.length ? p.prescriptions.map(rx => `
    <div class="rx-card">
      <div class="rx-header">
        <div>
          <div class="rx-med">💊 ${rx.medication}</div>
          <div class="note-meta">Par ${rx.doctor_name} · ${rx.created_at}</div>
        </div>
        ${role === 'doctor' ? `<button class="btn-danger" onclick="deleteRx(${rx.id}, ${p.id})">🗑</button>` : ''}
      </div>
      <div class="rx-details">
        <div class="rx-detail-item"><label>Dosage</label><span>${rx.dosage}</span></div>
        <div class="rx-detail-item"><label>Fréquence</label><span>${rx.frequency}</span></div>
        <div class="rx-detail-item"><label>Durée</label><span>${rx.duration}</span></div>
      </div>
      ${rx.instructions ? `<div class="rx-instructions">${rx.instructions}</div>` : ''}
      ${rx.expires_at ? `<div class="note-meta" style="margin-top:8px">Expire le : ${rx.expires_at}</div>` : ''}
    </div>
  `).join('') : '<div class="empty-state"><div class="empty-icon">💊</div><p>Aucune ordonnance</p></div>';

  container.innerHTML = `
    <div class="record-top">
      <div class="info-card">
        <div class="patient-header">
          <div class="avatar-lg">${initials(p.name)}</div>
          <div>
            <div class="patient-name-big">${p.name}</div>
            <div class="patient-email-big">${p.email}</div>
          </div>
        </div>
        <div class="info-grid">
          <div class="info-item"><label>Date de naissance</label><span>${formatDate(p.date_of_birth)}</span></div>
          <div class="info-item"><label>Âge</label><span>${p.age} ans</span></div>
          <div class="info-item"><label>Groupe sanguin</label><span class="blood-badge">${p.blood_type}</span></div>
          <div class="info-item"><label>Téléphone</label><span>${p.phone || '—'}</span></div>
          <div class="info-item" style="grid-column:1/-1"><label>Adresse</label><span>${p.address || '—'}</span></div>
          <div class="info-item" style="grid-column:1/-1"><label>Contact d'urgence</label><span>${p.emergency_contact || '—'}</span></div>
        </div>
        <div style="margin-top:16px">${editBtn}</div>
      </div>

      <div class="info-card">
        <h2>⚠ Allergies</h2>
        <div class="allergy-list">${allergyTags}</div>
      </div>
    </div>

    <div class="record-tabs">
      <button class="record-tab active" data-panel="notes">Notes médicales (${p.notes.length})</button>
      <button class="record-tab" data-panel="prescriptions">Ordonnances (${p.prescriptions.length})</button>
    </div>

    <div id="panel-notes" class="tab-panel active">
      <div class="section-header">
        <h3>Notes médicales</h3>
        ${addNoteBtn}
      </div>
      ${notesHtml}
    </div>

    <div id="panel-prescriptions" class="tab-panel">
      <div class="section-header">
        <h3>Ordonnances</h3>
        ${addRxBtn}
      </div>
      ${rxHtml}
    </div>
  `;

  // Tab switching
  container.querySelectorAll('.record-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      container.querySelectorAll('.record-tab').forEach(t => t.classList.remove('active'));
      container.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(`panel-${tab.dataset.panel}`).classList.add('active');
    });
  });
}

function formatDate(iso) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

// ─── EDIT MODAL ────────────────────────────────
function openEditModal(p) {
  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <h2>✏ Modifier le dossier</h2>
    <div class="modal-form">
      <div class="edit-grid">
        <div class="field full"><label>Nom complet</label><input id="e-name" value="${p.name}" /></div>
        <div class="field"><label>Date de naissance</label><input type="date" id="e-dob" value="${p.date_of_birth}" /></div>
        <div class="field"><label>Groupe sanguin</label>
          <select id="e-blood">
            ${['A+','A-','B+','B-','AB+','AB-','O+','O-'].map(b => `<option ${b===p.blood_type?'selected':''}>${b}</option>`).join('')}
          </select>
        </div>
        <div class="field"><label>Téléphone</label><input id="e-phone" value="${p.phone||''}" /></div>
        <div class="field"><label>Contact d'urgence</label><input id="e-emergency" value="${p.emergency_contact||''}" /></div>
        <div class="field full"><label>Allergies</label><input id="e-allergies" value="${p.allergies||''}" placeholder="séparées par des virgules" /></div>
        <div class="field full"><label>Adresse</label><textarea id="e-address">${p.address||''}</textarea></div>
      </div>
      <div class="modal-actions">
        <button class="btn-secondary" onclick="closeModal()">Annuler</button>
        <button class="btn-primary" onclick="saveEdit(${p.id})">Enregistrer</button>
      </div>
    </div>
  `;
  openModal();
}

async function saveEdit(recordId) {
  try {
    await api('PUT', `/api/patients/${recordId}`, {
      full_name: document.getElementById('e-name').value,
      date_of_birth: document.getElementById('e-dob').value,
      blood_type: document.getElementById('e-blood').value,
      phone: document.getElementById('e-phone').value,
      emergency_contact: document.getElementById('e-emergency').value,
      allergies: document.getElementById('e-allergies').value,
      address: document.getElementById('e-address').value
    });
    closeModal();
    toast('Dossier mis à jour avec succès');
    if (currentUser.role === 'doctor') openRecord(recordId);
    else loadMyRecord();
  } catch (err) { toast(err.message, 'error'); }
}

// ─── NOTE MODAL ────────────────────────────────
function openNoteModal(patientId) {
  document.getElementById('modal-body').innerHTML = `
    <h2>📝 Nouvelle note médicale</h2>
    <div class="modal-form">
      <div class="field"><label>Titre</label><input id="n-title" placeholder="ex: Consultation de suivi" /></div>
      <div class="field"><label>Diagnostic</label><input id="n-diagnosis" placeholder="ex: Grippe saisonnière" /></div>
      <div class="field"><label>Contenu de la note</label><textarea id="n-content" placeholder="Observations cliniques…"></textarea></div>
      <div class="modal-actions">
        <button class="btn-secondary" onclick="closeModal()">Annuler</button>
        <button class="btn-sage" onclick="saveNote(${patientId})">Ajouter la note</button>
      </div>
    </div>
  `;
  openModal();
}

async function saveNote(patientId) {
  const title = document.getElementById('n-title').value.trim();
  const content = document.getElementById('n-content').value.trim();
  if (!title || !content) { toast('Titre et contenu requis', 'error'); return; }
  try {
    await api('POST', `/api/patients/${patientId}/notes`, {
      title,
      content,
      diagnosis: document.getElementById('n-diagnosis').value
    });
    closeModal();
    toast('Note ajoutée');
    openRecord(patientId);
  } catch (err) { toast(err.message, 'error'); }
}

async function deleteNote(noteId, patientId) {
  if (!confirm('Supprimer cette note ?')) return;
  try {
    await api('DELETE', `/api/notes/${noteId}`);
    toast('Note supprimée');
    openRecord(patientId);
  } catch (err) { toast(err.message, 'error'); }
}

// ─── RX MODAL ──────────────────────────────────
function openRxModal(patientId) {
  document.getElementById('modal-body').innerHTML = `
    <h2>💊 Nouvelle ordonnance</h2>
    <div class="modal-form">
      <div class="field"><label>Médicament</label><input id="rx-med" placeholder="ex: Paracétamol 500mg" /></div>
      <div class="field-row">
        <div class="field"><label>Dosage</label><input id="rx-dose" placeholder="ex: 1 comprimé" /></div>
        <div class="field"><label>Fréquence</label><input id="rx-freq" placeholder="ex: 3x/jour" /></div>
      </div>
      <div class="field-row">
        <div class="field"><label>Durée</label><input id="rx-dur" placeholder="ex: 7 jours" /></div>
        <div class="field"><label>Date d'expiration</label><input type="date" id="rx-exp" /></div>
      </div>
      <div class="field"><label>Instructions particulières</label><textarea id="rx-instr" placeholder="ex: Prendre au repas…"></textarea></div>
      <div class="modal-actions">
        <button class="btn-secondary" onclick="closeModal()">Annuler</button>
        <button class="btn-sage" onclick="saveRx(${patientId})">Émettre l'ordonnance</button>
      </div>
    </div>
  `;
  openModal();
}

async function saveRx(patientId) {
  const med = document.getElementById('rx-med').value.trim();
  const dosage = document.getElementById('rx-dose').value.trim();
  const frequency = document.getElementById('rx-freq').value.trim();
  const duration = document.getElementById('rx-dur').value.trim();
  if (!med || !dosage || !frequency || !duration) { toast('Veuillez remplir tous les champs obligatoires', 'error'); return; }
  try {
    await api('POST', `/api/patients/${patientId}/prescriptions`, {
      medication: med,
      dosage,
      frequency,
      duration,
      instructions: document.getElementById('rx-instr').value,
      expires_at: document.getElementById('rx-exp').value || null
    });
    closeModal();
    toast('Ordonnance émise');
    openRecord(patientId);
  } catch (err) { toast(err.message, 'error'); }
}

async function deleteRx(rxId, patientId) {
  if (!confirm('Supprimer cette ordonnance ?')) return;
  try {
    await api('DELETE', `/api/prescriptions/${rxId}`);
    toast('Ordonnance supprimée');
    openRecord(patientId);
  } catch (err) { toast(err.message, 'error'); }
}

// ─── MODAL HELPERS ─────────────────────────────
function openModal()  { document.getElementById('modal-overlay').classList.remove('hidden'); }
function closeModal() { document.getElementById('modal-overlay').classList.add('hidden'); }

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
});

// ─── INIT ──────────────────────────────────────
(async () => {
  try {
    const me = await api('GET', '/api/me');
    if (me.authenticated) {
      currentUser = me;
      buildSidebar(me);
      showApp();
      if (me.role === 'doctor') { loadPatients(); showView('view-patients'); }
      else { loadMyRecord(); showView('view-my-record'); }
    } else {
      showAuth();
    }
  } catch { showAuth(); }
})();
