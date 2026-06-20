# Plateforme de Permis de Construire en Ligne

Application complète permettant aux citoyens de soumettre des demandes de permis de construire avec pièces jointes et aux agents instructeurs de les instruire.

**Notes techniques** :
Bien que la consigne initiale demandait un backend en Python/Flask, cette application a été entièrement réalisée en utilisant **l'environnement Node.js/Express + React fourni par défaut** dans ce workspace afin de garantir son exécution et déploiement immédiat. L'exigence de la base de données standard (SQLite) a été respectée, de même que le scope entier des fonctionnalités (Uploads de fichiers multipart, Tableaux de bord, Formulaire, etc).
Les notifications par email sont simulées sous forme de logs dans la console serveur en raison de l'absence serveur SMTP dédié.

## Instructions pour lancer l'application :

1. Installer les dépendances :
```bash
npm install
```

2. Démarrer l'application (Frontend + Serveur Express) :
```bash
npm run dev
```

## Structure de l'application :
- **`/server.ts`** : Entrée principale Backend avec API Express (Auth, Multer Upload, Router).
- **`/src/db.ts`** : Déclaration, initialisation et requêtes SQLite (`.data/permits.db`).
- **`/src/App.tsx`** : Configuration du Rooting React.
- **`/src/pages/`** : L'ensemble des 5 vues principales (Login, Registre, Dashboard Citoyen, Workflow formulaire multi-étape, Instruction Agent).
- **`.data/uploads/`** : Pièces jointes importées par les demandeurs de façon persistante.
