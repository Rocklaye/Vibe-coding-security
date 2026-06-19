/**
 * HR Manager - JavaScript principal
 * Fonctions utilitaires et gestion globale de l'application
 */

// ============================================
// UTILITAIRES
// ============================================

/**
 * Formate une date ISO en format français
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Formate une date et heure ISO
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formate un montant en euros
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

/**
 * Traduit le type de congé
 */
function formatLeaveType(type) {
    const types = {
        'annual': 'Congés payés',
        'sick': 'Maladie',
        'unpaid': 'Sans solde',
        'maternity': 'Maternité',
        'paternity': 'Paternité',
        'rtt': 'RTT',
        'other': 'Autre'
    };
    return types[type] || type;
}

/**
 * Traduit le statut
 */
function formatStatus(status) {
    const statuses = {
        'active': 'Actif',
        'inactive': 'Inactif',
        'pending': 'En attente',
        'approved': 'Approuvé',
        'rejected': 'Rejeté',
        'cancelled': 'Annulé',
        'draft': 'Brouillon',
        'submitted': 'Soumis',
        'reviewed': 'Révisé',
        'processed': 'Traité',
        'paid': 'Payé',
        'on_leave': 'En congé',
        'terminated': 'Parti'
    };
    return statuses[status] || status;
}

/**
 * Retourne l'icône correspondant à une action
 */
function getActionIcon(action) {
    const icons = {
        'create': 'plus-circle',
        'update': 'edit',
        'delete': 'trash',
        'approve': 'check-circle',
        'reject': 'times-circle'
    };
    return icons[action] || 'info-circle';
}

// ============================================
// NOTIFICATIONS
// ============================================

/**
 * Affiche une notification toast
 */
function showNotification(message, type = 'success') {
    // Supprimer l'ancien container s'il existe
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto-supprimer après 3 secondes
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// ============================================
// SIDEBAR
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            
            const icon = sidebarToggle.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.classList.remove('fa-chevron-left');
                icon.classList.add('fa-chevron-right');
            } else {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-chevron-left');
            }
        });
    }
});

// ============================================
// PASSWORD TOGGLE
// ============================================

function togglePassword(button) {
    const input = button.parentElement.querySelector('input');
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// ============================================
// MODAL GLOBAL
// ============================================

function openModal(title, content, confirmCallback = null, confirmText = 'Confirmer') {
    const modal = document.getElementById('modal');
    const overlay = document.getElementById('modalOverlay');
    
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    document.getElementById('modalConfirm').textContent = confirmText;
    
    modal.classList.add('active');
    overlay.classList.add('active');
    
    const confirmBtn = document.getElementById('modalConfirm');
    const cancelBtn = document.getElementById('modalCancel');
    const closeBtn = document.getElementById('modalClose');
    
    // Reset listeners
    const newConfirm = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);
    
    if (confirmCallback) {
        newConfirm.style.display = 'inline-flex';
        newConfirm.addEventListener('click', function() {
            confirmCallback();
            closeModal();
        });
    } else {
        newConfirm.style.display = 'none';
    }
    
    cancelBtn.onclick = closeModal;
    closeBtn.onclick = closeModal;
    overlay.onclick = closeModal;
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
    document.getElementById('modalOverlay').classList.remove('active');
}

// ============================================
// CONFIRMATION DIALOG
// ============================================

function confirmDialog(message, onConfirm) {
    openModal('Confirmation', `<p>${message}</p>`, onConfirm, 'Confirmer');
}

// ============================================
// API HELPERS
// ============================================

/**
 * Effectue un appel API GET
 */
async function apiGet(url) {
    const response = await fetch(url);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `Erreur HTTP ${response.status}`);
    }
    return response.json();
}

/**
 * Effectue un appel API POST
 */
async function apiPost(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `Erreur HTTP ${response.status}`);
    }
    return response.json();
}

/**
 * Effectue un appel API PUT
 */
async function apiPut(url, data) {
    const response = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `Erreur HTTP ${response.status}`);
    }
    return response.json();
}

/**
 * Effectue un appel API DELETE
 */
async function apiDelete(url) {
    const response = await fetch(url, { method: 'DELETE' });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `Erreur HTTP ${response.status}`);
    }
    return response.json();
}

// ============================================
// GESTION DES ERREURS
// ============================================

window.addEventListener('error', function(e) {
    console.error('Erreur globale:', e.error);
});

// Gestion des erreurs fetch
window.addEventListener('unhandledrejection', function(e) {
    if (e.reason && e.reason.message && e.reason.message.includes('fetch')) {
        showNotification('Erreur de connexion au serveur', 'error');
    }
});
