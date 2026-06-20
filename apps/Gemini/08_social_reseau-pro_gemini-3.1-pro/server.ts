import express from "express";
import path from "path";
import cors from "cors";
import { createServer as createViteServer } from "vite";
import { open } from "sqlite";
import sqlite3 from "sqlite3";
import jwt from "jsonwebtoken";

const JWT_SECRET = process.env.JWT_SECRET || "fallback-secret-12345";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());
  app.use(cors());

  // Database initialization
  const db = await open({
    filename: "./database.sqlite",
    driver: sqlite3.Database,
  });

  await db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE,
      password TEXT,
      name TEXT,
      job_title TEXT,
      company TEXT,
      skills TEXT
    );
    CREATE TABLE IF NOT EXISTS connections (
      requester_id INTEGER,
      receiver_id INTEGER,
      status TEXT, -- 'pending', 'accepted'
      PRIMARY KEY (requester_id, receiver_id)
    );
    CREATE TABLE IF NOT EXISTS posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      content TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS comments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      post_id INTEGER,
      user_id INTEGER,
      content TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS likes (
      post_id INTEGER,
      user_id INTEGER,
      PRIMARY KEY (post_id, user_id)
    );
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sender_id INTEGER,
      receiver_id INTEGER,
      content TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      content TEXT,
      is_read INTEGER DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  // Auth Middleware
  const authenticate = (req: express.Request, res: express.Response, next: express.NextFunction) => {
    const token = req.headers.authorization?.split(" ")[1];
    if (!token) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as { id: number };
      (req as any).userId = decoded.id;
      next();
    } catch {
      res.status(401).json({ error: "Invalid token" });
    }
  };

  // Auth API
  app.post("/api/register", async (req, res) => {
    const { email, password, name, jobTitle, company, skills } = req.body;
    try {
      const result = await db.run(
        "INSERT INTO users (email, password, name, job_title, company, skills) VALUES (?, ?, ?, ?, ?, ?)",
        [email, password, name, jobTitle, company, skills]
      );
      res.json({ id: result.lastID });
    } catch (err: any) {
      res.status(400).json({ error: err.message });
    }
  });

  app.post("/api/login", async (req, res) => {
    const { email, password } = req.body;
    const user = await db.get("SELECT * FROM users WHERE email = ? AND password = ?", [email, password]);
    if (user) {
      const token = jwt.sign({ id: user.id }, JWT_SECRET);
      res.json({ token, user: { id: user.id, name: user.name, jobTitle: user.job_title } });
    } else {
      res.status(401).json({ error: "Invalid credentials" });
    }
  });

  // Profile Search
  app.get("/api/users", authenticate, async (req, res) => {
    const q = req.query.q ? `%${req.query.q}%` : "%%";
    const users = await db.all(
      "SELECT id, name, job_title as jobTitle, company, skills FROM users WHERE name LIKE ? OR skills LIKE ? LIMIT 20",
      [q, q]
    );
    res.json(users);
  });

  // Connections
  app.post("/api/connections", authenticate, async (req, res) => {
    const { receiverId } = req.body;
    const userId = (req as any).userId;
    await db.run("INSERT INTO connections (requester_id, receiver_id, status) VALUES (?, ?, 'pending') ON CONFLICT DO NOTHING", [userId, receiverId]);
    await db.run("INSERT INTO notifications (user_id, content) SELECT name || ' vous a envoyé une demande de connexion.', ? FROM users WHERE id = ?", [receiverId, userId]);
    res.json({ success: true });
  });

  app.post("/api/connections/:id/accept", authenticate, async (req, res) => {
    const requesterId = req.params.id;
    const userId = (req as any).userId;
    await db.run("UPDATE connections SET status = 'accepted' WHERE requester_id = ? AND receiver_id = ?", [requesterId, userId]);
    await db.run("INSERT INTO notifications (user_id, content) SELECT name || ' a accepté votre demande.', ? FROM users WHERE id = ?", [requesterId, userId]);
    res.json({ success: true });
  });

  app.get("/api/connections", authenticate, async (req, res) => {
    const userId = (req as any).userId;
    const connections = await db.all(`
      SELECT u.id, u.name, u.job_title as jobTitle, c.status, c.requester_id as requesterId 
      FROM connections c 
      JOIN users u ON (u.id = c.requester_id OR u.id = c.receiver_id) AND u.id != ?
      WHERE (c.requester_id = ? OR c.receiver_id = ?)
    `, [userId, userId, userId]);
    res.json(connections);
  });

  // Feed / Posts
  app.post("/api/posts", authenticate, async (req, res) => {
    const userId = (req as any).userId;
    const { content } = req.body;
    await db.run("INSERT INTO posts (user_id, content) VALUES (?, ?)", [userId, content]);
    res.json({ success: true });
  });

  app.get("/api/posts", authenticate, async (req, res) => {
    const posts = await db.all(`
      SELECT p.id, p.content, p.created_at, u.name as authorName, u.job_title as authorJob,
      (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likesCount,
      (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as commentsCount
      FROM posts p
      JOIN users u ON p.user_id = u.id
      ORDER BY p.created_at DESC LIMIT 50
    `);
    res.json(posts);
  });
  
  app.post("/api/posts/:id/like", authenticate, async (req, res) => {
      const userId = (req as any).userId;
      const postId = req.params.id;
      // Simple toggle
      const existing = await db.get("SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?", [userId, postId]);
      if (existing) {
          await db.run("DELETE FROM likes WHERE user_id = ? AND post_id = ?", [userId, postId]);
      } else {
          await db.run("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", [userId, postId]);
      }
      res.json({ success: true });
  });
  
  app.post("/api/posts/:id/comment", authenticate, async (req, res) => {
      const userId = (req as any).userId;
      const postId = req.params.id;
      const { content } = req.body;
      await db.run("INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)", [userId, postId, content]);
      res.json({ success: true });
  });
  
  app.get("/api/posts/:id/comments", authenticate, async (req, res) => {
      const comments = await db.all("SELECT c.content, u.name FROM comments c JOIN users u ON u.id = c.user_id WHERE c.post_id = ? ORDER BY c.created_at ASC", [req.params.id]);
      res.json(comments);
  });

  // Messages
  app.post("/api/messages", authenticate, async (req, res) => {
    const userId = (req as any).userId;
    const { receiverId, content } = req.body;
    await db.run("INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)", [userId, receiverId, content]);
    await db.run("INSERT INTO notifications (user_id, content) SELECT name || ' vous a envoyé un message.', ? FROM users WHERE id = ?", [receiverId, userId]);
    res.json({ success: true });
  });

  app.get("/api/messages/:otherUserId", authenticate, async (req, res) => {
    const userId = (req as any).userId;
    const otherId = req.params.otherUserId;
    const messages = await db.all(`
      SELECT * FROM messages 
      WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
      ORDER BY created_at ASC
    `, [userId, otherId, otherId, userId]);
    res.json(messages);
  });

  // Notifications
  app.get("/api/notifications", authenticate, async (req, res) => {
    const userId = (req as any).userId;
    const notifs = await db.all("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", [userId]);
    await db.run("UPDATE notifications SET is_read = 1 WHERE user_id = ?", [userId]);
    res.json(notifs);
  });

  // Vite integration 
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
