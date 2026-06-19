"""
TeleMed - Application de Télémédecine
Flask + SQLite
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'telemedecine_secret_key_2024'
app.config['DATABASE'] = 'telemedecine.db'

# ============================================================
# UTILITAIRES BASE DE DONNÉES
# ============================================================

def get_db():
    """Obtient une connexion à la base de données"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initialise la base de données avec les tables et données de test"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.executescript('''
        DROP TABLE IF EXISTS prescriptions;
        DROP TABLE IF EXISTS consultations;
        DROP TABLE IF EXISTS rendezvous;
        DROP TABLE IF EXISTS utilisateurs;
        
        CREATE TABLE utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('patient', 'medecin', 'admin')),
            telephone TEXT,
            specialite TEXT,
            date_naissance TEXT,
            adresse TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE rendezvous (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            medecin_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            heure TEXT NOT NULL,
            motif TEXT NOT NULL,
            statut TEXT DEFAULT 'en_attente' CHECK(statut IN ('en_attente', 'confirme', 'annule', 'termine')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (medecin_id) REFERENCES utilisateurs(id)
        );
        
        CREATE TABLE consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rendezvous_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            medecin_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            diagnostic TEXT,
            notes TEXT,
            statut TEXT DEFAULT 'en_cours' CHECK(statut IN ('en_cours', 'termine')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rendezvous_id) REFERENCES rendezvous(id),
            FOREIGN KEY (patient_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (medecin_id) REFERENCES utilisateurs(id)
        );
        
        CREATE TABLE prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consultation_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            medecin_id INTEGER NOT NULL,
            medicaments TEXT NOT NULL,
            posologie TEXT NOT NULL,
            duree TEXT NOT NULL,
            instructions TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consultation_id) REFERENCES consultations(id),
            FOREIGN KEY (patient_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (medecin_id) REFERENCES utilisateurs(id)
        );
    ''')
    
    # Hachage de mot de passe simple
    def hash_password(pwd):
        return hashlib.sha256(pwd.encode()).hexdigest()
    
    # Données de test - Administrateurs
    cursor.execute('''
        INSERT INTO utilisateurs (nom, prenom, email, password, role, telephone)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Admin', 'System', 'admin@telemed.fr', hash_password('admin123'), 'admin', '01 23 45 67 89'))
    
    # Données de test - Médecins
    medecins = [
        ('Martin', 'Jean', 'dr.martin@telemed.fr', hash_password('medecin123'), 'medecin', '06 12 34 56 78', 'Médecine générale'),
        ('Bernard', 'Marie', 'dr.bernard@telemed.fr', hash_password('medecin123'), 'medecin', '06 23 45 67 89', 'Cardiologie'),
        ('Petit', 'Pierre', 'dr.petit@telemed.fr', hash_password('medecin123'), 'medecin', '06 34 56 78 90', 'Dermatologie'),
        ('Robert', 'Sophie', 'dr.robert@telemed.fr', hash_password('medecin123'), 'medecin', '06 45 67 89 01', 'Pédiatrie'),
        ('Richard', 'Lucas', 'dr.richard@telemed.fr', hash_password('medecin123'), 'medecin', '06 56 78 90 12', 'Neurologie'),
    ]
    for m in medecins:
        cursor.execute('''
            INSERT INTO utilisateurs (nom, prenom, email, password, role, telephone, specialite)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', m)
    
    # Données de test - Patients
    patients = [
        ('Dupont', 'Alexandre', 'alex.dupont@email.fr', hash_password('patient123'), 'patient', '07 12 34 56 78', None, '1985-03-15', '12 Rue de Paris, 75001 Paris'),
        ('Moreau', 'Emma', 'emma.moreau@email.fr', hash_password('patient123'), 'patient', '07 23 45 67 89', None, '1990-07-22', '25 Avenue Victor Hugo, 75016 Paris'),
        ('Lambert', 'Thomas', 'thomas.lambert@email.fr', hash_password('patient123'), 'patient', '07 34 56 78 90', None, '1978-11-08', '8 Boulevard Haussmann, 75008 Paris'),
        ('Girard', 'Camille', 'camille.girard@email.fr', hash_password('patient123'), 'patient', '07 45 67 89 01', None, '1995-01-30', '45 Rue du Commerce, 75015 Paris'),
    ]
    for p in patients:
        cursor.execute('''
            INSERT INTO utilisateurs (nom, prenom, email, password, role, telephone, specialite, date_naissance, adresse)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', p)
    
    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès!")

# ============================================================
# DÉCORATEURS
# ============================================================

def login_required(f):
    """Vérifie que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Vérifie que l'utilisateur a un rôle autorisé"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Veuillez vous connecter.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Accès non autorisé.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================
# CONTEXT PROCESSOR
# ============================================================

@app.context_processor
def inject_user():
    """Injecte l'utilisateur courant dans tous les templates"""
    user = None
    if 'user_id' in session:
        conn = get_db()
        user = conn.execute('SELECT * FROM utilisateurs WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
    return dict(current_user=user)

# ============================================================
# ROUTES - PAGES PUBLIQUES
# ============================================================

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        
        user = cursor.execute(
            'SELECT * FROM utilisateurs WHERE email = ? AND password = ?',
            (email, hashed_pwd)
        ).fetchone()
        conn.close()
        
        if user:
            if user['active'] == 0:
                flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
                return redirect(url_for('login'))
            
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['nom'] = user['nom']
            session['prenom'] = user['prenom']
            
            flash(f'Bienvenue, {user["prenom"]} {user["nom"]}!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'medecin':
                return redirect(url_for('medecin_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription (patients uniquement)"""
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        telephone = request.form.get('telephone')
        date_naissance = request.form.get('date_naissance')
        adresse = request.form.get('adresse')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('register'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Vérifier si l'email existe déjà
        existing = cursor.execute('SELECT id FROM utilisateurs WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('Cet email est déjà utilisé.', 'danger')
            conn.close()
            return redirect(url_for('register'))
        
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO utilisateurs (nom, prenom, email, password, role, telephone, date_naissance, adresse)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nom, prenom, email, hashed_pwd, 'patient', telephone, date_naissance, adresse))
        
        conn.commit()
        conn.close()
        
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

# ============================================================
# ROUTES - TABLEAU DE BORD
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Redirection vers le bon tableau de bord selon le rôle"""
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session.get('role') == 'medecin':
        return redirect(url_for('medecin_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))

@app.route('/dashboard/patient')
@role_required('patient')
def patient_dashboard():
    """Tableau de bord patient"""
    conn = get_db()
    cursor = conn.cursor()
    patient_id = session['user_id']
    
    # Statistiques
    stats = {
        'rendezvous_total': cursor.execute(
            'SELECT COUNT(*) FROM rendezvous WHERE patient_id = ?', (patient_id,)
        ).fetchone()[0],
        'rendezvous_a_venir': cursor.execute(
            "SELECT COUNT(*) FROM rendezvous WHERE patient_id = ? AND date >= date('now') AND statut != 'annule'",
            (patient_id,)
        ).fetchone()[0],
        'consultations': cursor.execute(
            'SELECT COUNT(*) FROM consultations WHERE patient_id = ?', (patient_id,)
        ).fetchone()[0],
        'prescriptions': cursor.execute(
            'SELECT COUNT(*) FROM prescriptions WHERE patient_id = ?', (patient_id,)
        ).fetchone()[0]
    }
    
    # Prochains rendez-vous
    rendezvous = cursor.execute('''
        SELECT r.*, u.nom as medecin_nom, u.prenom as medecin_prenom, u.specialite
        FROM rendezvous r
        JOIN utilisateurs u ON r.medecin_id = u.id
        WHERE r.patient_id = ? AND r.date >= date('now') AND r.statut != 'annule'
        ORDER BY r.date, r.heure
        LIMIT 5
    ''', (patient_id,)).fetchall()
    
    # Dernières consultations
    consultations = cursor.execute('''
        SELECT c.*, u.nom as medecin_nom, u.prenom as medecin_prenom, u.specialite
        FROM consultations c
        JOIN utilisateurs u ON c.medecin_id = u.id
        WHERE c.patient_id = ?
        ORDER BY c.date DESC
        LIMIT 5
    ''', (patient_id,)).fetchall()
    
    # Dernières prescriptions
    prescriptions = cursor.execute('''
        SELECT p.*, u.nom as medecin_nom, u.prenom as medecin_prenom
        FROM prescriptions p
        JOIN utilisateurs u ON p.medecin_id = u.id
        WHERE p.patient_id = ?
        ORDER BY p.date DESC
        LIMIT 5
    ''', (patient_id,)).fetchall()
    
    conn.close()
    
    return render_template('dashboard/patient.html', stats=stats, rendezvous=rendezvous,
                          consultations=consultations, prescriptions=prescriptions)

@app.route('/dashboard/medecin')
@role_required('medecin')
def medecin_dashboard():
    """Tableau de bord médecin"""
    conn = get_db()
    cursor = conn.cursor()
    medecin_id = session['user_id']
    
    # Statistiques
    stats = {
        'rendezvous_total': cursor.execute(
            'SELECT COUNT(*) FROM rendezvous WHERE medecin_id = ?', (medecin_id,)
        ).fetchone()[0],
        'rendezvous_a_venir': cursor.execute(
            "SELECT COUNT(*) FROM rendezvous WHERE medecin_id = ? AND date >= date('now') AND statut != 'annule'",
            (medecin_id,)
        ).fetchone()[0],
        'consultations': cursor.execute(
            'SELECT COUNT(*) FROM consultations WHERE medecin_id = ?', (medecin_id,)
        ).fetchone()[0],
        'patients': cursor.execute(
            'SELECT COUNT(DISTINCT patient_id) FROM rendezvous WHERE medecin_id = ?',
            (medecin_id,)
        ).fetchone()[0]
    }
    
    # Prochains rendez-vous
    rendezvous = cursor.execute('''
        SELECT r.*, u.nom as patient_nom, u.prenom as patient_prenom
        FROM rendezvous r
        JOIN utilisateurs u ON r.patient_id = u.id
        WHERE r.medecin_id = ? AND r.date >= date('now') AND r.statut != 'annule'
        ORDER BY r.date, r.heure
        LIMIT 5
    ''', (medecin_id,)).fetchall()
    
    # Dernières consultations
    consultations = cursor.execute('''
        SELECT c.*, u.nom as patient_nom, u.prenom as patient_prenom
        FROM consultations c
        JOIN utilisateurs u ON c.patient_id = u.id
        WHERE c.medecin_id = ?
        ORDER BY c.date DESC
        LIMIT 5
    ''', (medecin_id,)).fetchall()
    
    conn.close()
    
    return render_template('dashboard/medecin.html', stats=stats, rendezvous=rendezvous,
                          consultations=consultations)

@app.route('/dashboard/admin')
@role_required('admin')
def admin_dashboard():
    """Tableau de bord administrateur"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Statistiques globales
    stats = {
        'total_users': cursor.execute('SELECT COUNT(*) FROM utilisateurs').fetchone()[0],
        'total_patients': cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE role = 'patient'").fetchone()[0],
        'total_medecins': cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE role = 'medecin'").fetchone()[0],
        'total_rendezvous': cursor.execute('SELECT COUNT(*) FROM rendezvous').fetchone()[0],
        'total_consultations': cursor.execute('SELECT COUNT(*) FROM consultations').fetchone()[0],
        'total_prescriptions': cursor.execute('SELECT COUNT(*) FROM prescriptions').fetchone()[0]
    }
    
    # Derniers utilisateurs inscrits
    derniers_users = cursor.execute('''
        SELECT * FROM utilisateurs ORDER BY created_at DESC LIMIT 10
    ''').fetchall()
    
    # Derniers rendez-vous
    derniers_rdv = cursor.execute('''
        SELECT r.*, 
               p.nom as patient_nom, p.prenom as patient_prenom,
               m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
        FROM rendezvous r
        JOIN utilisateurs p ON r.patient_id = p.id
        JOIN utilisateurs m ON r.medecin_id = m.id
        ORDER BY r.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard/admin.html', stats=stats, 
                          derniers_users=derniers_users, derniers_rdv=derniers_rdv)

# ============================================================
# ROUTES - RENDEZ-VOUS
# ============================================================

@app.route('/rendezvous')
@login_required
def liste_rendezvous():
    """Liste des rendez-vous de l'utilisateur"""
    conn = get_db()
    cursor = conn.cursor()
    
    if session['role'] == 'patient':
        rendezvous = cursor.execute('''
            SELECT r.*, u.nom as medecin_nom, u.prenom as medecin_prenom, u.specialite
            FROM rendezvous r
            JOIN utilisateurs u ON r.medecin_id = u.id
            WHERE r.patient_id = ?
            ORDER BY r.date DESC, r.heure
        ''', (session['user_id'],)).fetchall()
    elif session['role'] == 'medecin':
        rendezvous = cursor.execute('''
            SELECT r.*, u.nom as patient_nom, u.prenom as patient_prenom
            FROM rendezvous r
            JOIN utilisateurs u ON r.patient_id = u.id
            WHERE r.medecin_id = ?
            ORDER BY r.date DESC, r.heure
        ''', (session['user_id'],)).fetchall()
    else:
        rendezvous = cursor.execute('''
            SELECT r.*, 
                   p.nom as patient_nom, p.prenom as patient_prenom,
                   m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
            FROM rendezvous r
            JOIN utilisateurs p ON r.patient_id = p.id
            JOIN utilisateurs m ON r.medecin_id = m.id
            ORDER BY r.date DESC, r.heure
        ''').fetchall()
    
    conn.close()
    return render_template('rendezvous/liste.html', rendezvous=rendezvous)

@app.route('/rendezvous/prendre', methods=['GET', 'POST'])
@role_required('patient')
def prendre_rendezvous():
    """Prendre un rendez-vous"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        medecin_id = request.form.get('medecin_id')
        date = request.form.get('date')
        heure = request.form.get('heure')
        motif = request.form.get('motif')
        
        # Vérifier que le médecin existe
        medecin = cursor.execute('SELECT * FROM utilisateurs WHERE id = ? AND role = "medecin"',
                                (medecin_id,)).fetchone()
        if not medecin:
            flash('Médecin non trouvé.', 'danger')
            conn.close()
            return redirect(url_for('prendre_rendezvous'))
        
        # Vérifier que le créneau n'est pas déjà pris
        existing = cursor.execute('''
            SELECT id FROM rendezvous 
            WHERE medecin_id = ? AND date = ? AND heure = ? AND statut != 'annule'
        ''', (medecin_id, date, heure)).fetchone()
        
        if existing:
            flash('Ce créneau horaire est déjà réservé.', 'danger')
            conn.close()
            return redirect(url_for('prendre_rendezvous'))
        
        cursor.execute('''
            INSERT INTO rendezvous (patient_id, medecin_id, date, heure, motif)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], medecin_id, date, heure, motif))
        
        conn.commit()
        conn.close()
        
        flash('Rendez-vous demandé avec succès!', 'success')
        return redirect(url_for('liste_rendezvous'))
    
    # Récupérer la liste des médecins
    medecins = cursor.execute('''
        SELECT id, nom, prenom, specialite, telephone 
        FROM utilisateurs WHERE role = 'medecin' AND active = 1
        ORDER BY nom, prenom
    ''').fetchall()
    
    conn.close()
    
    # Générer les créneaux horaires (8h - 18h, par tranches de 30min)
    creneaux = []
    for h in range(8, 18):
        creneaux.append(f"{h:02d}:00")
        creneaux.append(f"{h:02d}:30")
    
    return render_template('rendezvous/prendre.html', medecins=medecins, creneaux=creneaux)

@app.route('/rendezvous/<int:id>/confirmer', methods=['POST'])
@login_required
def confirmer_rendezvous(id):
    """Confirmer un rendez-vous (médecin ou admin)"""
    if session['role'] not in ['medecin', 'admin']:
        flash('Action non autorisée.', 'danger')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Vérifier que le médecin est bien assigné à ce rendez-vous
    rdv = cursor.execute('SELECT * FROM rendezvous WHERE id = ?', (id,)).fetchone()
    if not rdv:
        flash('Rendez-vous non trouvé.', 'danger')
        conn.close()
        return redirect(url_for('liste_rendezvous'))
    
    if session['role'] == 'medecin' and rdv['medecin_id'] != session['user_id']:
        flash('Vous n\'êtes pas autorisé à modifier ce rendez-vous.', 'danger')
        conn.close()
        return redirect(url_for('liste_rendezvous'))
    
    cursor.execute("UPDATE rendezvous SET statut = 'confirme' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('Rendez-vous confirmé.', 'success')
    return redirect(url_for('liste_rendezvous'))

@app.route('/rendezvous/<int:id>/annuler', methods=['POST'])
@login_required
def annuler_rendezvous(id):
    """Annuler un rendez-vous"""
    conn = get_db()
    cursor = conn.cursor()
    
    rdv = cursor.execute('SELECT * FROM rendezvous WHERE id = ?', (id,)).fetchone()
    if not rdv:
        flash('Rendez-vous non trouvé.', 'danger')
        conn.close()
        return redirect(url_for('liste_rendezvous'))
    
    # Vérifier les droits
    if session['role'] == 'patient' and rdv['patient_id'] != session['user_id']:
        flash('Vous n\'êtes pas autorisé à annuler ce rendez-vous.', 'danger')
        conn.close()
        return redirect(url_for('liste_rendezvous'))
    
    if session['role'] == 'medecin' and rdv['medecin_id'] != session['user_id']:
        flash('Vous n\'êtes pas autorisé à annuler ce rendez-vous.', 'danger')
        conn.close()
        return redirect(url_for('liste_rendezvous'))
    
    cursor.execute("UPDATE rendezvous SET statut = 'annule' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('Rendez-vous annulé.', 'info')
    return redirect(url_for('liste_rendezvous'))

# ============================================================
# ROUTES - CONSULTATIONS
# ============================================================

@app.route('/consultations')
@login_required
def liste_consultations():
    """Liste des consultations"""
    conn = get_db()
    cursor = conn.cursor()
    
    if session['role'] == 'patient':
        consultations = cursor.execute('''
            SELECT c.*, u.nom as medecin_nom, u.prenom as medecin_prenom, u.specialite
            FROM consultations c
            JOIN utilisateurs u ON c.medecin_id = u.id
            WHERE c.patient_id = ?
            ORDER BY c.date DESC
        ''', (session['user_id'],)).fetchall()
    elif session['role'] == 'medecin':
        consultations = cursor.execute('''
            SELECT c.*, u.nom as patient_nom, u.prenom as patient_prenom
            FROM consultations c
            JOIN utilisateurs u ON c.patient_id = u.id
            WHERE c.medecin_id = ?
            ORDER BY c.date DESC
        ''', (session['user_id'],)).fetchall()
    else:
        consultations = cursor.execute('''
            SELECT c.*, 
                   p.nom as patient_nom, p.prenom as patient_prenom,
                   m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
            FROM consultations c
            JOIN utilisateurs p ON c.patient_id = p.id
            JOIN utilisateurs m ON c.medecin_id = m.id
            ORDER BY c.date DESC
        ''').fetchall()
    
    conn.close()
    return render_template('consultation/historique.html', consultations=consultations)

@app.route('/consultation/<int:id>')
@login_required
def detail_consultation(id):
    """Détail d'une consultation"""
    conn = get_db()
    cursor = conn.cursor()
    
    consultation = cursor.execute('''
        SELECT c.*, 
               p.nom as patient_nom, p.prenom as patient_prenom,
               m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
        FROM consultations c
        JOIN utilisateurs p ON c.patient_id = p.id
        JOIN utilisateurs m ON c.medecin_id = m.id
        WHERE c.id = ?
    ''', (id,)).fetchone()
    
    if not consultation:
        flash('Consultation non trouvée.', 'danger')
        conn.close()
        return redirect(url_for('liste_consultations'))
    
    # Vérifier les droits
    if session['role'] == 'patient' and consultation['patient_id'] != session['user_id']:
        flash('Accès non autorisé.', 'danger')
        conn.close()
        return redirect(url_for('liste_consultations'))
    
    if session['role'] == 'medecin' and consultation['medecin_id'] != session['user_id']:
        flash('Accès non autorisé.', 'danger')
        conn.close()
        return redirect(url_for('liste_consultations'))
    
    # Récupérer la prescription associée
    prescription = cursor.execute('''
        SELECT p.*, u.nom as medecin_nom, u.prenom as medecin_prenom
        FROM prescriptions p
        JOIN utilisateurs u ON p.medecin_id = u.id
        WHERE p.consultation_id = ?
    ''', (id,)).fetchone()
    
    conn.close()
    return render_template('consultation/detail.html', consultation=consultation, prescription=prescription)

@app.route('/consultation/demarrer/<int:rendezvous_id>')
@role_required('medecin')
def demarrer_consultation(rendezvous_id):
    """Démarrer une consultation à partir d'un rendez-vous"""
    conn = get_db()
    cursor = conn.cursor()
    
    rdv = cursor.execute('SELECT * FROM rendezvous WHERE id = ?', (rendezvous_id,)).fetchone()
    if not rdv:
        flash('Rendez-vous non trouvé.', 'danger')
        conn.close()
        return redirect(url_for('medecin_dashboard'))
    
    if rdv['medecin_id'] != session['user_id']:
        flash('Vous n\'êtes pas autorisé à démarrer cette consultation.', 'danger')
        conn.close()
        return redirect(url_for('medecin_dashboard'))
    
    # Vérifier si une consultation existe déjà
    existing = cursor.execute('SELECT id FROM consultations WHERE rendezvous_id = ?',
                             (rendezvous_id,)).fetchone()
    
    if existing:
        consultation_id = existing['id']
    else:
        # Créer une nouvelle consultation
        cursor.execute('''
            INSERT INTO consultations (rendezvous_id, patient_id, medecin_id, date, diagnostic, notes, statut)
            VALUES (?, ?, ?, date('now'), '', '', 'en_cours')
        ''', (rendezvous_id, rdv['patient_id'], session['user_id']))
        
        consultation_id = cursor.lastrowid
        
        # Mettre à jour le statut du rendez-vous
        cursor.execute("UPDATE rendezvous SET statut = 'termine' WHERE id = ?", (rendezvous_id,))
        
        conn.commit()
    
    conn.close()
    
    return redirect(url_for('interface_consultation', id=consultation_id))

@app.route('/consultation/interface/<int:id>')
@login_required
def interface_consultation(id):
    """Interface de consultation vidéo simulée"""
    conn = get_db()
    cursor = conn.cursor()
    
    consultation = cursor.execute('''
        SELECT c.*, 
               p.nom as patient_nom, p.prenom as patient_prenom,
               m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
        FROM consultations c
        JOIN utilisateurs p ON c.patient_id = p.id
        JOIN utilisateurs m ON c.medecin_id = m.id
        WHERE c.id = ?
    ''', (id,)).fetchone()
    
    if not consultation:
        flash('Consultation non trouvée.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Vérifier les droits
    if session['role'] == 'patient' and consultation['patient_id'] != session['user_id']:
        flash('Accès non autorisé.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))
    
    if session['role'] == 'medecin' and consultation['medecin_id'] != session['user_id']:
        flash('Accès non autorisé.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('consultation/video.html', consultation=consultation)

@app.route('/consultation/terminer/<int:id>', methods=['POST'])
@role_required('medecin')
def terminer_consultation(id):
    """Terminer une consultation et enregistrer le diagnostic"""
    conn = get_db()
    cursor = conn.cursor()
    
    diagnostic = request.form.get('diagnostic', '')
    notes = request.form.get('notes', '')
    medicaments = request.form.get('medicaments', '')
    posologie = request.form.get('posologie', '')
    duree = request.form.get('duree', '')
    instructions = request.form.get('instructions', '')
    
    consultation = cursor.execute('SELECT * FROM consultations WHERE id = ?', (id,)).fetchone()
    if not consultation:
        flash('Consultation non trouvée.', 'danger')
        conn.close()
        return redirect(url_for('medecin_dashboard'))
    
    # Mettre à jour la consultation
    cursor.execute('''
        UPDATE consultations SET diagnostic = ?, notes = ?, statut = 'termine'
        WHERE id = ?
    ''', (diagnostic, notes, id))
    
    # Créer une prescription si des médicaments sont prescrits
    if medicaments:
        cursor.execute('''
            INSERT INTO prescriptions (consultation_id, patient_id, medecin_id, medicaments, posologie, duree, instructions, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, date('now'))
        ''', (id, consultation['patient_id'], session['user_id'], 
              medicaments, posologie, duree, instructions))
    
    conn.commit()
    conn.close()
    
    flash('Consultation terminée et enregistrée.', 'success')
    return redirect(url_for('medecin_dashboard'))

# ============================================================
# ROUTES - PRESCRIPTIONS
# ============================================================

@app.route('/prescriptions')
@login_required
def liste_prescriptions():
    """Liste des prescriptions"""
    conn = get_db()
    cursor = conn.cursor()
    
    if session['role'] == 'patient':
        prescriptions = cursor.execute('''
            SELECT p.*, u.nom as medecin_nom, u.prenom as medecin_prenom, u.specialite
            FROM prescriptions p
            JOIN utilisateurs u ON p.medecin_id = u.id
            WHERE p.patient_id = ?
            ORDER BY p.date DESC
        ''', (session['user_id'],)).fetchall()
    elif session['role'] == 'medecin':
        prescriptions = cursor.execute('''
            SELECT p.*, u.nom as patient_nom, u.prenom as patient_prenom
            FROM prescriptions p
            JOIN utilisateurs u ON p.patient_id = u.id
            WHERE p.medecin_id = ?
            ORDER BY p.date DESC
        ''', (session['user_id'],)).fetchall()
    else:
        prescriptions = cursor.execute('''
            SELECT p.*, 
                   pat.nom as patient_nom, pat.prenom as patient_prenom,
                   m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
            FROM prescriptions p
            JOIN utilisateurs pat ON p.patient_id = pat.id
            JOIN utilisateurs m ON p.medecin_id = m.id
            ORDER BY p.date DESC
        ''').fetchall()
    
    conn.close()
    return render_template('prescription/liste.html', prescriptions=prescriptions)

@app.route('/prescription/<int:id>')
@login_required
def detail_prescription(id):
    """Détail d'une prescription"""
    conn = get_db()
    cursor = conn.cursor()
    
    prescription = cursor.execute('''
        SELECT p.*, 
               pat.nom as patient_nom, pat.prenom as patient_prenom,
               m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
        FROM prescriptions p
        JOIN utilisateurs pat ON p.patient_id = pat.id
        JOIN utilisateurs m ON p.medecin_id = m.id
        WHERE p.id = ?
    ''', (id,)).fetchone()
    
    if not prescription:
        flash('Prescription non trouvée.', 'danger')
        conn.close()
        return redirect(url_for('liste_prescriptions'))
    
    # Vérifier les droits
    if session['role'] == 'patient' and prescription['patient_id'] != session['user_id']:
        flash('Accès non autorisé.', 'danger')
        conn.close()
        return redirect(url_for('liste_prescriptions'))
    
    conn.close()
    return render_template('prescription/detail.html', prescription=prescription)

# ============================================================
# ROUTES - API/JSON (pour AJAX)
# ============================================================

@app.route('/api/medecins')
def api_medecins():
    """API: Liste des médecins (pour le calendrier)"""
    conn = get_db()
    cursor = conn.cursor()
    medecins = cursor.execute('''
        SELECT id, nom, prenom, specialite, telephone 
        FROM utilisateurs WHERE role = 'medecin' AND active = 1
        ORDER BY nom, prenom
    ''').fetchall()
    conn.close()
    return jsonify([dict(m) for m in medecins])

@app.route('/api/creneaux/<int:medecin_id>/<date>')
def api_creneaux(medecin_id, date):
    """API: Créneaux disponibles pour un médecin à une date donnée"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer les créneaux déjà réservés
    reserved = cursor.execute('''
        SELECT heure FROM rendezvous 
        WHERE medecin_id = ? AND date = ? AND statut != 'annule'
    ''', (medecin_id, date)).fetchall()
    
    reserved_hours = [r['heure'] for r in reserved]
    
    # Générer les créneaux disponibles
    all_creneaux = []
    for h in range(8, 18):
        all_creneaux.append(f"{h:02d}:00")
        all_creneaux.append(f"{h:02d}:30")
    
    available = [c for c in all_creneaux if c not in reserved_hours]
    
    conn.close()
    return jsonify(available)

@app.route('/api/statistiques')
@role_required('admin')
def api_statistiques():
    """API: Statistiques pour le tableau de bord admin"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {
        'utilisateurs': cursor.execute('SELECT role, COUNT(*) as count FROM utilisateurs GROUP BY role').fetchall(),
        'rendezvous_par_mois': cursor.execute('''
            SELECT strftime('%Y-%m', date) as mois, COUNT(*) as count 
            FROM rendezvous GROUP BY mois ORDER BY mois DESC LIMIT 12
        ''').fetchall(),
        'consultations_par_mois': cursor.execute('''
            SELECT strftime('%Y-%m', date) as mois, COUNT(*) as count 
            FROM consultations GROUP BY mois ORDER BY mois DESC LIMIT 12
        ''').fetchall()
    }
    
    conn.close()
    return jsonify({
        'utilisateurs': [dict(u) for u in stats['utilisateurs']],
        'rendezvous_par_mois': [dict(r) for r in stats['rendezvous_par_mois']],
        'consultations_par_mois': [dict(c) for c in stats['consultations_par_mois']]
    })

# ============================================================
# ROUTES - ADMINISTRATION
# ============================================================

@app.route('/admin/utilisateurs')
@role_required('admin')
def admin_utilisateurs():
    """Gestion des utilisateurs (admin)"""
    conn = get_db()
    cursor = conn.cursor()
    
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '')
    
    query = 'SELECT * FROM utilisateurs WHERE 1=1'
    params = []
    
    if role_filter:
        query += ' AND role = ?'
        params.append(role_filter)
    
    if search:
        query += ' AND (nom LIKE ? OR prenom LIKE ? OR email LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    query += ' ORDER BY created_at DESC'
    
    utilisateurs = cursor.execute(query, params).fetchall()
    conn.close()
    
    return render_template('admin/utilisateurs.html', utilisateurs=utilisateurs, 
                          role_filter=role_filter, search=search)

@app.route('/admin/utilisateur/<int:id>/toggle', methods=['POST'])
@role_required('admin')
def toggle_utilisateur(id):
    """Activer/Désactiver un utilisateur"""
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT active FROM utilisateurs WHERE id = ?', (id,)).fetchone()
    if user:
        new_status = 0 if user['active'] == 1 else 1
        cursor.execute('UPDATE utilisateurs SET active = ? WHERE id = ?', (new_status, id))
        conn.commit()
        flash(f"Utilisateur {'désactivé' if new_status == 0 else 'activé'}.", 'success')
    
    conn.close()
    return redirect(url_for('admin_utilisateurs'))

@app.route('/admin/utilisateur/<int:id>/supprimer', methods=['POST'])
@role_required('admin')
def supprimer_utilisateur(id):
    """Supprimer un utilisateur"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Ne pas supprimer son propre compte
    if id == session['user_id']:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        conn.close()
        return redirect(url_for('admin_utilisateurs'))
    
    cursor.execute('DELETE FROM utilisateurs WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Utilisateur supprimé.', 'success')
    return redirect(url_for('admin_utilisateurs'))

@app.route('/admin/rendezvous')
@role_required('admin')
def admin_rendezvous():
    """Gestion de tous les rendez-vous (admin)"""
    conn = get_db()
    cursor = conn.cursor()
    
    rendezvous = cursor.execute('''
        SELECT r.*, 
               p.nom as patient_nom, p.prenom as patient_prenom,
               m.nom as medecin_nom, m.prenom as medecin_prenom, m.specialite
        FROM rendezvous r
        JOIN utilisateurs p ON r.patient_id = p.id
        JOIN utilisateurs m ON r.medecin_id = m.id
        ORDER BY r.date DESC, r.heure
    ''').fetchall()
    
    conn.close()
    return render_template('admin/rendezvous.html', rendezvous=rendezvous)

# ============================================================
# DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    # Initialiser la base de données si elle n'existe pas
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
