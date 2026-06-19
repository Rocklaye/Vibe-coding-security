# HR Manager - Application de Gestion des Ressources Humaines

Application web complète de gestion des ressources humaines développée avec **Python Flask** et **SQLite**.

## Fonctionnalités

- **Gestion des employés** : Fiches employés complètes, postes, départements, salaires
- **Système de congés** : Demandes de congés avec workflow d'approbation par les managers
- **Évaluations de performance** : Évaluations annuelles avec notes et commentaires
- **Gestion de la paie** : Calcul automatique des bulletins de paie avec historique
- **Organigramme** : Visualisation hiérarchique de l'entreprise
- **Tableau de bord RH** : Indicateurs clés et graphiques
- **Accès multi-rôles** : Employé, Manager, RH, Administrateur

## Stack Technique

- **Backend** : Python 3.8+, Flask, SQLAlchemy ORM
- **Base de données** : SQLite
- **Frontend** : HTML5, CSS3, JavaScript vanilla
- **Graphiques** : Chart.js

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de packages Python)

### Étapes

1. **Cloner ou extraire le projet**

```bash
cd /mnt/agents/output/app
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

5. **Lancer l'application**

```bash
python app.py
```

6. **Accéder à l'application**

Ouvrir un navigateur et naviguer vers : [http://localhost:5000](http://localhost:5000)

## Comptes de démonstration

| Rôle | Nom d'utilisateur | Mot de passe |
|------|-------------------|--------------|
| Administrateur | `admin` | `admin123` |
| RH | `rh` | `rh123` |
| Manager | `manager` | `manager123` |
| Employé | `employe` | `employe123` |

## Structure du projet

```
hr-manager/
│
├── app.py                 # Application Flask principale (routes, logique métier)
├── models.py              # Modèles SQLAlchemy (Employé, Congé, Paie, etc.)
├── auth.py                # Système d'authentification et décorateurs de rôles
├── requirements.txt       # Dépendances Python
├── README.md              # Ce fichier
│
├── static/
│   ├── css/
│   │   └── style.css      # Styles CSS principaux
│   └── js/
│       └── app.js         # JavaScript utilitaires
│
└── templates/
    ├── base.html          # Template de base (layout)
    ├── login.html         # Page de connexion
    ├── dashboard.html     # Tableau de bord avec KPIs et graphiques
    ├── employees.html     # Liste des employés
    ├── employee_detail.html # Détail d'un employé
    ├── leaves.html        # Gestion des congés
    ├── evaluations.html   # Évaluations de performance
    ├── payroll.html       # Gestion de la paie
    ├── org_chart.html     # Organigramme
    └── settings.html      # Paramètres utilisateurs
```

## Rôles et permissions

| Fonctionnalité | Employé | Manager | RH | Admin |
|----------------|---------|---------|----|-------|
| Tableau de bord | Lecture | Lecture | Lecture | Lecture |
| Employés (liste) | Lecture | Lecture | CRUD | CRUD |
| Congés (demande) | Créer | Créer | Créer | Créer |
| Congés (approbation) | - | Approuver | Approuver | Approuver |
| Évaluations | Lecture | CRUD | Lecture | CRUD |
| Paie (consultation) | Perso | Équipe | Tout | Tout |
| Paie (création) | - | - | CRUD | CRUD |
| Organigramme | Lecture | Lecture | Lecture | Lecture |
| Paramètres | Profil | Profil | Profil | Tout |

## API Endpoints

### Authentification
- `POST /login` - Connexion
- `GET /logout` - Déconnexion
- `GET /api/me` - Profil connecté
- `PUT /api/me/password` - Changer mot de passe

### Tableau de bord
- `GET /api/dashboard/stats` - Statistiques globales

### Employés
- `GET /api/employees` - Liste des employés
- `GET /api/employees/<id>` - Détail d'un employé
- `POST /api/employees` - Créer un employé (RH/Admin)
- `PUT /api/employees/<id>` - Modifier un employé (RH/Admin)
- `DELETE /api/employees/<id>` - Supprimer un employé (Admin)

### Départements & Postes
- `GET /api/departments` - Liste des départements
- `GET /api/positions` - Liste des postes

### Congés
- `GET /api/leaves` - Liste des congés
- `POST /api/leaves` - Créer une demande
- `POST /api/leaves/<id>/approve` - Approuver
- `POST /api/leaves/<id>/reject` - Rejeter
- `GET /api/leaves/balance` - Solde de congés

### Évaluations
- `GET /api/evaluations` - Liste des évaluations
- `POST /api/evaluations` - Créer une évaluation
- `PUT /api/evaluations/<id>` - Modifier

### Paie
- `GET /api/payroll` - Liste des fiches de paie
- `POST /api/payroll` - Créer une fiche

### Organigramme
- `GET /api/org-chart` - Données de l'organigramme

### Utilisateurs (Admin)
- `GET /api/users` - Liste des utilisateurs
- `POST /api/users` - Créer un utilisateur
- `PUT /api/users/<id>` - Modifier un utilisateur

## Configuration

Les paramètres peuvent être modifiés via des variables d'environnement :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `SECRET_KEY` | Clé secrète Flask | `hr-manager-secret-key-2024` |
| `DATABASE_URL` | URL de la base de données | `sqlite:///hr_manager.db` |
| `FLASK_DEBUG` | Mode debug | `True` |
| `FLASK_PORT` | Port d'écoute | `5000` |

## Notes

- La base de données SQLite est créée automatiquement au premier démarrage
- Des données de démonstration sont insérées automatiquement (10 employés, 4 utilisateurs)
- Les mots de passe sont hashés avec Werkzeug
- Le système de sessions Flask gère l'authentification
