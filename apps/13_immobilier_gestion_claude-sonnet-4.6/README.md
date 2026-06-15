# t13 — GestImmo : Gestion locative immobilière

Application web complète de gestion locative générée par **claude-sonnet-4-6**.

Stack : Python 3.11+ · Flask · Flask-SQLAlchemy · SQLite · HTML/CSS/JS

---

## Démarrage rapide

```bash
cd t13_immobilier_gestion_claude-sonnet-4.6

python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

python app.py
# → http://localhost:8080
```

La base de données `gestimmo.db` et le dossier `static/uploads/` sont créés automatiquement.

---

## Fonctionnalités

| Module | Fonctionnalités |
|---|---|
| **Authentification** | Inscription / connexion, deux rôles : Propriétaire & Locataire |
| **Biens** | CRUD complet, photos multiples, type/surface/loyer/charges/dépôt |
| **Locataires** | Création avec accès espace locataire, fiche détaillée |
| **Baux** | Création, résiliation, type (vide/meublé/commercial), date de paiement |
| **Paiements** | Enregistrement, historique par bien, suivi mensuel, alertes retard |
| **Quittances** | Génération HTML imprimable (PDF via navigateur), numérotation automatique |
| **États des lieux** | Entrée & sortie, état général, notes, galerie photos |
| **Espace locataire** | Dashboard, historique paiements, documents, quittances |

---

## Structure des fichiers

```
t13_immobilier_gestion_claude-sonnet-4.6/
├── app.py                        # Flask : modèles + toutes les routes
├── requirements.txt
├── README.md
├── static/
│   ├── css/style.css             # Design professionnel (sidebar navy)
│   ├── js/main.js                # Prévisualisation photos, auto-fill
│   └── uploads/                  # Photos uploadées (créé automatiquement)
└── templates/
    ├── base.html                 # Layout sidebar (owner / tenant)
    ├── login.html / register.html
    ├── owner_dashboard.html      # Stats, alertes loyers en retard
    ├── properties.html / property_detail.html / property_form.html
    ├── tenants.html / tenant_detail.html / tenant_form.html
    ├── leases.html / lease_form.html
    ├── payments.html / payment_form.html
    ├── inspections.html / inspection_form.html / inspection_detail.html
    ├── receipt.html              # Quittance imprimable (print → PDF)
    ├── tenant_dashboard.html
    ├── tenant_payments.html
    └── tenant_documents.html
```

---

## Utilisation typique (flux propriétaire)

1. **S'inscrire** comme propriétaire
2. **Ajouter un bien** (Mes biens → + Ajouter)
3. **Créer un locataire** (Locataires → + Nouveau)
4. **Créer un bail** en liant le bien et le locataire
5. **Encaisser les loyers** chaque mois (Paiements → + Encaisser)
6. **Générer des quittances** (clic sur "Quittance" → Imprimer → PDF)
7. **Réaliser un état des lieux** en début et fin de bail

## Accès locataire

Le locataire peut se connecter avec les identifiants créés par le propriétaire.  
Il accède à : son logement, son historique de paiements, ses quittances, ses états des lieux.

---

## Production

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

Utilisez Gunicorn ou Waitress pour déployer en production. Désactivez `debug=True`.
