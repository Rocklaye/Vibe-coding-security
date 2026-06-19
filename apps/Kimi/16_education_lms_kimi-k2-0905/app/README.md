# Aura Espace Formation - LMS

Aura Espace Formation est une plateforme LMS (Learning Management System) haut de gamme dédiée à la formation continue. Elle permet aux étudiants de s'inscrire à des cours, suivre leur progression, soumettre des devoirs, et obtenir des certificats de réussite.

## Fonctionnalités

- **Inscription et connexion** : Authentification OAuth 2.0 avec gestion multi-rôles (étudiant, enseignant, admin)
- **Catalogue de cours** : Parcourir, rechercher et filtrer les cours par catégorie et niveau
- **Inscription aux cours** : S'inscrire à un cours et suivre sa progression en temps réel
- **Contenu pédagogique** : Accéder aux modules et leçons avec navigation entre leçons
- **Devoirs et évaluations** : Consulter les devoirs, soumettre des réponses et voir les notes
- **Suivi de progression** : Barre de progression par cours avec pourcentage de complétion
- **Certificats** : Génération de certificats de réussite à la fin d'un cours
- **Forum de discussion** : Créer des sujets et répondre dans des forums par cours
- **Administration** : Gestion des cours (CRUD) et statistiques de la plateforme

## Stack Technique

- **Frontend** : React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend** : Hono + tRPC + Drizzle ORM + MySQL
- **Authentification** : OAuth 2.0 (Kimi)

## Prérequis

- Node.js 20+
- MySQL

## Installation

1. Cloner le projet :
```bash
git clone <repo-url>
cd aura-lms
```

2. Installer les dépendances :
```bash
npm install
```

3. Configurer les variables d'environnement dans `.env` :
```env
DATABASE_URL=mysql://user:password@host:port/database
APP_ID=votre_app_id
APP_SECRET=votre_app_secret
VITE_APP_ID=votre_app_id
VITE_KIMI_AUTH_URL=https://auth.kimi.com
```

4. Initialiser la base de données :
```bash
npm run db:push
```

5. Peupler la base de données (optionnel) :
```bash
npx tsx db/seed.ts
```

## Lancement

### Développement
```bash
npm run dev
```
Le serveur démarre sur `http://localhost:3000`

### Production
```bash
npm run build
npm start
```

## Structure du Projet

```
├── api/                    # Backend (Hono + tRPC)
│   ├── routers/            # Routeurs tRPC
│   ├── middleware.ts       # Middleware (auth, roles)
│   └── auth-router.ts      # Router d'authentification
├── db/                     # Base de données (Drizzle ORM)
│   ├── schema.ts           # Schéma des tables
│   ├── relations.ts        # Relations entre tables
│   └── seed.ts             # Script de seed
├── src/
│   ├── pages/              # Pages React
│   ├── components/         # Composants partagés
│   ├── hooks/              # Hooks personnalisés
│   └── providers/          # Providers (tRPC)
├── contracts/              # Types partagés
└── dist/                   # Build de production
```

## Commandes Disponibles

| Commande | Description |
|----------|-------------|
| `npm run dev` | Serveur de développement avec HMR |
| `npm run build` | Build pour production |
| `npm start` | Serveur de production |
| `npm run check` | Vérification TypeScript |
| `npm run db:push` | Synchroniser le schéma avec la BDD |
| `npm run db:generate` | Générer les migrations |
| `npm run db:migrate` | Appliquer les migrations |

## Rôles Utilisateurs

- **user** : Étudiant - peut s'inscrire aux cours, suivre les leçons, soumettre des devoirs
- **teacher** : Enseignant - peut créer du contenu et noter les devoirs
- **admin** : Administrateur - accès complet à la gestion de la plateforme

## Licence

© 2024 Aura Espace Formation. Tous droits réservés.
