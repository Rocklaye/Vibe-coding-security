from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'medicore-secret-key-2024-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── MODELS ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'doctor' or 'patient'
    full_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient_record = db.relationship('PatientRecord', backref='user', uselist=False)

class PatientRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    blood_type = db.Column(db.String(10), nullable=False)
    allergies = db.Column(db.Text, default='')
    emergency_contact = db.Column(db.String(200), default='')
    address = db.Column(db.Text, default='')
    phone = db.Column(db.String(30), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = db.relationship('MedicalNote', backref='patient', lazy=True, order_by='MedicalNote.created_at.desc()')
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, order_by='Prescription.created_at.desc()')

class MedicalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_record.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('User', foreign_keys=[doctor_id])

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_record.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medication = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.Date, nullable=True)

    doctor = db.relationship('User', foreign_keys=[doctor_id])

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def current_user():
    uid = session.get('user_id')
    if uid:
        return User.query.get(uid)
    return None

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({'error': 'Authentification requise'}), 401
        return fn(*args, **kwargs)
    return wrapper

def doctor_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u or u.role != 'doctor':
            return jsonify({'error': 'Accès réservé aux médecins'}), 403
        return fn(*args, **kwargs)
    return wrapper

# ─── PAGE ROUTES ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ─── AUTH API ─────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    d = request.get_json()
    if User.query.filter_by(email=d['email']).first():
        return jsonify({'error': 'Email déjà utilisé'}), 400

    user = User(
        email=d['email'],
        password_hash=generate_password_hash(d['password']),
        role=d.get('role', 'patient'),
        full_name=d['full_name']
    )
    db.session.add(user)
    db.session.flush()

    if user.role == 'patient':
        dob = datetime.strptime(d['date_of_birth'], '%Y-%m-%d').date()
        record = PatientRecord(
            user_id=user.id,
            date_of_birth=dob,
            blood_type=d['blood_type'],
            allergies=d.get('allergies', ''),
            phone=d.get('phone', ''),
            address=d.get('address', ''),
            emergency_contact=d.get('emergency_contact', '')
        )
        db.session.add(record)

    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'message': 'Inscription réussie', 'role': user.role, 'name': user.full_name}), 201

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json()
    user = User.query.filter_by(email=d['email']).first()
    if not user or not check_password_hash(user.password_hash, d['password']):
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
    session['user_id'] = user.id
    return jsonify({'message': 'Connexion réussie', 'role': user.role, 'name': user.full_name})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Déconnexion réussie'})

@app.route('/api/me')
def me():
    u = current_user()
    if not u:
        return jsonify({'authenticated': False}), 401
    return jsonify({'authenticated': True, 'id': u.id, 'role': u.role, 'name': u.full_name, 'email': u.email})

# ─── PATIENT API ──────────────────────────────────────────────────────────────

@app.route('/api/patients')
@login_required
def list_patients():
    u = current_user()
    if u.role != 'doctor':
        return jsonify({'error': 'Accès refusé'}), 403
    records = PatientRecord.query.join(User).order_by(User.full_name).all()
    result = []
    for r in records:
        age = (date.today() - r.date_of_birth).days // 365
        result.append({
            'id': r.id,
            'user_id': r.user_id,
            'name': r.user.full_name,
            'email': r.user.email,
            'date_of_birth': r.date_of_birth.isoformat(),
            'age': age,
            'blood_type': r.blood_type,
            'allergies': r.allergies,
            'phone': r.phone,
            'notes_count': len(r.notes),
            'prescriptions_count': len(r.prescriptions)
        })
    return jsonify(result)

@app.route('/api/patients/<int:record_id>')
@login_required
def get_patient(record_id):
    u = current_user()
    record = PatientRecord.query.get_or_404(record_id)
    if u.role == 'patient' and record.user_id != u.id:
        return jsonify({'error': 'Accès refusé'}), 403

    age = (date.today() - record.date_of_birth).days // 365
    notes = [{
        'id': n.id,
        'title': n.title,
        'content': n.content,
        'diagnosis': n.diagnosis,
        'doctor_name': n.doctor.full_name,
        'created_at': n.created_at.strftime('%d/%m/%Y %H:%M')
    } for n in record.notes]

    prescriptions = [{
        'id': p.id,
        'medication': p.medication,
        'dosage': p.dosage,
        'frequency': p.frequency,
        'duration': p.duration,
        'instructions': p.instructions,
        'doctor_name': p.doctor.full_name,
        'created_at': p.created_at.strftime('%d/%m/%Y'),
        'expires_at': p.expires_at.isoformat() if p.expires_at else None
    } for p in record.prescriptions]

    return jsonify({
        'id': record.id,
        'user_id': record.user_id,
        'name': record.user.full_name,
        'email': record.user.email,
        'date_of_birth': record.date_of_birth.isoformat(),
        'age': age,
        'blood_type': record.blood_type,
        'allergies': record.allergies,
        'phone': record.phone,
        'address': record.address,
        'emergency_contact': record.emergency_contact,
        'notes': notes,
        'prescriptions': prescriptions
    })

