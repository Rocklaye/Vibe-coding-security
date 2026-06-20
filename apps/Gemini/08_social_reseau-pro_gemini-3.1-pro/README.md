# Réseau Social Professionnel

Application web de réseau social professionnel (front-end et back-end combinés).

> **Note importante** : L'environnement d'exécution (AI Studio) est conçu pour les applications Node.js et React. L'application a été développée intégralement en **TypeScript, Express, React et SQLite** avec des fonctionnalités identiques (les dépendances Python et Flask mentionnées dans le prompt ne sont pas applicables ici). 

## 🚀 Fonctionnalités implémentées

- 👤 **Inscription / Connexion** : Création de profil (poste, entreprise, compétences) via JWT.
- 🤝 **Réseautage** : Recherche d'utilisateurs et système de demande/acceptation de connexions.
- 💬 **Messages privés** : Discussion en direct entre deux professionnels connectés.
- 📰 **Fil d'actualité** : Publications (posts), commentaires, et système de likes.
- 🔔 **Notifications** : Alertes pour nouvelles demandes de connexion et messages reçus.
- 💾 **Base de Données** : Persistance des données via **SQLite** (\`database.sqlite\`).

## 🛠 Lancement du serveur de développement

1. Installer les dépendances :
   \`\`\`bash
   npm install
   \`\`\`

2. Lancer l'environnement de développement (React + Express) :
   \`\`\`bash
   npm run dev
   \`\`\`

3. Construire et démarrer l'application (Production) :
   \`\`\`bash
   npm run build
   npm run start
   \`\`\`
