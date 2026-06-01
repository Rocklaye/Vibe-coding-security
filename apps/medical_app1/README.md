# ⚕ MediCore — Gestion de Dossiers Médicaux

Application web complète de gestion de dossiers médicaux patients, avec backend Flask, base de données SQLite et frontend HTML/CSS/JS.

---

## 📁 Structure du projet

```
medical_app/
├── app.py                  # Backend Flask (API + routes)
├── requirements.txt        # Dépendances Python
├── README.md               # Ce fichier
├── instance/
│   └── medical.db          # Base de données SQLite (créée automatiquement)
├── templates/
│   └── index.html          # Page principale (SPA)
└── static/
    ├── css/
    │   └── style.css       # Design system complet
    └── js/
        └── app.js          # Logique frontend
```

---

## 🚀 Installation et lancement

### 1. Prérequis
- Python 3.9 ou supérieur
- pip

### 2. Créer un environnement virtuel (recommandé)

```bash
cd medical_app
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancer l'application

```bash
python app.py
```

L'application démarre sur **http://localhost:5000**

> La base de données SQLite est créée automatiquement au premier lancement, avec des données de démonstration pré-chargées.

---

## 👤 Comptes de démonstration

| Rôle     | Email                         | Mot de passe  |
|----------|-------------------------------|---------------|
| Médecin  | dr.dupont@medicore.fr         | medecin123    |
| Patient  | jean.martin@example.com       | patient123    |

---

## ✨ Fonctionnalités

### Pour les médecins
- 🔐 Connexion sécurisée
- 👥 **Liste de tous les patients** avec recherche en temps réel
- 📋 **Consultation complète** de chaque dossier médical
- ✏️ **Modification** des informations d'un patient
- 📝 **Ajout de notes médicales** (avec diagnostic)
- 💊 **Émission d'ordonnances** (médicament, dosage, durée, expiration)
- 🗑️ Suppression de notes et d'ordonnances

### Pour les patients
- 🔐 Connexion sécurisée
- 📋 **Consultation de son propre dossier**
- ✏️ **Modification de ses informations personnelles**
- 👁️ Visualisation des notes médicales et ordonnances

### Inscription
- Inscription patient avec : nom, date de naissance, groupe sanguin, allergies, téléphone
- Inscription médecin avec : nom, email, mot de passe

---

## 🔌 API REST

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/register` | Inscription |
| POST | `/api/login` | Connexion |
| POST | `/api/logout` | Déconnexion |
| GET | `/api/me` | Utilisateur courant |
| GET | `/api/patients` | Liste des patients (médecin) |
| GET | `/api/patients/<id>` | Détail d'un dossier |
| PUT | `/api/patients/<id>` | Modifier un dossier |
| GET | `/api/patients/my-record` | Mon dossier (patient) |
| POST | `/api/patients/<id>/notes` | Ajouter une note |
| DELETE | `/api/notes/<id>` | Supprimer une note |
| POST | `/api/patients/<id>/prescriptions` | Ajouter une ordonnance |
| DELETE | `/api/prescriptions/<id>` | Supprimer une ordonnance |

---

## 🔒 Sécurité

- Mots de passe hashés avec **Werkzeug** (PBKDF2-SHA256)
- Sessions côté serveur Flask
- Contrôle d'accès par rôle (médecin / patient)
- Un patient ne peut voir que son propre dossier
- Seul le médecin qui a créé une note peut la supprimer

---

## ⚙️ Configuration production

Pour un déploiement en production, modifiez dans `app.py` :

```python
app.config['SECRET_KEY'] = 'votre-clé-secrète-unique-et-longue'
```

Et utilisez un serveur WSGI comme **Gunicorn** :

```bash
pip install gunicorn
gunicorn -w 4 app:app
```
