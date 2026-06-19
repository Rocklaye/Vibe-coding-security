from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from functools import wraps
import os
import json

# ── Setup ─────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secops-dev-secret-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secops.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Constants ─────────────────────────────────────────────────────────────────

SEVERITIES   = ['critical', 'high', 'medium', 'low']
STATUSES     = ['open', 'investigating', 'contained', 'eradicated', 'recovering', 'resolved', 'closed', 'false_positive']
CATEGORIES   = ['Phishing', 'Malware', 'Ransomware', 'DDoS', 'Data Breach',
                'Insider Threat', 'Unauthorized Access', 'Vulnerability Exploitation',
                'Social Engineering', 'Brute Force', 'Supply Chain', 'Other']
ROLES        = ['analyst', 'manager', 'admin']
EVENT_TYPES  = ['detection', 'investigation', 'containment', 'eradication',
                'recovery', 'communication', 'escalation', 'remediation', 'other']

# ── Models ────────────────────────────────────────────────────────────────────

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(150), nullable=False)
    role          = db.Column(db.String(20), nullable=False, default='analyst')
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_incidents = db.relationship('Incident', backref='assignee', lazy=True,
                                          foreign_keys='Incident.assigned_to')
    created_incidents  = db.relationship('Incident', backref='creator', lazy=True,
                                          foreign_keys='Incident.created_by')

    @property
    def open_count(self):
        return Incident.query.filter(
            Incident.assigned_to == self.id,
            Incident.status.notin_(['resolved', 'closed', 'false_positive'])
        ).count()


