/**
 * TeleMed - Application de Télémédecine
 * JavaScript principal
 */

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-fermeture des alertes après 5 secondes
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
    
    // Confirmation pour les actions destructrices
    const confirmForms = document.querySelectorAll('form[onsubmit]');
    confirmForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const onsubmitAttr = form.getAttribute('onsubmit');
            if (onsubmitAttr && onsubmitAttr.includes('confirm')) {
                // La confirmation est gérée par l'attribut inline
                return;
            }
        });
    });
    
    // Tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Animation des cards au scroll
    const animatedElements = document.querySelectorAll('.feature-card, .doctor-card-home');
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    animatedElements.forEach(function(el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Gestion du mot de passe (afficher/masquer)
    window.togglePassword = function(inputId) {
        const input = document.getElementById(inputId);
        const button = input.nextElementSibling;
        const icon = button.querySelector('i');
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
        }
    };
    
    // Smooth scroll pour les ancres
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Mise à jour de l'heure en temps réel (si élément présent)
    function updateTime() {
        const timeElements = document.querySelectorAll('.live-time');
        timeElements.forEach(function(el) {
            const now = new Date();
            el.textContent = now.toLocaleTimeString('fr-FR');
        });
    }
    
    if (document.querySelector('.live-time')) {
        setInterval(updateTime, 1000);
        updateTime();
    }
    
    // Validation des formulaires en temps réel
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateInput(this);
                }
            });
        });
    });
    
    function validateInput(input) {
        if (input.checkValidity()) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
        }
    }
    
    // Gestion des tableaux responsives
    const tables = document.querySelectorAll('.table-responsive table');
    tables.forEach(function(table) {
        // Ajouter une classe pour le scroll horizontal sur mobile
        table.classList.add('table-mobile-friendly');
    });
    
    // Animation du compteur pour les statistiques
    const statNumbers = document.querySelectorAll('.card h3.fw-bold');
    
    const numberObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                numberObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    statNumbers.forEach(function(el) {
        numberObserver.observe(el);
    });
    
    function animateCounter(element) {
        const target = parseInt(element.textContent) || 0;
        if (target === 0) return;
        
        const duration = 1000;
        const step = target / (duration / 16);
        let current = 0;
        
        const timer = setInterval(function() {
            current += step;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }
    
    // Gestion des filtres de tableau
    const filterInputs = document.querySelectorAll('.table-filter');
    filterInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const tableId = this.dataset.table;
            const column = this.dataset.column;
            const value = this.value.toLowerCase();
            const table = document.getElementById(tableId);
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(function(row) {
                    const cell = row.querySelectorAll('td')[column];
                    if (cell) {
                        const cellText = cell.textContent.toLowerCase();
                        row.style.display = cellText.includes(value) ? '' : 'none';
                    }
                });
            }
        });
    });
    
    // Confirmations pour les actions importantes
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            if (typeof callback === 'function') {
                callback();
            }
            return true;
        }
        return false;
    };
    
    // Gestion du mode sombre (si implémenté plus tard)
    window.toggleDarkMode = function() {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDark);
    };
    
    // Restaurer le mode sombre
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
    
    console.log('TeleMed - Application initialisée');
});

// Fonctions globales

/**
 * Formate une date en français
 */
function formatDateFR(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

/**
 * Formate une heure
 */
function formatTime(timeString) {
    return timeString.substring(0, 5);
}

/**
 * Affiche un message de notification
 */
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(function() {
        const closeBtn = alertDiv.querySelector('.btn-close');
        if (closeBtn) closeBtn.click();
    }, 5000);
}

/**
 * Copie le texte dans le presse-papiers
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copié dans le presse-papiers!', 'success');
    }).catch(function() {
        showNotification('Erreur lors de la copie', 'danger');
    });
}

/**
 * Défilement vers un élément
 */
function scrollToElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
