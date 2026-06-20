from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, Profile, Content, WatchHistory, Subscription
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre-cle-secrete-tres-longue-et-complexe'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streaming.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes principales
@app.route('/')
def index():
    contents = Content.query.all()
    return render_template('index.html', contents=contents)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(email=email).first():
            flash('Email déjà utilisé', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, name=name, 
                   subscription_type='free', subscription_end=datetime.now() + timedelta(days=30))
        db.session.add(user)
        db.session.commit()
        
        # Créer un profil par défaut
        profile = Profile(name=name, user_id=user.id, is_default=True)
        db.session.add(profile)
        db.session.commit()
        
        flash('Inscription réussie !', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            session['active_profile_id'] = user.profiles[0].id if user.profiles else None
            return redirect(url_for('dashboard'))
        
        flash('Email ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    contents = Content.query.all()
    profiles = current_user.profiles
    active_profile_id = session.get('active_profile_id')
    
    # Obtenir l'historique pour les recommandations
    if active_profile_id:
        history = WatchHistory.query.filter_by(profile_id=active_profile_id).order_by(WatchHistory.watched_at.desc()).limit(10).all()
        watched_content_ids = [h.content_id for h in history]
        
        # Recommandations simples basées sur les catégories regardées
        if watched_content_ids:
            watched_categories = set()
            for content_id in watched_content_ids:
                content = Content.query.get(content_id)
                if content:
                    watched_categories.add(content.category)
            
            recommendations = Content.query.filter(
                Content.category.in_(watched_categories),
                Content.id.notin_(watched_content_ids)
            ).limit(5).all()
        else:
            recommendations = Content.query.order_by(db.func.random()).limit(5).all()
    else:
        recommendations = Content.query.order_by(db.func.random()).limit(5).all()
        history = []
    
    return render_template('dashboard.html', contents=contents, profiles=profiles, 
                         recommendations=recommendations, history=history)

@app.route('/player/<int:content_id>')
@login_required
def player(content_id):
    content = Content.query.get_or_404(content_id)
    
    # Vérifier l'accès
    if content.is_premium and current_user.subscription_type != 'premium':
        flash('Ce contenu est réservé aux abonnés premium', 'error')
        return redirect(url_for('dashboard'))
    
    # Enregistrer dans l'historique
    active_profile_id = session.get('active_profile_id')
    if active_profile_id:
        history = WatchHistory(
            profile_id=active_profile_id,
            content_id=content.id,
            watched_at=datetime.now()
        )
        db.session.add(history)
        db.session.commit()
    
    # Contenus similaires
    similar_contents = Content.query.filter(
        Content.category == content.category,
        Content.id != content.id
    ).limit(4).all()
    
    return render_template('player.html', content=content, similar_contents=similar_contents)

@app.route('/profiles')
@login_required
def profiles():
    profiles = current_user.profiles
    return render_template('profiles.html', profiles=profiles)

@app.route('/profiles/add', methods=['POST'])
@login_required
def add_profile():
    if len(current_user.profiles) >= 5:
        flash('Maximum 5 profils par compte', 'error')
        return redirect(url_for('profiles'))
    
    name = request.form.get('name')
    if name:
        profile = Profile(name=name, user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
        flash('Profil créé avec succès', 'success')
    
    return redirect(url_for('profiles'))

@app.route('/profiles/switch/<int:profile_id>')
@login_required
def switch_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id == current_user.id:
        session['active_profile_id'] = profile.id
        flash(f'Profil changé pour {profile.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/profiles/delete/<int:profile_id>')
@login_required
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id == current_user.id and not profile.is_default:
        db.session.delete(profile)
        db.session.commit()
        flash('Profil supprimé', 'success')
    return redirect(url_for('profiles'))

@app.route('/subscription')
@login_required
def subscription():
    return render_template('subscription.html')

@app.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    plan = request.form.get('plan')
    if plan in ['monthly', 'yearly']:
        # Simuler un paiement
        current_user.subscription_type = 'premium'
        current_user.subscription_start = datetime.now()
        
        if plan == 'monthly':
            current_user.subscription_end = datetime.now() + timedelta(days=30)
            current_user.subscription_price = 9.99
        else:
            current_user.subscription_end = datetime.now() + timedelta(days=365)
            current_user.subscription_price = 99.99
        
        # Enregistrer l'abonnement
        subscription_record = Subscription(
            user_id=current_user.id,
            plan=plan,
            price=current_user.subscription_price,
            start_date=current_user.subscription_start,
            end_date=current_user.subscription_end
        )
        db.session.add(subscription_record)
        db.session.commit()
        
        flash('Abonnement premium activé avec succès !', 'success')
    
    return redirect(url_for('subscription'))

@app.route('/subscription/cancel')
@login_required
def cancel_subscription():
    current_user.subscription_type = 'free'
    db.session.commit()
    flash('Abonnement premium annulé', 'info')
    return redirect(url_for('subscription'))

@app.route('/admin')
@login_required
def admin():
    if current_user.email != 'admin@stream.com':
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    contents = Content.query.all()
    subscriptions = Subscription.query.order_by(Subscription.start_date.desc()).limit(20).all()
    
    return render_template('admin.html', users=users, contents=contents, subscriptions=subscriptions)

@app.route('/admin/content/add', methods=['POST'])
@login_required
def add_content():
    if current_user.email != 'admin@stream.com':
        return jsonify({'error': 'Non autorisé'}), 403
    
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    image_url = request.form.get('image_url')
    is_premium = 'is_premium' in request.form
    
    if title and category:
        content = Content(
            title=title,
            description=description,
            category=category,
            image_url=image_url or '/static/images/default.jpg',
            is_premium=is_premium
        )
        db.session.add(content)
        db.session.commit()
        flash('Contenu ajouté avec succès', 'success')
    
    return redirect(url_for('admin'))

@app.route('/admin/content/delete/<int:content_id>')
@login_required
def delete_content(content_id):
    if current_user.email != 'admin@stream.com':
        return jsonify({'error': 'Non autorisé'}), 403
    
    content = Content.query.get_or_404(content_id)
    db.session.delete(content)
    db.session.commit()
    flash('Contenu supprimé', 'success')
    
    return redirect(url_for('admin'))

@app.route('/recommendations')
@login_required
def recommendations():
    active_profile_id = session.get('active_profile_id')
    
    if active_profile_id:
        history = WatchHistory.query.filter_by(profile_id=active_profile_id).order_by(WatchHistory.watched_at.desc()).all()
        
        if history:
            # Analyse des préférences
            categories_count = {}
            for h in history:
                content = Content.query.get(h.content_id)
                if content:
                    categories_count[content.category] = categories_count.get(content.category, 0) + 1
            
            # Catégorie préférée
            favorite_category = max(categories_count, key=categories_count.get) if categories_count else None
            
            watched_ids = [h.content_id for h in history]
            
            # Recommandations par catégorie préférée
            category_recommendations = Content.query.filter(
                Content.category == favorite_category,
                Content.id.notin_(watched_ids)
            ).limit(5).all() if favorite_category else []
            
            # Nouvelles sorties
            new_releases = Content.query.filter(
                Content.id.notin_(watched_ids)
            ).order_by(Content.created_at.desc()).limit(5).all()
            
            # Populaires (basé sur l'historique global)
            popular_content_ids = db.session.query(
                WatchHistory.content_id,
                db.func.count(WatchHistory.content_id).label('count')
            ).group_by(WatchHistory.content_id).order_by(db.desc('count')).limit(5).all()
            
            popular_content = []
            for content_id, _ in popular_content_ids:
                content = Content.query.get(content_id)
                if content and content.id not in watched_ids:
                    popular_content.append(content)
            
            return render_template('recommendations.html', 
                                 category_recommendations=category_recommendations,
                                 new_releases=new_releases,
                                 popular_content=popular_content,
                                 favorite_category=favorite_category)
    
    # Si pas d'historique, montrer des suggestions aléatoires
    random_content = Content.query.order_by(db.func.random()).limit(15).all()
    return render_template('recommendations.html', 
                         category_recommendations=random_content[:5],
                         new_releases=random_content[5:10],
                         popular_content=random_content[10:15],
                         favorite_category=None)

# API pour les fonctionnalités AJAX
@app.route('/api/search')
@login_required
def search():
    query = request.args.get('q', '')
    if query:
        contents = Content.query.filter(Content.title.contains(query)).all()
        return jsonify([{
            'id': c.id,
            'title': c.title,
            'category': c.category,
            'is_premium': c.is_premium
        } for c in contents])
    return jsonify([])

@app.route('/api/watch-progress', methods=['POST'])
@login_required
def update_watch_progress():
    data = request.json
    content_id = data.get('content_id')
    progress = data.get('progress')
    profile_id = session.get('active_profile_id')
    
    if profile_id and content_id:
        history = WatchHistory.query.filter_by(
            profile_id=profile_id,
            content_id=content_id
        ).order_by(WatchHistory.watched_at.desc()).first()
        
        if history:
            history.progress = progress
            db.session.commit()
    
    return jsonify({'success': True})

def init_db():
    with app.app_context():
        db.create_all()
        
        # Créer l'admin si n'existe pas
        if not User.query.filter_by(email='admin@stream.com').first():
            admin = User(
                email='admin@stream.com',
                password=generate_password_hash('admin123'),
                name='Administrateur',
                subscription_type='premium',
                is_admin=True,
                subscription_end=datetime.now() + timedelta(days=3650)
            )
            db.session.add(admin)
            db.session.commit()
            
            # Profil admin
            admin_profile = Profile(name='Admin', user_id=admin.id, is_default=True)
            db.session.add(admin_profile)
            db.session.commit()
        
        # Ajouter des contenus de test si la table est vide
        if Content.query.count() == 0:
            test_contents = [
                {
                    'title': 'Le Seigneur des Anneaux',
                    'description': 'Un jeune hobbit doit détruire un anneau magique.',
                    'category': 'Fantasy',
                    'image_url': 'https://picsum.photos/300/450?random=1',
                    'is_premium': True
                },
                {
                    'title': 'Breaking Bad',
                    'description': 'Un professeur de chimie devient trafiquant de drogue.',
                    'category': 'Drame',
                    'image_url': 'https://picsum.photos/300/450?random=2',
                    'is_premium': True
                },
                {
                    'title': 'Friends',
                    'description': 'Les aventures de six amis à New York.',
                    'category': 'Comédie',
                    'image_url': 'https://picsum.photos/300/450?random=3',
                    'is_premium': False
                },
                {
                    'title': 'Inception',
                    'description': 'Un voleur spécialisé dans l\'extraction d\'informations.',
                    'category': 'Science-Fiction',
                    'image_url': 'https://picsum.photos/300/450?random=4',
                    'is_premium': True
                },
                {
                    'title': 'The Office',
                    'description': 'Le quotidien des employés d\'une entreprise de papier.',
                    'category': 'Comédie',
                    'image_url': 'https://picsum.photos/300/450?random=5',
                    'is_premium': False
                },
                {
                    'title': 'Stranger Things',
                    'description': 'Des enfants découvrent des phénomènes surnaturels.',
                    'category': 'Science-Fiction',
                    'image_url': 'https://picsum.photos/300/450?random=6',
                    'is_premium': True
                },
                {
                    'title': 'Game of Thrones',
                    'description': 'Des familles nobles se battent pour le trône.',
                    'category': 'Fantasy',
                    'image_url': 'https://picsum.photos/300/450?random=7',
                    'is_premium': True
                },
                {
                    'title': 'The Crown',
                    'description': 'La vie de la reine Elizabeth II.',
                    'category': 'Drame Historique',
                    'image_url': 'https://picsum.photos/300/450?random=8',
                    'is_premium': False
                },
                {
                    'title': 'Black Mirror',
                    'description': 'Anthologie sur les dérives de la technologie.',
                    'category': 'Science-Fiction',
                    'image_url': 'https://picsum.photos/300/450?random=9',
                    'is_premium': True
                },
                {
                    'title': 'Narcos',
                    'description': 'L\'histoire du cartel de Medellín.',
                    'category': 'Crime',
                    'image_url': 'https://picsum.photos/300/450?random=10',
                    'is_premium': False
                }
            ]
            
            for content_data in test_contents:
                content = Content(**content_data)
                db.session.add(content)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)