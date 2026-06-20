// Gestion des profils
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du lecteur vidéo
    initVideoPlayer();
    
    // Gestion des formulaires
    initForms();
    
    // Recherche en temps réel
    initSearch();
    
    // Animations
    initAnimations();
});

// Lecteur vidéo simulé
function initVideoPlayer() {
    const videoSimulator = document.querySelector('.video-simulator');
    const playButton = document.querySelector('.play-button');
    const progressFill = document.querySelector('.progress-fill');
    
    if (videoSimulator && playButton) {
        let isPlaying = false;
        let progress = 0;
        let interval;
        
        playButton.addEventListener('click', function() {
            if (!isPlaying) {
                isPlaying = true;
                playButton.innerHTML = '⏸️';
                
                // Simuler la progression
                interval = setInterval(() => {
                    progress += 0.1;
                    if (progress <= 100) {
                        progressFill.style.width = progress + '%';
                    } else {
                        clearInterval(interval);
                        isPlaying = false;
                        playButton.innerHTML = '▶️';
                        progress = 0;
                        progressFill.style.width = '0%';
                        
                        // Envoyer la progression au serveur
                        updateWatchProgress();
                    }
                }, 1000);
            } else {
                isPlaying = false;
                playButton.innerHTML = '▶️';
                clearInterval(interval);
            }
        });
        
        // Contrôle de la barre de progression
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.addEventListener('click', function(e) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const width = rect.width;
                progress = (x / width) * 100;
                progressFill.style.width = progress + '%';
            });
        }
    }
}

// Mise à jour de la progression de visionnage
function updateWatchProgress() {
    const contentId = document.querySelector('[data-content-id]')?.dataset.contentId;
    const progressFill = document.querySelector('.progress-fill');
    
    if (contentId && progressFill) {
        const progress = parseFloat(progressFill.style.width) || 0;
        
        fetch('/api/watch-progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content_id: parseInt(contentId),
                progress: progress
            })
        }).then(response => response.json())
        .then(data => {
            console.log('Progression sauvegardée');
        });
    }
}

// Gestion des formulaires
function initForms() {
    // Validation des formulaires
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#e50914';
                } else {
                    field.style.borderColor = '#444';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Veuillez remplir tous les champs requis', 'error');
            }
        });
    });
}

// Recherche en temps réel
function initSearch() {
    const searchInput = document.querySelector('#search-input');
    const searchResults = document.querySelector('#search-results');
    
    if (searchInput && searchResults) {
        let timeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            const query = this.value.trim();
            
            if (query.length > 2) {
                timeout = setTimeout(() => {
                    fetch(`/api/search?q=${encodeURIComponent(query)}`)
                        .then(response => response.json())
                        .then(results => {
                            searchResults.innerHTML = '';
                            
                            if (results.length === 0) {
                                searchResults.innerHTML = '<p class="no-results">Aucun résultat trouvé</p>';
                                searchResults.style.display = 'block';
                            } else {
                                results.forEach(item => {
                                    const div = document.createElement('div');
                                    div.className = 'search-item';
                                    div.innerHTML = `
                                        <a href="/player/${item.id}">
                                            <strong>${item.title}</strong>
                                            <span class="badge badge-${item.is_premium ? 'premium' : 'free'}">
                                                ${item.is_premium ? 'Premium' : 'Gratuit'}
                                            </span>
                                            <span class="category-tag">${item.category}</span>
                                        </a>
                                    `;
                                    searchResults.appendChild(div);
                                });
                                searchResults.style.display = 'block';
                            }
                        });
                }, 300);
            } else {
                searchResults.style.display = 'none';
                searchResults.innerHTML = '';
            }
        });
        
        // Fermer les résultats lors d'un clic ailleurs
        document.addEventListener('click', function(e) {
            if (!searchResults.contains(e.target) && e.target !== searchInput) {
                searchResults.style.display = 'none';
            }
        });
    }
}

// Animations
function initAnimations() {
    // Animation des cartes au scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.content-card, .plan-card, .profile-card').forEach(card => {
        observer.observe(card);
    });
    
    // Animation du compteur dans l'admin
    animateCounters();
}

// Animation des compteurs
function animateCounters() {
    const counters = document.querySelectorAll('.stat-value[data-target]');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000;
        const start = 0;
        const startTime = performance.now();
        
        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const value = Math.floor(progress * target);
            
            counter.textContent = value;
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        }
        
        requestAnimationFrame(updateCounter);
    });
}

// Notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '10000';
    notification.style.maxWidth = '300px';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Gestion du mode plein écran pour le lecteur vidéo
function toggleFullscreen() {
    const videoContainer = document.querySelector('.video-simulator');
    
    if (videoContainer) {
        if (!document.fullscreenElement) {
            videoContainer.requestFullscreen().catch(err => {
                console.log('Erreur plein écran:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }
}

// Confirmation de suppression
function confirmDelete(message = 'Êtes-vous sûr de vouloir supprimer cet élément ?') {
    return confirm(message);
}

// Gestion des likes/favoris (fonctionnalité future)
function toggleLike(contentId) {
    const likeButton = document.querySelector(`[data-like="${contentId}"]`);
    if (likeButton) {
        likeButton.classList.toggle('liked');
        const isLiked = likeButton.classList.contains('liked');
        
        // Animation de like
        if (isLiked) {
            likeButton.style.transform = 'scale(1.2)';
            setTimeout(() => {
                likeButton.style.transform = 'scale(1)';
            }, 200);
        }
    }
}

// Export des fonctions pour utilisation globale
window.toggleFullscreen = toggleFullscreen;
window.confirmDelete = confirmDelete;
window.toggleLike = toggleLike;