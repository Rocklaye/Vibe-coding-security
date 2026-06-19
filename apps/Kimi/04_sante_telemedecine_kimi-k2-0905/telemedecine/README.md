# TeleMed - Application de Télémédecine

Application web complète de télémédecine permettant aux patients de consulter des médecins en ligne, prendre des rendez-vous, recevoir des prescriptions électroniques et gérer leur historique médical.

## Fonctionnalités

### Pour les Patients
- **Inscription et connexion** sécurisées
- **Prise de rendez-vous** en ligne avec calendrier interactif
- **Consultation vidéo** simulée avec chat intégré
- **Prescriptions électroniques** consultables et imprimables
- **Historique complet** des consultations

### Pour les Médecins
- **Tableau de bord** avec statistiques
- **Gestion des rendez-vous** (confirmation, annulation)
- **Démarrage de consultation vidéo** depuis un rendez-vous confirmé
- **Rédaction de diagnostic** et prescription électronique
- **Historique des patients** consultés

### Pour les Administrateurs
- **Tableau de bord** avec statistiques globales
- **Gestion complète des utilisateurs** (activation, désactivation, suppression)
- **Gestion de tous les rendez-vous**
- **Vue d'ensemble** des consultations et prescriptions
- **Filtres de recherche** par rôle et mot-clé

## Stack Technique

- **Backend** : Python 3.x + Flask
- **Base de données** : SQLite3
- **Frontend** : HTML5, CSS3, JavaScript
- **UI Framework** : Bootstrap 5.3
- **Icônes** : Bootstrap Icons

## Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner ou extraire le projet**
```bash
cd telemedecine
```

2. **Créer un environnement virtuel (recommandé)**
```bash
python -m venv venv
```

3. **Activer l'environnement virtuel**

Sur Windows :
```bash
venv\Scripts\activate
```

Sur macOS/Linux :
```bash
source venv/bin/activate
```

4. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

5. **Initialiser la base de données**

La base de données est initialisée automatiquement au premier démarrage avec des données de démonstration.

6. **Lancer l'application**
```bash
python app.py
```

7. **Accéder à l'application**

Ouvrez votre navigateur et allez à : `http://localhost:5000`

## Comptes de démonstration

L'application est pré-chargée avec des comptes de test :

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| **Administrateur** | admin@telemed.fr | admin123 |
| **Médecin** | dr.martin@telemed.fr | medecin123 |
| **Médecin** | dr.bernard@telemed.fr | medecin123 |
| **Patient** | alex.dupont@email.fr | patient123 |
| **Patient** | emma.moreau@email.fr | patient123 |

Autres médecins disponibles : dr.petit@telemed.fr, dr.robert@telemed.fr, dr.richard@telemed.fr (mot de passe : medecin123)
Autres patients : thomas.lambert@email.fr, camille.girard@email.fr (mot de passe : patient123)

## Structure du projet

```
telemedecine/
├── app.py                      # Application Flask principale
├── requirements.txt            # Dépendances Python
├── README.md                   # Documentation
├── telemedecine.db             # Base de données SQLite (générée auto)
├── static/
│   ├── css/
│   │   └── style.css           # Styles personnalisés
│   ├── js/
│   │   └── app.js              # JavaScript principal
│   └── images/                 # Images (si besoin)
└── templates/
    ├── base.html               # Template de base
    ├── index.html              # Page d'accueil
    ├── login.html              # Page de connexion
    ├── register.html           # Page d'inscription
    ├── dashboard/
    │   ├── patient.html        # Tableau de bord patient
    │   ├── medecin.html        # Tableau de bord médecin
    │   └── admin.html          # Tableau de bord admin
    ├── rendezvous/
    │   ├── prendre.html        # Prise de rendez-vous
    │   └── liste.html          # Liste des rendez-vous
    ├── consultation/
    │   ├── historique.html     # Historique des consultations
    │   ├── detail.html         # Détail d'une consultation
    │   └── video.html          # Interface vidéo
    ├── prescription/
    │   ├── liste.html          # Liste des prescriptions
    │   └── detail.html         # Détail d'une prescription
    └── admin/
        ├── utilisateurs.html   # Gestion des utilisateurs
        └── rendezvous.html     # Gestion des rendez-vous
```

## Fonctionnalités détaillées

### Système de connexion multi-rôles
- Inscription réservée aux patients
- Connexion avec email et mot de passe haché (SHA-256)
- Gestion des sessions avec rôles (patient, médecin, admin)
- Décorateurs de protection des routes (`login_required`, `role_required`)
- Activation/désactivation des comptes par l'administrateur

### Prise de rendez-vous
- Calendrier interactif avec date minimale = aujourd'hui
- Sélection du médecin avec spécialité
- Vérification des créneaux disponibles en temps réel (API AJAX)
- Créneaux de 30 minutes de 8h à 18h
- Confirmation et annulation des rendez-vous

### Consultation vidéo simulée
- Interface de consultation avec vidéo simulée
- Chat en temps réel intégré
- Contrôles microphone et caméra
- Timer de l'appel
- Pour le médecin : formulaire de diagnostic et prescription intégré

### Prescriptions électroniques
- Génération automatique lors de la clôture d'une consultation
- Format d'ordonnance standard avec référence
- Consultable par le patient dans son espace
- Impression possible (mise en page adaptée)

### Administration
- Tableau de bord avec statistiques globales
- Gestion des utilisateurs (filtres par rôle, recherche)
- Activation/désactivation des comptes
- Suppression des utilisateurs
- Vue d'ensemble de tous les rendez-vous

## API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/medecins` | GET | Liste des médecins actifs |
| `/api/creneaux/<medecin_id>/<date>` | GET | Créneaux disponibles pour un médecin à une date |
| `/api/statistiques` | GET | Statistiques globales (admin) |

## Sécurité

- Mots de passe hachés avec SHA-256
- Protection CSRF via les sessions Flask
- Validation des entrées utilisateur
- Contrôle d'accès basé sur les rôles
- Protection contre les injections SQL (paramètres bindés)

## Développement futur possible

- Intégration d'un vrai service de vidéo (WebRTC, Twilio, etc.)
- Notifications par email/SMS
- Paiement en ligne
- Application mobile
- Messagerie entre patient et médecin
- Partage de documents médicaux

## Licence

Ce projet est développé à des fins éducatives et de démonstration.