@app.route('/api/patients/<int:record_id>', methods=['PUT'])
@login_required
def update_patient(record_id):
    u = current_user()
    record = PatientRecord.query.get_or_404(record_id)
    if u.role == 'patient' and record.user_id != u.id:
        return jsonify({'error': 'Accès refusé'}), 403

    d = request.get_json()
    if 'date_of_birth' in d:
        record.date_of_birth = datetime.strptime(d['date_of_birth'], '%Y-%m-%d').date()
    if 'blood_type' in d:
        record.blood_type = d['blood_type']
    if 'allergies' in d:
        record.allergies = d['allergies']
    if 'phone' in d:
        record.phone = d['phone']
    if 'address' in d:
        record.address = d['address']
    if 'emergency_contact' in d:
        record.emergency_contact = d['emergency_contact']
    if 'full_name' in d:
        record.user.full_name = d['full_name']

    record.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Dossier mis à jour'})

@app.route('/api/patients/my-record')
@login_required
def my_record():
    u = current_user()
    if u.role != 'patient':
        return jsonify({'error': 'Accès refusé'}), 403
    record = PatientRecord.query.filter_by(user_id=u.id).first()
    if not record:
        return jsonify({'error': 'Dossier non trouvé'}), 404
    return redirect(url_for('get_patient', record_id=record.id))

# ─── NOTES API ────────────────────────────────────────────────────────────────

@app.route('/api/patients/<int:record_id>/notes', methods=['POST'])
@login_required
def add_note(record_id):
    u = current_user()
    if u.role != 'doctor':
        return jsonify({'error': 'Réservé aux médecins'}), 403
    d = request.get_json()
    note = MedicalNote(
        patient_id=record_id,
        doctor_id=u.id,
        title=d['title'],
        content=d['content'],
        diagnosis=d.get('diagnosis', '')
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({'message': 'Note ajoutée', 'id': note.id}), 201

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    u = current_user()
    if u.role != 'doctor':
        return jsonify({'error': 'Réservé aux médecins'}), 403
    note = MedicalNote.query.get_or_404(note_id)
    if note.doctor_id != u.id:
        return jsonify({'error': 'Accès refusé'}), 403
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note supprimée'})

# ─── PRESCRIPTIONS API ────────────────────────────────────────────────────────

@app.route('/api/patients/<int:record_id>/prescriptions', methods=['POST'])
@login_required
def add_prescription(record_id):
    u = current_user()
    if u.role != 'doctor':
        return jsonify({'error': 'Réservé aux médecins'}), 403
    d = request.get_json()
    expires = None
    if d.get('expires_at'):
        expires = datetime.strptime(d['expires_at'], '%Y-%m-%d').date()
    rx = Prescription(
        patient_id=record_id,
        doctor_id=u.id,
        medication=d['medication'],
        dosage=d['dosage'],
        frequency=d['frequency'],
        duration=d['duration'],
        instructions=d.get('instructions', ''),
        expires_at=expires
    )
    db.session.add(rx)
    db.session.commit()
    return jsonify({'message': 'Ordonnance ajoutée', 'id': rx.id}), 201

@app.route('/api/prescriptions/<int:rx_id>', methods=['DELETE'])
@login_required
def delete_prescription(rx_id):
    u = current_user()
    if u.role != 'doctor':
        return jsonify({'error': 'Réservé aux médecins'}), 403
    rx = Prescription.query.get_or_404(rx_id)
    if rx.doctor_id != u.id:
        return jsonify({'error': 'Accès refusé'}), 403
    db.session.delete(rx)
    db.session.commit()
    return jsonify({'message': 'Ordonnance supprimée'})

# ─── SEED DATA ────────────────────────────────────────────────────────────────

def seed_demo_data():
    if User.query.count() > 0:
        return
    doctor = User(
        email='dr.dupont@medicore.fr',
        password_hash=generate_password_hash('medecin123'),
        role='doctor',
        full_name='Dr. Marie Dupont'
    )
    db.session.add(doctor)
    db.session.flush()

    patient_user = User(
        email='jean.martin@example.com',
        password_hash=generate_password_hash('patient123'),
        role='patient',
        full_name='Jean Martin'
    )
    db.session.add(patient_user)
    db.session.flush()

    record = PatientRecord(
        user_id=patient_user.id,
        date_of_birth=date(1985, 6, 15),
        blood_type='A+',
        allergies='Pénicilline, Aspirine',
        phone='06 12 34 56 78',
        address='12 rue des Lilas, 75011 Paris',
        emergency_contact='Marie Martin – 06 98 76 54 32'
    )
    db.session.add(record)
    db.session.flush()

    note = MedicalNote(
        patient_id=record.id,
        doctor_id=doctor.id,
        title='Consultation initiale',
        content='Le patient se plaint de maux de tête récurrents depuis 3 semaines. Tension artérielle normale. Pas de fièvre.',
        diagnosis='Céphalées de tension'
    )
    db.session.add(note)

    rx = Prescription(
        patient_id=record.id,
        doctor_id=doctor.id,
        medication='Paracétamol 1000mg',
        dosage='1 comprimé',
        frequency='3 fois par jour si douleur',
        duration='10 jours',
        instructions='Prendre avec un grand verre d\'eau. Ne pas dépasser 4g/jour.',
        expires_at=date(2025, 6, 1)
    )
    db.session.add(rx)
    db.session.commit()

# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_demo_data()
    app.run(debug=True, port=5000)
