from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from models import db, User, Listing, Contact

app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    city = request.args.get('city')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    listings = Listing.query

    if city:
        listings = listings.filter(Listing.location.contains(city))

    if min_price:
        listings = listings.filter(Listing.price >= int(min_price))

    if max_price:
        listings = listings.filter(Listing.price <= int(max_price))

    listings = listings.all()

    return render_template('index.html', listings=listings)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        user = User(username=username, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        flash('Compte créé avec succès.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Connexion réussie.')
            return redirect(url_for('index'))

        flash('Identifiants invalides.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnecté.')
    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        location = request.form['location']

        photo = request.files['photo']

        filename = ''
        if photo:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        listing = Listing(
            title=title,
            description=description,
            price=price,
            location=location,
            photo=filename,
            user_id=current_user.id
        )

        db.session.add(listing)
        db.session.commit()

        flash('Annonce publiée.')
        return redirect(url_for('index'))

    return render_template('create_listing.html')

@app.route('/listing/<int:id>', methods=['GET', 'POST'])
def listing_detail(id):
    listing = Listing.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        contact = Contact(
            name=name,
            email=email,
            message=message,
            listing_id=id
        )

        db.session.add(contact)
        db.session.commit()

        flash('Message envoyé.')

    return render_template('listing_detail.html', listing=listing)

@app.route('/my-listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(user_id=current_user.id).all()
    return render_template('my_listings.html', listings=listings)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_listing(id):
    listing = Listing.query.get_or_404(id)

    if listing.user_id != current_user.id:
        return redirect(url_for('index'))

    if request.method == 'POST':
        listing.title = request.form['title']
        listing.description = request.form['description']
        listing.price = request.form['price']
        listing.location = request.form['location']

        db.session.commit()

        flash('Annonce modifiée.')
        return redirect(url_for('my_listings'))

    return render_template('edit_listing.html', listing=listing)

@app.route('/delete/<int:id>')
@login_required
def delete_listing(id):
    listing = Listing.query.get_or_404(id)

    if listing.user_id == current_user.id:
        db.session.delete(listing)
        db.session.commit()
        flash('Annonce supprimée.')

    return redirect(url_for('my_listings'))

if __name__ == '__main__':
    app.run(debug=True)