class Incident(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    ref              = db.Column(db.String(20), unique=True, nullable=False)
    title            = db.Column(db.String(300), nullable=False)
    description      = db.Column(db.Text, default='')
    severity         = db.Column(db.String(20), nullable=False, default='medium')
    status           = db.Column(db.String(30), nullable=False, default='open')
    category         = db.Column(db.String(50), nullable=False, default='Other')
    source           = db.Column(db.String(200), default='')
    affected_systems = db.Column(db.Text, default='')
    ioc              = db.Column(db.Text, default='')
    assigned_to      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at      = db.Column(db.DateTime, nullable=True)
    closed_at        = db.Column(db.DateTime, nullable=True)

    timeline_events = db.relationship('TimelineEvent', backref='incident', lazy=True,
                                       cascade='all, delete-orphan',
                                       order_by='TimelineEvent.event_time')
    comments        = db.relationship('Comment', backref='incident', lazy=True,
                                       cascade='all, delete-orphan',
                                       order_by='Comment.created_at')

    @property
    def is_active(self):
        return self.status not in ('resolved', 'closed', 'false_positive')

    @property
    def mttr_hours(self):
        if self.resolved_at:
            return round((self.resolved_at - self.created_at).total_seconds() / 3600, 1)
        return None

    @property
    def age_hours(self):
        end = self.resolved_at or datetime.utcnow()
        return round((end - self.created_at).total_seconds() / 3600, 1)


class TimelineEvent(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incident.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type  = db.Column(db.String(30), nullable=False, default='other')
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    event_time  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', foreign_keys=[user_id])


class Comment(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incident.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', foreign_keys=[user_id])


class AuditLog(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action      = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), default='')
    target_id   = db.Column(db.Integer, nullable=True)
    target_ref  = db.Column(db.String(50), default='')
    details     = db.Column(db.Text, default='')
    ip_address  = db.Column(db.String(45), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])


# ── Helpers ───────────────────────────────────────────────────────────────────

def log_audit(action, target_type='', target_id=None, target_ref='', details=''):
    entry = AuditLog(
        user_id=session.get('user_id'),
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_ref=target_ref,
        details=details,
        ip_address=request.remote_addr or '',
    )
    db.session.add(entry)


def next_ref():
    last = Incident.query.order_by(Incident.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"INC-{n:05d}"


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


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def deco(*a, **kw):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Accès non autorisé.', 'error')
                return redirect(url_for('dashboard'))
            return f(*a, **kw)
        return deco
    return decorator


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username, is_active=True).first()

        if user and check_password_hash(user.password_hash, password):
            session.update(user_id=user.id, username=user.username,
                           role=user.role, full_name=user.full_name)
            log_audit('LOGIN', 'user', user.id, user.username)
            db.session.commit()
            return redirect(url_for('dashboard'))

        flash('Identifiants incorrects ou compte désactivé.', 'error')
        log_audit('LOGIN_FAIL', details=f'username={username}')
        db.session.commit()

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Only allow registration if no users exist, or if admin is logged in
    user_count = User.query.count()
    if user_count > 0 and session.get('role') != 'admin':
        flash('Les inscriptions sont fermées. Contactez un administrateur.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username  = request.form['username'].strip()
        email     = request.form['email'].strip().lower()
        password  = request.form['password']
        full_name = request.form['full_name'].strip()
        role      = request.form.get('role', 'analyst')

        if len(password) < 8:
            flash('Mot de passe : 8 caractères minimum.', 'error')
            return render_template('register.html', first=user_count == 0)

        if User.query.filter_by(username=username).first():
            flash("Nom d'utilisateur déjà pris.", 'error')
            return render_template('register.html', first=user_count == 0)

        if User.query.filter_by(email=email).first():
            flash('Email déjà utilisé.', 'error')
            return render_template('register.html', first=user_count == 0)

        # First user is always admin
        if user_count == 0:
            role = 'admin'

        user = User(username=username, email=email, full_name=full_name,
                    password_hash=generate_password_hash(password),
                    role=role if role in ROLES else 'analyst')
        db.session.add(user)
        db.session.flush()
        log_audit('USER_CREATED', 'user', user.id, username, f'role={role}')
        db.session.commit()

        if 'user_id' not in session:
            session.update(user_id=user.id, username=user.username,
                           role=user.role, full_name=user.full_name)
        else:
            flash(f'Compte {username} créé.', 'success')
            return redirect(url_for('admin_users'))

        flash('Compte créé ! Bienvenue.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html', first=user_count == 0)


@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_audit('LOGOUT')
        db.session.commit()
    session.clear()
    return redirect(url_for('login'))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    now = datetime.utcnow()
    thirty_ago = now - timedelta(days=30)
    seven_ago  = now - timedelta(days=7)

    total_open = Incident.query.filter(
        Incident.status.notin_(['resolved', 'closed', 'false_positive'])).count()

    by_severity = {s: Incident.query.filter(
        Incident.severity == s,
        Incident.status.notin_(['resolved', 'closed', 'false_positive'])
    ).count() for s in SEVERITIES}

    by_status = {s: Incident.query.filter_by(status=s).count() for s in STATUSES}

    # MTTR last 30 days
    resolved_recent = Incident.query.filter(
        Incident.resolved_at.isnot(None),
        Incident.resolved_at >= thirty_ago
    ).all()
    mttr = 0
    if resolved_recent:
        times = [(i.resolved_at - i.created_at).total_seconds() / 3600
                 for i in resolved_recent]
        mttr = round(sum(times) / len(times), 1)

    # Incidents last 7 days (per day)
    daily = []
    for d in range(6, -1, -1):
        day = now - timedelta(days=d)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = start + timedelta(days=1)
        count = Incident.query.filter(
            Incident.created_at >= start, Incident.created_at < end).count()
        daily.append({'label': start.strftime('%a'), 'count': count})

    # Recent incidents
    recent = Incident.query.order_by(Incident.created_at.desc()).limit(8).all()

    # My incidents (for analysts)
    my_incidents = []
    if session['role'] == 'analyst':
        my_incidents = Incident.query.filter(
            Incident.assigned_to == session['user_id'],
            Incident.status.notin_(['resolved', 'closed', 'false_positive'])
        ).order_by(Incident.severity.asc()).all()

    # Analyst workload (for managers/admins)
    analysts_load = []
    if session['role'] in ('manager', 'admin'):
        analysts = User.query.filter(
            User.role.in_(['analyst', 'manager']), User.is_active == True).all()
        analysts_load = [(u, u.open_count) for u in analysts]

    total_last30 = Incident.query.filter(Incident.created_at >= thirty_ago).count()
    total_last7  = Incident.query.filter(Incident.created_at >= seven_ago).count()

    return render_template('dashboard.html',
        total_open=total_open, by_severity=by_severity, by_status=by_status,
        mttr=mttr, daily=daily, recent=recent, my_incidents=my_incidents,
        analysts_load=analysts_load, total_last30=total_last30, total_last7=total_last7,
        now=now)


# ── Incidents ─────────────────────────────────────────────────────────────────

@app.route('/incidents')
@login_required
def incidents():
    sev    = request.args.get('severity', '')
    status = request.args.get('status', '')
    cat    = request.args.get('category', '')
    assign = request.args.get('assigned', '')
    q      = request.args.get('q', '').strip()

    query = Incident.query

    if sev:    query = query.filter_by(severity=sev)
    if status: query = query.filter_by(status=status)
    if cat:    query = query.filter_by(category=cat)
    if assign == 'me':
        query = query.filter_by(assigned_to=session['user_id'])
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(Incident.title.ilike(like), Incident.ref.ilike(like),
                   Incident.description.ilike(like)))

    incs = query.order_by(Incident.created_at.desc()).all()
    analysts = User.query.filter(User.role.in_(['analyst', 'manager']),
                                  User.is_active == True).all()

    return render_template('incidents.html', incs=incs, analysts=analysts,
        severities=SEVERITIES, statuses=STATUSES, categories=CATEGORIES,
        filters={'severity': sev, 'status': status, 'category': cat,
                 'assigned': assign, 'q': q})


@app.route('/incidents/new', methods=['GET', 'POST'])
@login_required
def incident_new():
    analysts = User.query.filter(User.role.in_(['analyst', 'manager']),
                                  User.is_active == True).all()
    if request.method == 'POST':
        f = request.form
        inc = Incident(
            ref=next_ref(),
            title=f['title'].strip(),
            description=f.get('description', '').strip(),
            severity=f.get('severity', 'medium'),
            status='open',
            category=f.get('category', 'Other'),
            source=f.get('source', '').strip(),
            affected_systems=f.get('affected_systems', '').strip(),
            ioc=f.get('ioc', '').strip(),
            assigned_to=int(f['assigned_to']) if f.get('assigned_to') else None,
            created_by=session['user_id'],
        )
        db.session.add(inc)
        db.session.flush()

        # Auto-add detection event
        ev = TimelineEvent(
            incident_id=inc.id,
            user_id=session['user_id'],
            event_type='detection',
            title='Incident détecté / créé',
            description=f"Incident créé par {session['full_name']}. Source: {inc.source or 'N/A'}",
            event_time=datetime.utcnow(),
        )
        db.session.add(ev)
        log_audit('INCIDENT_CREATED', 'incident', inc.id, inc.ref,
                  f'severity={inc.severity} category={inc.category}')
        db.session.commit()
        flash(f'Incident {inc.ref} créé.', 'success')
        return redirect(url_for('incident_detail', inc_id=inc.id))

    return render_template('incident_form.html', inc=None,
        analysts=analysts, severities=SEVERITIES,
        categories=CATEGORIES, event_types=EVENT_TYPES)


@app.route('/incidents/<int:inc_id>')
@login_required
def incident_detail(inc_id):
    inc      = Incident.query.get_or_404(inc_id)
    analysts = User.query.filter(User.role.in_(['analyst', 'manager']),
                                  User.is_active == True).all()
    return render_template('incident_detail.html', inc=inc,
        analysts=analysts, statuses=STATUSES, event_types=EVENT_TYPES,
        SEVERITIES=SEVERITIES)


@app.route('/incidents/<int:inc_id>/edit', methods=['GET', 'POST'])
@login_required
def incident_edit(inc_id):
    inc      = Incident.query.get_or_404(inc_id)
    analysts = User.query.filter(User.role.in_(['analyst', 'manager']),
                                  User.is_active == True).all()

    if request.method == 'POST':
        old_sev = inc.severity
        f = request.form
        inc.title            = f['title'].strip()
        inc.description      = f.get('description', '').strip()
        inc.severity         = f.get('severity', inc.severity)
        inc.category         = f.get('category', inc.category)
        inc.source           = f.get('source', '').strip()
        inc.affected_systems = f.get('affected_systems', '').strip()
        inc.ioc              = f.get('ioc', '').strip()
        inc.updated_at       = datetime.utcnow()

        changes = []
        if old_sev != inc.severity:
            changes.append(f'severity: {old_sev}→{inc.severity}')

        log_audit('INCIDENT_UPDATED', 'incident', inc.id, inc.ref,
                  '; '.join(changes) if changes else 'fields updated')
        db.session.commit()
        flash('Incident mis à jour.', 'success')
        return redirect(url_for('incident_detail', inc_id=inc.id))

    return render_template('incident_form.html', inc=inc,
        analysts=analysts, severities=SEVERITIES,
        categories=CATEGORIES, event_types=EVENT_TYPES)


@app.route('/incidents/<int:inc_id>/status', methods=['POST'])
@login_required
def incident_status(inc_id):
    inc        = Incident.query.get_or_404(inc_id)
    new_status = request.form.get('status', '')

    if new_status not in STATUSES:
        flash('Statut invalide.', 'error')
        return redirect(url_for('incident_detail', inc_id=inc_id))

    if session['role'] == 'analyst' and new_status in ('closed', 'false_positive'):
        flash('Seuls les managers/admins peuvent fermer un incident.', 'error')
        return redirect(url_for('incident_detail', inc_id=inc_id))

    old_status = inc.status
    inc.status     = new_status
    inc.updated_at = datetime.utcnow()

    if new_status == 'resolved' and not inc.resolved_at:
        inc.resolved_at = datetime.utcnow()
    if new_status in ('closed', 'false_positive') and not inc.closed_at:
        inc.closed_at = datetime.utcnow()

    # Auto timeline event
    ev = TimelineEvent(
        incident_id=inc.id,
        user_id=session['user_id'],
        event_type='investigation' if new_status == 'investigating' else
                   'containment'  if new_status == 'contained'     else
                   'eradication'  if new_status == 'eradicated'    else
                   'recovery'     if new_status == 'recovering'    else 'other',
        title=f'Statut changé : {old_status} → {new_status}',
        description=request.form.get('note', '').strip(),
        event_time=datetime.utcnow(),
    )
    db.session.add(ev)
    log_audit('STATUS_CHANGED', 'incident', inc.id, inc.ref,
              f'{old_status}→{new_status}')
    db.session.commit()
    flash(f'Statut mis à jour : {new_status}.', 'success')
    return redirect(url_for('incident_detail', inc_id=inc_id))


@app.route('/incidents/<int:inc_id>/assign', methods=['POST'])
@role_required('manager', 'admin')
def incident_assign(inc_id):
    inc         = Incident.query.get_or_404(inc_id)
    analyst_id  = request.form.get('analyst_id', type=int)
    old_assignee = inc.assignee.full_name if inc.assignee else 'Non assigné'

    inc.assigned_to = analyst_id if analyst_id else None
    inc.updated_at  = datetime.utcnow()
    new_assignee    = inc.assignee.full_name if inc.assignee else 'Non assigné'

    log_audit('INCIDENT_ASSIGNED', 'incident', inc.id, inc.ref,
              f'{old_assignee} → {new_assignee}')
    db.session.commit()
    flash('Analyste assigné.', 'success')
    return redirect(url_for('incident_detail', inc_id=inc_id))


@app.route('/incidents/<int:inc_id>/severity', methods=['POST'])
@role_required('manager', 'admin')
def incident_severity(inc_id):
    inc     = Incident.query.get_or_404(inc_id)
    new_sev = request.form.get('severity', '')
    if new_sev not in SEVERITIES:
        flash('Sévérité invalide.', 'error')
        return redirect(url_for('incident_detail', inc_id=inc_id))

    old_sev    = inc.severity
    inc.severity   = new_sev
    inc.updated_at = datetime.utcnow()
    log_audit('SEVERITY_CHANGED', 'incident', inc.id, inc.ref,
              f'{old_sev}→{new_sev}')
    db.session.commit()
    flash(f'Sévérité mise à jour : {new_sev}.', 'success')
    return redirect(url_for('incident_detail', inc_id=inc_id))


@app.route('/incidents/<int:inc_id>/timeline', methods=['POST'])
@login_required
def timeline_add(inc_id):
    inc = Incident.query.get_or_404(inc_id)
    f   = request.form

    raw_dt = f.get('event_time', '').strip()
    try:
        event_time = datetime.fromisoformat(raw_dt) if raw_dt else datetime.utcnow()
    except ValueError:
        event_time = datetime.utcnow()

    ev = TimelineEvent(
        incident_id=inc_id,
        user_id=session['user_id'],
        event_type=f.get('event_type', 'other'),
        title=f['title'].strip(),
        description=f.get('description', '').strip(),
        event_time=event_time,
    )
    db.session.add(ev)
    log_audit('TIMELINE_EVENT', 'incident', inc.id, inc.ref,
              f'{ev.event_type}: {ev.title[:60]}')
    db.session.commit()
    flash('Événement ajouté à la timeline.', 'success')
    return redirect(url_for('incident_detail', inc_id=inc_id))


@app.route('/incidents/<int:inc_id>/comment', methods=['POST'])
@login_required
def comment_add(inc_id):
    inc     = Incident.query.get_or_404(inc_id)
    content = request.form.get('content', '').strip()
    if not content:
        flash('Le commentaire ne peut pas être vide.', 'error')
        return redirect(url_for('incident_detail', inc_id=inc_id))

    is_internal = 'is_internal' in request.form
    c = Comment(incident_id=inc_id, user_id=session['user_id'],
                content=content, is_internal=is_internal)
    db.session.add(c)
    log_audit('COMMENT_ADDED', 'incident', inc.id, inc.ref,
              f'internal={is_internal}')
    db.session.commit()
    flash('Commentaire ajouté.', 'success')
    return redirect(url_for('incident_detail', inc_id=inc_id))


# ── Analysts ──────────────────────────────────────────────────────────────────

@app.route('/analysts')
@login_required
def analysts():
    users = User.query.filter(
        User.role.in_(['analyst', 'manager']), User.is_active == True
    ).all()

    data = []
    for u in users:
        incs_by_sev = {s: Incident.query.filter(
            Incident.assigned_to == u.id,
            Incident.severity == s,
            Incident.status.notin_(['resolved', 'closed', 'false_positive'])
        ).count() for s in SEVERITIES}

        resolved_count = Incident.query.filter(
            Incident.assigned_to == u.id,
            Incident.status.in_(['resolved', 'closed'])
        ).count()

        data.append({'user': u, 'by_sev': incs_by_sev,
                     'open': u.open_count, 'resolved': resolved_count})

    return render_template('analysts.html', data=data)


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route('/admin/users')
@role_required('admin')
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users, roles=ROLES)


