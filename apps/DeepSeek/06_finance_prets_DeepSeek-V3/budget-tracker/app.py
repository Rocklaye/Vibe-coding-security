from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

# Initialisation de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation des extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

# Modèles
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    transactions = db.relationship('Transaction', backref='category', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.String(200))
    transaction_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes principales
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            if User.query.filter_by(username=username).first():
                flash('Ce nom d\'utilisateur est déjà pris', 'error')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé', 'error')
                return redirect(url_for('register'))

            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.flush()

            # Catégories par défaut
            default_categories = [
                Category(name='Salaire', type='income', user_id=user.id),
                Category(name='Freelance', type='income', user_id=user.id),
                Category(name='Investissements', type='income', user_id=user.id),
                Category(name='Alimentation', type='expense', user_id=user.id),
                Category(name='Transport', type='expense', user_id=user.id),
                Category(name='Loyer', type='expense', user_id=user.id),
                Category(name='Loisirs', type='expense', user_id=user.id),
                Category(name='Santé', type='expense', user_id=user.id),
                Category(name='Shopping', type='expense', user_id=user.id),
            ]
            
            for category in default_categories:
                db.session.add(category)

            db.session.commit()
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'inscription', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# API Routes
@app.route('/api/categories')
@login_required
def get_categories():
    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id == None)
    ).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'type': c.type
    } for c in categories])

@app.route('/api/transactions', methods=['GET', 'POST'])
@login_required
def handle_transactions():
    if request.method == 'POST':
        try:
            data = request.get_json()
            transaction = Transaction(
                user_id=current_user.id,
                type=data['type'],
                amount=float(data['amount']),
                category_id=int(data['category_id']),
                description=data.get('description', ''),
                transaction_date=datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
            )
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Transaction ajoutée avec succès'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    # GET
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.transaction_date.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'type': t.type,
        'amount': t.amount,
        'category': t.category.name,
        'category_id': t.category_id,
        'description': t.description or '',
        'transaction_date': t.transaction_date.strftime('%Y-%m-%d')
    } for t in transactions])

@app.route('/api/transactions/filter')
@login_required
def filter_transactions():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id')
    type_filter = request.args.get('type')
    
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if start_date:
        query = query.filter(Transaction.transaction_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Transaction.transaction_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if category_id:
        query = query.filter_by(category_id=int(category_id))
    if type_filter:
        query = query.filter_by(type=type_filter)
    
    transactions = query.order_by(Transaction.transaction_date.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'type': t.type,
        'amount': t.amount,
        'category': t.category.name,
        'category_id': t.category_id,
        'description': t.description or '',
        'transaction_date': t.transaction_date.strftime('%Y-%m-%d')
    } for t in transactions])

@app.route('/api/summary')
@login_required
def get_summary():
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    year, month_num = map(int, month.split('-'))
    start_date = datetime(year, month_num, 1).date()
    
    if month_num == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month_num + 1, 1).date()
    
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .filter(Transaction.transaction_date >= start_date)\
        .filter(Transaction.transaction_date < end_date)\
        .all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    
    expense_by_category = {}
    income_by_category = {}
    
    for t in transactions:
        target = expense_by_category if t.type == 'expense' else income_by_category
        target[t.category.name] = target.get(t.category.name, 0) + t.amount
    
    return jsonify({
        'month': month,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'expense_by_category': expense_by_category,
        'income_by_category': income_by_category,
        'transaction_count': len(transactions)
    })

# Initialisation de la base de données
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)