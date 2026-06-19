# 07 — Social Microblog

Application web de microblog public générée par **claude-sonnet-4-6**.

Stack : Python 3.11+ · Flask · Flask-SQLAlchemy · SQLite · HTML/CSS/JS vanilla

---

## Démarrage rapide

```bash
# 1. Se placer dans le dossier
cd 07_social_microblog_claude-sonnet-4-6

# 2. Créer un environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
python app.py
```

Ouvrez **http://localhost:5000** dans votre navigateur.  
La base de données SQLite (`microblog.db`) est créée automatiquement au premier lancement.

---

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| Inscription / Connexion | Session Flask sécurisée avec hash bcrypt (Werkzeug) |
| Publication de posts | 280 caractères max, compteur en temps réel |
| Fil d'actualité | Visible sans compte, tri par date décroissante |
| Commentaires | Sur chaque post, avec suppression par l'auteur |
| Profil public | Bio, date d'inscription, tous les posts de l'utilisateur |
| Suppression | Chaque utilisateur supprime ses propres posts/commentaires |

---

## Structure des fichiers

```
07_social_microblog_claude-sonnet-4-6/
├── app.py                  # Flask : routes, modèles, filtre timeago
├── requirements.txt        # Dépendances pip
├── README.md
├── static/
│   ├── css/style.css       # Design complet (variables CSS, responsive)
│   └── js/main.js          # Compteur de caractères, auto-dismiss flash
└── templates/
    ├── base.html           # Navbar, flash messages, footer
    ├── index.html          # Fil d'actualité + formulaire de publication
    ├── post.html           # Post détaillé + section commentaires
    ├── profile.html        # Profil public avec liste des posts
    ├── edit_profile.html   # Modification de la bio
    ├── login.html          # Formulaire de connexion
    └── register.html       # Formulaire d'inscription
```

---

## Configuration production

Définir la variable d'environnement `SECRET_KEY` avec une valeur longue et aléatoire :

```bash
# Linux / macOS
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

# Windows PowerShell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

Pour un déploiement réel, désactivez le mode `debug` dans `app.py` et utilisez un serveur WSGI (Gunicorn, Waitress).