@app.route('/admin/users/new', methods=['POST'])
@role_required('admin')
def admin_user_new():
    username  = request.form['username'].strip()
    email     = request.form['email'].strip().lower()
    full_name = request.form['full_name'].strip()
    role      = request.form.get('role', 'analyst')
    password  = request.form.get('password', '').strip() or 'Secops2024!'

    if User.query.filter_by(username=username).first():
        flash("Nom d'utilisateur déjà pris.", 'error')
        return redirect(url_for('admin_users'))

    user = User(username=username, email=email, full_name=full_name,
                password_hash=generate_password_hash(password),
                role=role if role in ROLES else 'analyst')
    db.session.add(user)
    db.session.flush()
    log_audit('USER_CREATED', 'user', user.id, username,
              f'role={role} by admin')
    db.session.commit()
    flash(f'Utilisateur {username} créé. MDP: {password}', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:uid>/toggle', methods=['POST'])
@role_required('admin')
def admin_user_toggle(uid):
    user = User.query.get_or_404(uid)
    if user.id == session['user_id']:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'error')
        return redirect(url_for('admin_users'))
    user.is_active = not user.is_active
    log_audit('USER_TOGGLED', 'user', user.id, user.username,
              f'active={user.is_active}')
    db.session.commit()
    flash(f'Compte {"activé" if user.is_active else "désactivé"}.', 'info')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:uid>/role', methods=['POST'])
