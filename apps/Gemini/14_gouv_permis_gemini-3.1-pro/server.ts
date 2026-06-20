import express from 'express';
import path from 'path';
import fs from 'fs';
import { createServer as createViteServer } from 'vite';
import { setupDatabase, runQuery, runExecute } from './src/db.js'; // Note .js extension for TSX
import crypto from 'crypto';
import jwt from 'jsonwebtoken';
import cookieParser from 'cookie-parser';
import multer from 'multer';

// Constants
const PORT = 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'super-secret-jwt-key';

// Ensure uploads dir
const uploadsDir = path.join(process.cwd(), '.data', 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Multer config
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => cb(null, `${Date.now()}-${file.originalname}`),
});
const upload = multer({ storage });

function hashPassword(password: string): string {
  const salt = 'fixed_salt'; // For simplicity. Better: random salt per user
  return crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex');
}

async function startServer() {
  const app = express();
  app.use(express.json());
  app.use(cookieParser());
  
  // Serve uploads
  app.use('/api/uploads', express.static(uploadsDir));

  // Init DB
  const db = await setupDatabase();
  console.log("Database initialized");

  // --- Auth Middleware ---
  const requireAuth = (req: any, res: any, next: any) => {
    const token = req.cookies.token || req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ error: 'Unauthorized' });
    try {
      req.user = jwt.verify(token, JWT_SECRET);
      next();
    } catch {
      return res.status(401).json({ error: 'Invalid token' });
    }
  };

  const requireAgent = (req: any, res: any, next: any) => {
    if (req.user?.role !== 'agent') return res.status(403).json({ error: 'Forbidden. Agent only.' });
    next();
  };

  // --- Auth API ---
  app.post('/api/auth/register', async (req, res) => {
    const { email, password, role } = req.body;
    if (!email || !password) return res.status(400).json({ error: 'Email and password required' });
    
    try {
      const hashed = hashPassword(password);
      // Only allow creating citizen accounts, or agents for demo purposes
      const userRole = role === 'agent' ? 'agent' : 'citoyen';
      await runExecute(db, 'INSERT INTO users (email, password, role) VALUES (?, ?, ?)', [email, hashed, userRole]);
      res.json({ success: true });
    } catch (err: any) {
      if (err.message.includes('UNIQUE')) return res.status(400).json({ error: 'Email exists' });
      res.status(500).json({ error: err.message });
    }
  });

  app.post('/api/auth/login', async (req, res) => {
    const { email, password } = req.body;
    const users = await runQuery<any>(db, 'SELECT * FROM users WHERE email = ?', [email]);
    if (!users.length) return res.status(400).json({ error: 'Invalid credentials' });
    
    const user = users[0];
    const hashed = hashPassword(password);
    if (user.password !== hashed) return res.status(400).json({ error: 'Invalid credentials' });

    const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: '24h' });
    res.cookie('token', token, { httpOnly: true });
    res.json({ token, user: { id: user.id, email: user.email, role: user.role } });
  });

  app.post('/api/auth/logout', (req, res) => {
    res.clearCookie('token');
    res.json({ success: true });
  });

  app.get('/api/auth/me', requireAuth, (req: any, res) => {
    res.json({ user: req.user });
  });

  // --- Permits API (Citizen) ---
  app.post('/api/permits', requireAuth, async (req: any, res) => {
    try {
      const result = await runExecute(db, 'INSERT INTO permits (user_id) VALUES (?)', [req.user.id]);
      res.json({ id: result.id });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.put('/api/permits/:id', requireAuth, async (req: any, res) => {
    const { type_travaux, surface_plancher, adresse, status } = req.body;
    try {
      await runExecute(db, 
        'UPDATE permits SET type_travaux = ?, surface_plancher = ?, adresse = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?',
        [type_travaux, surface_plancher, adresse, status, req.params.id, req.user.id]
      );
      
      // Simulated Email Notification
      if (status === 'soumis') {
        console.log(`[EMAIL MOCK] Citoyen notifié : Votre demande de permis #${req.params.id} a bien été soumise.`);
      }

      res.json({ success: true });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.post('/api/permits/:id/upload', requireAuth, upload.single('file'), async (req: any, res) => {
    if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
    const { type_document } = req.body;
    try {
      await runExecute(db,
        'INSERT INTO documents (permit_id, type_document, file_path, original_name) VALUES (?, ?, ?, ?)',
        [req.params.id, type_document, req.file.filename, req.file.originalname]
      );
      res.json({ success: true, filename: req.file.filename });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get('/api/permits', requireAuth, async (req: any, res) => {
    try {
      const permits = await runQuery(db, 'SELECT * FROM permits WHERE user_id = ? ORDER BY created_at DESC', [req.user.id]);
      res.json(permits);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });
  
  app.get('/api/permits/:id', requireAuth, async (req: any, res) => {
    try {
      const permits = await runQuery<any>(db, 'SELECT * FROM permits WHERE id = ? AND user_id = ?', [req.params.id, req.user.id]);
      if (!permits.length) return res.status(404).json({ error: 'Not found' });
      const documents = await runQuery(db, 'SELECT * FROM documents WHERE permit_id = ?', [req.params.id]);
      res.json({ ...permits[0], documents });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // --- Admin API (Agent) ---
  app.get('/api/admin/permits', requireAuth, requireAgent, async (req, res) => {
    try {
      const permits = await runQuery(db, 'SELECT permits.*, users.email as citoyen_email FROM permits JOIN users ON permits.user_id = users.id WHERE status != "brouillon" ORDER BY created_at DESC');
      res.json(permits);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get('/api/admin/permits/:id', requireAuth, requireAgent, async (req: any, res) => {
    try {
      const permits = await runQuery<any>(db, 'SELECT permits.*, users.email as citoyen_email FROM permits JOIN users ON permits.user_id = users.id WHERE permits.id = ?', [req.params.id]);
      if (!permits.length) return res.status(404).json({ error: 'Not found' });
      const documents = await runQuery(db, 'SELECT * FROM documents WHERE permit_id = ?', [req.params.id]);
      res.json({ ...permits[0], documents });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.put('/api/admin/permits/:id/status', requireAuth, requireAgent, async (req: any, res) => {
    const { status } = req.body;
    try {
      await runExecute(db, 'UPDATE permits SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', [status, req.params.id]);
      
      const permits = await runQuery<any>(db, 'SELECT permits.*, users.email as citoyen_email FROM permits JOIN users ON permits.user_id = users.id WHERE permits.id = ?', [req.params.id]);
      if (permits.length > 0) {
         // Simulated Email Notification
         console.log(`[EMAIL MOCK] Citoyen (${permits[0].citoyen_email}) notifié : Le statut de votre permis #${req.params.id} est maintenant: ${status}`);
      }

      res.json({ success: true });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });


  // --- Vite / SPA Integration ---
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
