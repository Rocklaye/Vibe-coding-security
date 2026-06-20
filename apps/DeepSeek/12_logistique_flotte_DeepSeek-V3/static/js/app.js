// Configuration globale
const API_BASE_URL = '';

// Fonctions utilitaires
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Gestion des erreurs AJAX
function handleAjaxError(error) {
    console.error('Erreur AJAX:', error);
    showAlert('Une erreur est survenue lors de la communication avec le serveur', 'danger');
}

// Initialisation des tooltips Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Fonction pour rafraîchir les données en temps réel
function startAutoRefresh(intervalSeconds = 30) {
    setInterval(() => {
        if (document.hidden) return; // Ne pas rafraîchir si l'onglet n'est pas actif
        
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                updateDashboardStats(data);
            })
            .catch(error => console.error('Erreur de rafraîchissement:', error));
    }, intervalSeconds * 1000);
}

function updateDashboardStats(stats) {
    // Mettre à jour les compteurs du tableau de bord
    const statElements = document.querySelectorAll('.stat-card h2');
    if (statElements.length >= 4) {
        statElements[0].textContent = stats.total_vehicles;
        statElements[1].textContent = stats.available_vehicles;
        statElements[2].textContent = stats.active_tours;
        statElements[3].textContent = stats.open_incidents;
    }
}

// Validation de formulaire
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Gestion du stockage local pour les préférences utilisateur
function saveUserPreference(key, value) {
    localStorage.setItem(`fleet_${key}`, JSON.stringify(value));
}

function getUserPreference(key, defaultValue = null) {
    const value = localStorage.getItem(`fleet_${key}`);
    return value ? JSON.parse(value) : defaultValue;
}