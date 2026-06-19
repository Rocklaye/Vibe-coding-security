"""
Système d'authentification et gestion des accès
"""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash
from models import User

def login_required(f):
    """Décorateur : nécessite une connexion"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentification requise'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """Décorateur : nécessite un rôle minimum"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentification requise'}), 401
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                session.clear()
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Compte désactivé'}), 403
                return redirect(url_for('login'))
            
            if not user.has_role(role):
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Accès non autorisé'}), 403
                flash('Accès non autorisé', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Récupère l'utilisateur connecté"""
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

def log_action(entity_type, entity_id, action, details=None):
    """Enregistre une action dans le journal d'audit"""
    from models import db, AuditLog
    from flask import request
    
    audit = AuditLog(
        user_id=session.get('user_id'),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
