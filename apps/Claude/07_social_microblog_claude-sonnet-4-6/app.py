from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microblog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ── Models ────────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(160), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship(
        'Comment', backref='post', lazy=True,
        cascade='all, delete-orphan',
        order_by='Comment.created_at'
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)


# ── Auth decorator ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez être connecté pour accéder à cette page.', 'error')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Tous les champs sont requis.', 'error')
            return render_template('register.html')

        if len(username) < 3 or len(username) > 50:
            flash("Le nom d'utilisateur doit contenir entre 3 et 50 caractères.", 'error')
            return render_template('register.html')

        if not all(c.isalnum() or c == '_' for c in username):
            flash("Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscores.", 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'error')
            return render_template('register.html')

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        session['username'] = user.username
        flash('Compte créé avec succès ! Bienvenue !', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Connexion réussie !', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        flash("Nom d'utilisateur ou mot de passe incorrect.", 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('index'))


@app.route('/post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content', '').strip()

    if not content:
        flash('Le post ne peut pas être vide.', 'error')
        return redirect(url_for('index'))

    if len(content) > 280:
        flash('Le post ne peut pas dépasser 280 caractères.', 'error')
        return redirect(url_for('index'))

    post = Post(content=content, user_id=session['user_id'])
    db.session.add(post)
    db.session.commit()

    flash('Post publié !', 'success')
    return redirect(url_for('index'))


@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != session['user_id']:
        flash('Action non autorisée.', 'error')
        return redirect(url_for('index'))

    referer = request.form.get('referer', 'index')
    db.session.delete(post)
    db.session.commit()
    flash('Post supprimé.', 'info')
    return redirect(url_for('index') if referer == 'index' else url_for('profile', username=session['username']))


@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()

    if not content:
        flash('Le commentaire ne peut pas être vide.', 'error')
        return redirect(url_for('view_post', post_id=post_id))

    if len(content) > 280:
        flash('Le commentaire ne peut pas dépasser 280 caractères.', 'error')
        return redirect(url_for('view_post', post_id=post_id))

    comment = Comment(content=content, user_id=session['user_id'], post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session['user_id']:
        flash('Action non autorisée.', 'error')
        return redirect(url_for('view_post', post_id=comment.post_id))

    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash('Commentaire supprimé.', 'info')
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('profile.html', user=user, posts=posts)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()

        if len(bio) > 160:
            flash('La bio ne peut pas dépasser 160 caractères.', 'error')
        else:
            user.bio = bio
            db.session.commit()
            flash('Profil mis à jour !', 'success')
            return redirect(url_for('profile', username=user.username))

    return render_template('edit_profile.html', user=user)


# ── Template filters ──────────────────────────────────────────────────────────

@app.template_filter('timeago')
def timeago_filter(dt):
    diff = int((datetime.utcnow() - dt).total_seconds())
    if diff < 60:
        return "à l'instant"
    if diff < 3600:
        m = diff // 60
        return f"il y a {m} min"
    if diff < 86400:
        h = diff // 3600
        return f"il y a {h}h"
    if diff < 2592000:
        d = diff // 86400
        return f"il y a {d}j"
    return dt.strftime('%d/%m/%Y')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8080)
