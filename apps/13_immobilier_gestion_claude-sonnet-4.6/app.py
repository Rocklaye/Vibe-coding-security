from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
from functools import wraps
import os
import uuid

# ── App setup ─────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gestimmo-secret-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestimmo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024   # 16 MB

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)


# ── Models ────────────────────────────────────────────────────────────────────

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(10), nullable=False)   # owner | tenant
    full_name     = db.Column(db.String(150), default='')
    phone         = db.Column(db.String(20), default='')
    address       = db.Column(db.String(300), default='')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    properties        = db.relationship('Property',   backref='owner',  lazy=True,
                                        foreign_keys='Property.owner_id')
    leases_as_tenant  = db.relationship('Lease',      backref='tenant', lazy=True,
                                        foreign_keys='Lease.tenant_id')


class Property(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    owner_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title         = db.Column(db.String(200), nullable=False)
    address       = db.Column(db.String(300), nullable=False)
    city          = db.Column(db.String(100), nullable=False)
    postal_code   = db.Column(db.String(10),  nullable=False)
    property_type = db.Column(db.String(50),  nullable=False)
    area_m2       = db.Column(db.Float, default=0)
    rooms         = db.Column(db.Integer, default=1)
    rent_amount   = db.Column(db.Float, nullable=False)
    charges       = db.Column(db.Float, default=0)
    deposit       = db.Column(db.Float, default=0)
    description   = db.Column(db.Text, default='')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    photos  = db.relationship('PropertyPhoto', backref='property', lazy=True,
                               cascade='all, delete-orphan')
    leases  = db.relationship('Lease', backref='property', lazy=True)

    @property
    def total_rent(self):
        return self.rent_amount + self.charges

    @property
    def active_lease(self):
        return next((l for l in self.leases if l.status == 'active'), None)

    @property
    def cover_photo(self):
        covers = [p for p in self.photos if p.is_cover]
        return covers[0] if covers else (self.photos[0] if self.photos else None)


class PropertyPhoto(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    filename    = db.Column(db.String(300), nullable=False)
    is_cover    = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Lease(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    property_id   = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    tenant_id     = db.Column(db.Integer, db.ForeignKey('user.id'),     nullable=False)
    start_date    = db.Column(db.Date, nullable=False)
    end_date      = db.Column(db.Date, nullable=True)
    rent_amount   = db.Column(db.Float, nullable=False)
    charges       = db.Column(db.Float, default=0)
    deposit       = db.Column(db.Float, default=0)
    payment_day   = db.Column(db.Integer, default=1)
    lease_type    = db.Column(db.String(20), default='vide')   # vide | meublé | commercial
    status        = db.Column(db.String(20), default='active') # active | terminated
    notes         = db.Column(db.Text, default='')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    payments    = db.relationship('Payment',    backref='lease', lazy=True,
                                  cascade='all, delete-orphan')
    inspections = db.relationship('Inspection', backref='lease', lazy=True,
                                  cascade='all, delete-orphan')

    @property
    def total_rent(self):
        return self.rent_amount + self.charges

    def is_paid_for(self, month, year):
        return any(p.period_month == month and p.period_year == year for p in self.payments)


class Payment(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    lease_id     = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    amount       = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    period_month = db.Column(db.Integer, nullable=False)
    period_year  = db.Column(db.Integer, nullable=False)
    method       = db.Column(db.String(20), default='virement')
    reference    = db.Column(db.String(100), default='')
    notes        = db.Column(db.Text, default='')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    MONTH_NAMES = ['Janvier','Février','Mars','Avril','Mai','Juin',
                   'Juillet','Août','Septembre','Octobre','Novembre','Décembre']

    @property
    def period_label(self):
        return f"{self.MONTH_NAMES[self.period_month - 1]} {self.period_year}"

    @property
    def receipt_number(self):
        return f"QIT-{self.period_year}{self.period_month:02d}-{self.id:04d}"


class Inspection(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    lease_id          = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    inspection_type   = db.Column(db.String(10), nullable=False)  # entree | sortie
    date              = db.Column(db.Date, nullable=False)
    general_condition = db.Column(db.String(20), default='bon')   # bon | moyen | mauvais
    notes             = db.Column(db.Text, default='')
    created_by        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    photos = db.relationship('InspectionPhoto', backref='inspection', lazy=True,
                              cascade='all, delete-orphan')


class InspectionPhoto(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspection.id'), nullable=False)
    filename      = db.Column(db.String(300), nullable=False)
    caption       = db.Column(db.String(200), default='')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ── Helpers ───────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def save_upload(file, subfolder='misc'):
    if file and file.filename and allowed_file(file.filename):
        ext      = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        folder   = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        return os.path.join(subfolder, filename).replace('\\', '/')
    return None


def current_user():
    return db.session.get(User, session['user_id']) if 'user_id' in session else None


def login_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            flash('Connexion requise.', 'error')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return deco


def owner_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'owner':
            flash('Accès réservé aux propriétaires.', 'error')
            return redirect(url_for('tenant_dashboard'))
        return f(*a, **kw)
    return deco


def tenant_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'tenant':
            flash('Accès réservé aux locataires.', 'error')
            return redirect(url_for('owner_dashboard'))
        return f(*a, **kw)
    return deco


def owner_prop(prop_id):
    """Return property or 404, ensuring it belongs to the current owner."""
    return Property.query.filter_by(id=prop_id, owner_id=session['user_id']).first_or_404()


def owner_lease(lease_id):
    return Lease.query.join(Property).filter(
        Lease.id == lease_id, Property.owner_id == session['user_id']
    ).first_or_404()


def overdue_leases(owner_id):
    today = date.today()
    active = Lease.query.join(Property).filter(
        Property.owner_id == owner_id, Lease.status == 'active'
    ).all()
    return [l for l in active
            if not l.is_paid_for(today.month, today.year) and today.day > l.payment_day]


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('owner_dashboard') if session['role'] == 'owner' else url_for('tenant_dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'].strip()).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session.update(user_id=user.id, username=user.username,
                           role=user.role, full_name=user.full_name or user.username)
            return redirect(url_for('index'))
        flash('Identifiants incorrects.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username  = request.form['username'].strip()
        email     = request.form['email'].strip().lower()
        password  = request.form['password']
        full_name = request.form['full_name'].strip()
        role      = request.form.get('role', 'owner')

        if not all([username, email, password, full_name]):
            flash('Tous les champs sont requis.', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Mot de passe : 6 caractères minimum.', 'error')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash("Nom d'utilisateur déjà pris.", 'error')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email déjà utilisé.', 'error')
            return render_template('register.html')

        user = User(username=username, email=email, full_name=full_name,
                    password_hash=generate_password_hash(password),
                    role=role if role in ('owner', 'tenant') else 'owner')
        db.session.add(user)
        db.session.commit()
        session.update(user_id=user.id, username=user.username,
                       role=user.role, full_name=user.full_name)
        flash('Compte créé !', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Owner : Dashboard ─────────────────────────────────────────────────────────

@app.route('/owner')
@owner_required
def owner_dashboard():
    uid   = session['user_id']
    today = date.today()
    props = Property.query.filter_by(owner_id=uid).all()
    active_leases = Lease.query.join(Property).filter(
        Property.owner_id == uid, Lease.status == 'active').all()
    overdue = overdue_leases(uid)
    monthly = sum(l.total_rent for l in active_leases)
    recent  = Payment.query.join(Lease).join(Property).filter(
        Property.owner_id == uid).order_by(Payment.created_at.desc()).limit(6).all()
    return render_template('owner_dashboard.html',
        props=props, active_leases=active_leases, overdue=overdue,
        monthly=monthly, recent=recent, today=today)


# ── Owner : Properties ────────────────────────────────────────────────────────

@app.route('/owner/properties')
@owner_required
def owner_properties():
    props = Property.query.filter_by(owner_id=session['user_id'])\
                          .order_by(Property.created_at.desc()).all()
    return render_template('properties.html', props=props)


@app.route('/owner/properties/new', methods=['GET', 'POST'])
@owner_required
def property_new():
    if request.method == 'POST':
        f = request.form
        prop = Property(
            owner_id=session['user_id'],
            title=f['title'].strip(),
            address=f['address'].strip(),
            city=f['city'].strip(),
            postal_code=f['postal_code'].strip(),
            property_type=f['property_type'],
            area_m2=float(f.get('area_m2') or 0),
            rooms=int(f.get('rooms') or 1),
            rent_amount=float(f.get('rent_amount') or 0),
            charges=float(f.get('charges') or 0),
            deposit=float(f.get('deposit') or 0),
            description=f.get('description', '').strip(),
        )
        db.session.add(prop)
        db.session.flush()
        for i, photo in enumerate(request.files.getlist('photos')):
            path = save_upload(photo, f'properties/{prop.id}')
            if path:
                db.session.add(PropertyPhoto(property_id=prop.id, filename=path, is_cover=(i == 0)))
        db.session.commit()
        flash('Bien ajouté !', 'success')
        return redirect(url_for('property_detail', prop_id=prop.id))
    return render_template('property_form.html', prop=None)


@app.route('/owner/properties/<int:prop_id>')
@owner_required
def property_detail(prop_id):
    prop    = owner_prop(prop_id)
    history = Payment.query.join(Lease).filter(Lease.property_id == prop_id)\
                           .order_by(Payment.payment_date.desc()).all()
    return render_template('property_detail.html', prop=prop, history=history)


@app.route('/owner/properties/<int:prop_id>/edit', methods=['GET', 'POST'])
@owner_required
def property_edit(prop_id):
    prop = owner_prop(prop_id)
    if request.method == 'POST':
        f = request.form
        prop.title         = f['title'].strip()
        prop.address       = f['address'].strip()
        prop.city          = f['city'].strip()
        prop.postal_code   = f['postal_code'].strip()
        prop.property_type = f['property_type']
        prop.area_m2       = float(f.get('area_m2') or 0)
        prop.rooms         = int(f.get('rooms') or 1)
        prop.rent_amount   = float(f.get('rent_amount') or 0)
        prop.charges       = float(f.get('charges') or 0)
        prop.deposit       = float(f.get('deposit') or 0)
        prop.description   = f.get('description', '').strip()
        for photo in request.files.getlist('photos'):
            path = save_upload(photo, f'properties/{prop.id}')
            if path:
                db.session.add(PropertyPhoto(property_id=prop.id, filename=path))
        db.session.commit()
        flash('Bien mis à jour.', 'success')
        return redirect(url_for('property_detail', prop_id=prop.id))
    return render_template('property_form.html', prop=prop)


@app.route('/owner/properties/<int:prop_id>/photo/<int:photo_id>/delete', methods=['POST'])
@owner_required
def property_photo_delete(prop_id, photo_id):
    prop  = owner_prop(prop_id)
    photo = PropertyPhoto.query.filter_by(id=photo_id, property_id=prop.id).first_or_404()
    db.session.delete(photo)
    db.session.commit()
    flash('Photo supprimée.', 'info')
    return redirect(url_for('property_edit', prop_id=prop.id))


@app.route('/owner/properties/<int:prop_id>/delete', methods=['POST'])
@owner_required
def property_delete(prop_id):
    prop = owner_prop(prop_id)
    db.session.delete(prop)
    db.session.commit()
    flash('Bien supprimé.', 'info')
    return redirect(url_for('owner_properties'))


# ── Owner : Tenants ───────────────────────────────────────────────────────────

@app.route('/owner/tenants')
@owner_required
def owner_tenants():
    tenants = db.session.query(User)\
        .join(Lease, User.id == Lease.tenant_id)\
        .join(Property, Lease.property_id == Property.id)\
        .filter(Property.owner_id == session['user_id'])\
        .distinct().all()
    return render_template('tenants.html', tenants=tenants)


@app.route('/owner/tenants/new', methods=['GET', 'POST'])
@owner_required
def tenant_new():
    if request.method == 'POST':
        username  = request.form['username'].strip()
        email     = request.form['email'].strip().lower()
        password  = request.form.get('password', '').strip() or 'locataire123'
        full_name = request.form['full_name'].strip()
        phone     = request.form.get('phone', '').strip()
        address   = request.form.get('address', '').strip()

        if User.query.filter_by(username=username).first():
            flash("Nom d'utilisateur déjà pris.", 'error')
            return render_template('tenant_form.html', tenant=None)
        if User.query.filter_by(email=email).first():
            flash('Email déjà utilisé.', 'error')
            return render_template('tenant_form.html', tenant=None)

        tenant = User(username=username, email=email, full_name=full_name,
                      phone=phone, address=address,
                      password_hash=generate_password_hash(password), role='tenant')
        db.session.add(tenant)
        db.session.commit()
        flash(f'Locataire créé. Identifiants : {username} / {password}', 'success')
        return redirect(url_for('owner_tenants'))
    return render_template('tenant_form.html', tenant=None)


@app.route('/owner/tenants/<int:tenant_id>')
@owner_required
def tenant_detail(tenant_id):
    tenant   = User.query.filter_by(id=tenant_id, role='tenant').first_or_404()
    leases   = Lease.query.join(Property).filter(
        Lease.tenant_id == tenant_id, Property.owner_id == session['user_id']).all()
    payments = Payment.query.join(Lease).join(Property).filter(
        Lease.tenant_id == tenant_id, Property.owner_id == session['user_id'])\
        .order_by(Payment.payment_date.desc()).all()
    return render_template('tenant_detail.html', tenant=tenant, leases=leases, payments=payments)


# ── Owner : Leases ────────────────────────────────────────────────────────────

@app.route('/owner/leases')
@owner_required
def owner_leases():
    leases = Lease.query.join(Property).filter(
        Property.owner_id == session['user_id']
    ).order_by(Lease.created_at.desc()).all()
    return render_template('leases.html', leases=leases)


@app.route('/owner/leases/new', methods=['GET', 'POST'])
@owner_required
def lease_new():
    props   = Property.query.filter_by(owner_id=session['user_id']).all()
    tenants = User.query.filter_by(role='tenant').all()
    if request.method == 'POST':
        f = request.form
        prop = Property.query.filter_by(id=int(f['property_id']),
                                         owner_id=session['user_id']).first_or_404()
        lease = Lease(
            property_id=prop.id,
            tenant_id=int(f['tenant_id']),
            start_date=date.fromisoformat(f['start_date']),
            end_date=date.fromisoformat(f['end_date']) if f.get('end_date') else None,
            rent_amount=float(f.get('rent_amount') or 0),
            charges=float(f.get('charges') or 0),
            deposit=float(f.get('deposit') or 0),
            payment_day=int(f.get('payment_day') or 1),
            lease_type=f.get('lease_type', 'vide'),
            notes=f.get('notes', '').strip(),
        )
        db.session.add(lease)
        db.session.commit()
        flash('Bail créé !', 'success')
        return redirect(url_for('owner_leases'))
    return render_template('lease_form.html', lease=None, props=props, tenants=tenants)


@app.route('/owner/leases/<int:lease_id>/terminate', methods=['POST'])
@owner_required
def lease_terminate(lease_id):
    lease = owner_lease(lease_id)
    lease.status = 'terminated'
    db.session.commit()
    flash('Bail résilié.', 'info')
    return redirect(url_for('owner_leases'))


# ── Owner : Payments ──────────────────────────────────────────────────────────

@app.route('/owner/payments')
@owner_required
def owner_payments():
    today  = date.today()
    uid    = session['user_id']
    payments = Payment.query.join(Lease).join(Property).filter(
        Property.owner_id == uid).order_by(Payment.payment_date.desc()).all()
    active_leases = Lease.query.join(Property).filter(
        Property.owner_id == uid, Lease.status == 'active').all()
    statuses = [{
        'lease': l,
        'paid':  l.is_paid_for(today.month, today.year),
        'overdue': not l.is_paid_for(today.month, today.year) and today.day > l.payment_day,
    } for l in active_leases]
    return render_template('payments.html', payments=payments, statuses=statuses, today=today)


@app.route('/owner/payments/new', methods=['GET', 'POST'])
@owner_required
def payment_new():
    uid    = session['user_id']
    leases = Lease.query.join(Property).filter(
        Property.owner_id == uid, Lease.status == 'active').all()
    today = date.today()

    preselect = request.args.get('lease_id', type=int)

    if request.method == 'POST':
        lease_id = int(request.form['lease_id'])
        lease    = owner_lease(lease_id)
        pmt = Payment(
            lease_id=lease_id,
            amount=float(request.form.get('amount') or 0),
            payment_date=date.fromisoformat(request.form['payment_date']),
            period_month=int(request.form['period_month']),
            period_year=int(request.form['period_year']),
            method=request.form.get('method', 'virement'),
            reference=request.form.get('reference', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(pmt)
        db.session.commit()
        flash('Paiement enregistré.', 'success')
        return redirect(url_for('owner_payments'))
    return render_template('payment_form.html', leases=leases, today=today, preselect=preselect)


@app.route('/owner/payments/<int:payment_id>/receipt')
@owner_required
def payment_receipt(payment_id):
    pmt = Payment.query.join(Lease).join(Property).filter(
        Property.owner_id == session['user_id'], Payment.id == payment_id).first_or_404()
    owner = current_user()
    return render_template('receipt.html', pmt=pmt, owner=owner)


@app.route('/owner/payments/<int:payment_id>/delete', methods=['POST'])
@owner_required
def payment_delete(payment_id):
    pmt = Payment.query.join(Lease).join(Property).filter(
        Property.owner_id == session['user_id'], Payment.id == payment_id).first_or_404()
    db.session.delete(pmt)
    db.session.commit()
    flash('Paiement supprimé.', 'info')
    return redirect(url_for('owner_payments'))


# ── Owner : Inspections ───────────────────────────────────────────────────────

@app.route('/owner/inspections')
@owner_required
def owner_inspections():
    inspections = Inspection.query.join(Lease).join(Property).filter(
        Property.owner_id == session['user_id']
    ).order_by(Inspection.date.desc()).all()
    leases = Lease.query.join(Property).filter(
        Property.owner_id == session['user_id']).all()
    return render_template('inspections.html', inspections=inspections, leases=leases)


@app.route('/owner/inspections/new', methods=['GET', 'POST'])
@owner_required
def inspection_new():
    leases = Lease.query.join(Property).filter(
        Property.owner_id == session['user_id'], Lease.status == 'active').all()
    if request.method == 'POST':
        f = request.form
        insp = Inspection(
            lease_id=int(f['lease_id']),
            inspection_type=f['inspection_type'],
            date=date.fromisoformat(f['date']),
            general_condition=f.get('general_condition', 'bon'),
            notes=f.get('notes', '').strip(),
            created_by=session['user_id'],
        )
        db.session.add(insp)
        db.session.flush()
        captions = request.form.getlist('captions')
        for i, photo in enumerate(request.files.getlist('photos')):
            path = save_upload(photo, f'inspections/{insp.id}')
            if path:
                db.session.add(InspectionPhoto(
                    inspection_id=insp.id, filename=path,
                    caption=captions[i] if i < len(captions) else ''))
        db.session.commit()
        flash('État des lieux enregistré.', 'success')
        return redirect(url_for('owner_inspections'))
    return render_template('inspection_form.html', leases=leases, today=date.today())


@app.route('/owner/inspections/<int:insp_id>')
@owner_required
def inspection_detail(insp_id):
    insp = Inspection.query.join(Lease).join(Property).filter(
        Property.owner_id == session['user_id'], Inspection.id == insp_id).first_or_404()
    return render_template('inspection_detail.html', insp=insp)


# ── Tenant ────────────────────────────────────────────────────────────────────

@app.route('/tenant')
@tenant_required
def tenant_dashboard():
    uid   = session['user_id']
    today = date.today()
    lease = Lease.query.filter_by(tenant_id=uid, status='active').first()
    payments = Payment.query.filter_by(lease_id=lease.id)\
        .order_by(Payment.payment_date.desc()).all() if lease else []
    paid_this_month = lease.is_paid_for(today.month, today.year) if lease else True
    return render_template('tenant_dashboard.html',
        lease=lease, payments=payments[:5],
        paid_this_month=paid_this_month, today=today)


@app.route('/tenant/payments')
@tenant_required
def tenant_payments():
    payments = Payment.query.join(Lease).filter(
        Lease.tenant_id == session['user_id']
    ).order_by(Payment.payment_date.desc()).all()
    return render_template('tenant_payments.html', payments=payments)


@app.route('/tenant/payments/<int:payment_id>/receipt')
@tenant_required
def tenant_receipt(payment_id):
    pmt = Payment.query.join(Lease).filter(
        Lease.tenant_id == session['user_id'], Payment.id == payment_id).first_or_404()
    owner = db.session.get(User, pmt.lease.property.owner_id)
    return render_template('receipt.html', pmt=pmt, owner=owner)


@app.route('/tenant/documents')
@tenant_required
def tenant_documents():
    leases = Lease.query.filter_by(tenant_id=session['user_id']).all()
    inspections = Inspection.query.join(Lease).filter(
        Lease.tenant_id == session['user_id']).order_by(Inspection.date.desc()).all()
    return render_template('tenant_documents.html', leases=leases, inspections=inspections)


# ── Static uploads ────────────────────────────────────────────────────────────

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ── Template filters ──────────────────────────────────────────────────────────

@app.template_filter('eur')
def eur(v):
    if v is None:
        return '0,00 €'
    return f"{v:,.2f} €".replace(',', '\xa0').replace('.', ',')


@app.template_filter('dfr')
def dfr(d):
    if not d:
        return ''
    mois = ['janvier','février','mars','avril','mai','juin',
            'juillet','août','septembre','octobre','novembre','décembre']
    return f"{d.day} {mois[d.month-1]} {d.year}"


@app.template_filter('mfr')
def mfr(n):
    mois = ['Janvier','Février','Mars','Avril','Mai','Juin',
            'Juillet','Août','Septembre','Octobre','Novembre','Décembre']
    return mois[int(n) - 1]


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=8081)
