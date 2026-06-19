import { drizzle } from "drizzle-orm/mysql2";
import { createConnection } from "mysql2";
import * as schema from "./schema";

const connection = createConnection(process.env.DATABASE_URL || "");
const db = drizzle(connection, { schema, mode: "planetscale" });

async function seed() {
  console.log("Seeding database...");

  // Seed courses
  const coursesData = [
    {
      title: "Introduction à la Data Science",
      description: "Apprenez les fondamentaux de l'analyse de données, du machine learning et de la visualisation. Ce cours couvre Python, pandas, numpy et scikit-learn.",
      image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80",
      category: "Data Science",
      level: "debutant" as const,
      duration: "12 semaines",
      instructorId: 1,
      isPublished: true,
    },
    {
      title: "Littérature Française Contemporaine",
      description: "Explorez les œuvres majeures de la littérature française du XXe siècle jusqu'à nos jours. Analysez les thèmes, styles et mouvements littéraires.",
      image: "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&q=80",
      category: "Littérature",
      level: "intermediaire" as const,
      duration: "8 semaines",
      instructorId: 1,
      isPublished: true,
    },
    {
      title: "Développement Web Full-Stack",
      description: "Maîtrisez le développement web moderne avec React, Node.js, TypeScript et les bases de données. Devenez un développeur full-stack complet.",
      image: "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&q=80",
      category: "Programmation",
      level: "avance" as const,
      duration: "16 semaines",
      instructorId: 1,
      isPublished: true,
    },
    {
      title: "Design Thinking et Innovation",
      description: "Apprenez la méthodologie du design thinking pour résoudre des problèmes complexes et innover dans votre domaine d'activité.",
      image: "https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=800&q=80",
      category: "Design",
      level: "debutant" as const,
      duration: "6 semaines",
      instructorId: 1,
      isPublished: true,
    },
  ];

  for (const course of coursesData) {
    await db.insert(schema.courses).values(course);
  }
  console.log("Courses seeded");

  // Seed modules and lessons for each course
  const courseModules = [
    // Data Science modules
    {
      courseIndex: 0,
      modules: [
        {
          title: "Fondamentaux de Python",
          description: "Maîtrisez les bases de Python pour la data science",
          lessons: [
            { title: "Introduction à Python", content: "Variables, types de données, opérateurs de base.", duration: 45 },
            { title: "Structures de contrôle", content: "Conditions, boucles, compréhensions.", duration: 60 },
            { title: "Fonctions et modules", content: "Définition de fonctions, importation de modules.", duration: 50 },
          ],
        },
        {
          title: "Analyse de données avec Pandas",
          description: "Manipulez et analysez des données efficacement",
          lessons: [
            { title: "DataFrames et Séries", content: "Création et manipulation de DataFrames.", duration: 55 },
            { title: "Nettoyage de données", content: "Gestion des valeurs manquantes, doublons.", duration: 65 },
            { title: "Agrégation et groupby", content: "Opérations d'agrégation, pivot tables.", duration: 50 },
          ],
        },
        {
          title: "Visualisation de données",
          description: "Créez des visualisations percutantes",
          lessons: [
            { title: "Matplotlib - Graphiques de base", content: "Line plots, bar charts, scatter plots.", duration: 50 },
            { title: "Seaborn - Visualisations avancées", content: "Heatmaps, pair plots, distribution plots.", duration: 60 },
          ],
        },
      ],
    },
    // Literature modules
    {
      courseIndex: 1,
      modules: [
        {
          title: "Le Nouveau Roman",
          description: "Découvrez le mouvement du Nouveau Roman",
          lessons: [
            { title: "Alain Robbe-Grillet", content: "L'analyse des œuvres de Robbe-Grillet.", duration: 45 },
            { title: "Nathalie Sarraute", content: "Les tropismes et l'écriture sarrautienne.", duration: 50 },
          ],
        },
        {
          title: "La Littérature Engagée",
          description: "Sartre, Camus et l'engagement littéraire",
          lessons: [
            { title: "Jean-Paul Sartre", content: "L'existentialisme et la littérature engagée.", duration: 55 },
            { title: "Albert Camus", content: "L'absurde et la révolte chez Camus.", duration: 60 },
          ],
        },
      ],
    },
    // Web Dev modules
    {
      courseIndex: 2,
      modules: [
        {
          title: "Frontend avec React",
          description: "Construisez des interfaces modernes",
          lessons: [
            { title: "Composants et JSX", content: "Création de composants, syntaxe JSX.", duration: 50 },
            { title: "Hooks et State Management", content: "useState, useEffect, useContext.", duration: 65 },
            { title: "Routing et Navigation", content: "React Router, navigation SPA.", duration: 45 },
          ],
        },
        {
          title: "Backend avec Node.js",
          description: "Créez des API robustes",
          lessons: [
            { title: "Express.js - Bases", content: "Routes, middleware, gestion des requêtes.", duration: 55 },
            { title: "Bases de données SQL", content: "Modélisation, requêtes, ORM.", duration: 60 },
            { title: "Authentification JWT", content: "Tokens JWT, sécurisation des routes.", duration: 50 },
          ],
        },
      ],
    },
    // Design Thinking modules
    {
      courseIndex: 3,
      modules: [
        {
          title: "Phase d'Empathie",
          description: "Comprenez vos utilisateurs",
          lessons: [
            { title: "Entretiens utilisateurs", content: "Techniques d'interview, personas.", duration: 40 },
            { title: "Cartographie d'expérience", content: "Journey maps, empathy maps.", duration: 35 },
          ],
        },
        {
          title: "Phase de Prototypage",
          description: "Matérialisez vos idées",
          lessons: [
            { title: "Wireframing", content: "Mockups basse fidélité, paper prototyping.", duration: 45 },
            { title: "Tests utilisateurs", content: "Méthodologie de test, itérations.", duration: 50 },
          ],
        },
      ],
    },
  ];

  // Get inserted courses
  const insertedCourses = await db.select().from(schema.courses);

  for (const cm of courseModules) {
    const course = insertedCourses[cm.courseIndex];
    if (!course) continue;

    for (let mi = 0; mi < cm.modules.length; mi++) {
      const mod = cm.modules[mi];
      const [moduleResult] = await db.insert(schema.modules).values({
        courseId: course.id,
        title: mod.title,
        description: mod.description,
        order: mi,
      });

      const moduleId = moduleResult.insertId;

      for (let li = 0; li < mod.lessons.length; li++) {
        const lesson = mod.lessons[li];
        await db.insert(schema.lessons).values({
          moduleId: Number(moduleId),
          title: lesson.title,
          content: lesson.content,
          duration: lesson.duration,
          order: li,
        });
      }
    }
  }
  console.log("Modules and lessons seeded");

  // Seed assignments
  const assignmentsData = [
    { courseIndex: 0, title: "Analyse exploratoire de données", description: "Réalisez une EDA complète sur un jeu de données fourni.", maxScore: 100 },
    { courseIndex: 0, title: "Projet de Machine Learning", description: "Construisez un modèle de prédiction et évaluez ses performances.", maxScore: 100 },
    { courseIndex: 1, title: "Dissertation littéraire", description: "Rédigez une dissertation sur un thème au choix.", maxScore: 100 },
    { courseIndex: 2, title: "Application Full-Stack", description: "Développez une application complète avec React et Node.js.", maxScore: 100 },
    { courseIndex: 3, title: "Projet de Design Thinking", description: "Appliquez la méthodologie à un problème réel.", maxScore: 100 },
  ];

  for (const assign of assignmentsData) {
    const course = insertedCourses[assign.courseIndex];
    if (!course) continue;
    await db.insert(schema.assignments).values({
      courseId: course.id,
      title: assign.title,
      description: assign.description,
      maxScore: assign.maxScore,
    });
  }
  console.log("Assignments seeded");

  // Seed forum topics
  const forumTopicsData = [
    { courseIndex: 0, title: "Bienvenue dans le cours de Data Science !", content: "Présentez-vous et partagez vos objectifs d'apprentissage." },
    { courseIndex: 0, title: "Aide avec Pandas - DataFrames", content: "J'ai du mal à comprendre le mécanisme de filtrage avancé." },
    { courseIndex: 1, title: "Discussion sur L'Étranger de Camus", content: "Quelle est votre interprétation de la célèbre phrase 'Aujourd'hui, maman est morte' ?" },
    { courseIndex: 2, title: "Ressources complémentaires React", content: "Partagez vos meilleures ressources pour apprendre React." },
  ];

  for (const topic of forumTopicsData) {
    const course = insertedCourses[topic.courseIndex];
    if (!course) continue;
    await db.insert(schema.forumTopics).values({
      courseId: course.id,
      userId: 1,
      title: topic.title,
      content: topic.content,
    });
  }
  console.log("Forum topics seeded");

  console.log("Seeding complete!");
  connection.end();
}

seed().catch(console.error);