@role_required('admin')
def admin_user_role(uid):
    user    = User.query.get_or_404(uid)
    new_role = request.form.get('role', 'analyst')
    if new_role not in ROLES:
        flash('Rôle invalide.', 'error')
        return redirect(url_for('admin_users'))
    old_role   = user.role
    user.role  = new_role
    log_audit('USER_ROLE_CHANGED', 'user', user.id, user.username,
              f'{old_role}→{new_role}')
    db.session.commit()
    flash(f'Rôle de {user.username} changé en {new_role}.', 'success')
    return redirect(url_for('admin_users'))


# ── Audit log ─────────────────────────────────────────────────────────────────

@app.route('/audit')
@role_required('manager', 'admin')
def audit_log():
    page    = request.args.get('page', 1, type=int)
    action  = request.args.get('action', '')
    user_id = request.args.get('user_id', type=int)

    query = AuditLog.query
    if action:   query = query.filter(AuditLog.action.ilike(f'%{action}%'))
    if user_id:  query = query.filter_by(user_id=user_id)

    logs  = query.order_by(AuditLog.created_at.desc()).limit(200).all()
    users = User.query.order_by(User.full_name).all()

    return render_template('audit_log.html', logs=logs, users=users,
                           action=action, sel_user=user_id)


# ── API (JSON) ────────────────────────────────────────────────────────────────

@app.route('/api/metrics')
@login_required
def api_metrics():
    by_sev = {s: Incident.query.filter(
        Incident.severity == s,
        Incident.status.notin_(['resolved', 'closed', 'false_positive'])
    ).count() for s in SEVERITIES}
    total_open = sum(by_sev.values())
    return jsonify({'total_open': total_open, 'by_severity': by_sev})


# ── Template filters ──────────────────────────────────────────────────────────

@app.template_filter('dt')
def dt_filter(d):
    if not d:
        return '—'
    return d.strftime('%d/%m/%Y %H:%M')


@app.template_filter('timeago')
def timeago_filter(d):
    if not d:
        return ''
    diff = int((datetime.utcnow() - d).total_seconds())
    if diff < 60:       return 'à l\'instant'
    if diff < 3600:     return f'il y a {diff//60} min'
    if diff < 86400:    return f'il y a {diff//3600}h'
    if diff < 2592000:  return f'il y a {diff//86400}j'
    return d.strftime('%d/%m/%Y')


@app.template_filter('sev_class')
def sev_class(s):
    return {'critical': 'sev-crit', 'high': 'sev-high',
            'medium': 'sev-med', 'low': 'sev-low'}.get(s, '')


@app.template_filter('status_class')
def status_class(s):
    mapping = {
        'open': 'st-open', 'investigating': 'st-inv',
        'contained': 'st-cont', 'eradicated': 'st-erad',
        'recovering': 'st-rec', 'resolved': 'st-res',
        'closed': 'st-closed', 'false_positive': 'st-fp',
    }
    return mapping.get(s, '')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8082)
