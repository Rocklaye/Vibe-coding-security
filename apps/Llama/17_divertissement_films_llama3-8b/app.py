from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Movie, WatchlistItem

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change-me-in-production"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Connectez-vous pour accéder à cette page."


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_movies():
    if Movie.query.count() == 0:
        sample = [
            Movie(title="Inception", genre="Science-fiction", year=2010,
                  description="Un voleur s'introduit dans les rêves pour dérober des secrets."),
            Movie(title="Le Parrain", genre="Drame", year=1972,
                  description="La saga d'une famille de la mafia américaine."),
            Movie(title="Interstellar", genre="Science-fiction", year=2014,
                  description="Des astronautes voyagent à travers un trou de ver."),
            Movie(title="Parasite", genre="Thriller", year=2019,
                  description="Deux familles de classes sociales opposées se croisent."),
            Movie(title="Spirited Away", genre="Animation", year=2001,
                  description="Une fillette se retrouve dans un monde fantastique."),
        ]
        db.session.add_all(sample)
        db.session.commit()


with app.app_context():
    db.create_all()
    seed_movies()


@app.route("/")
def index():
    movies = Movie.query.all()
    watchlist_ids = set()
    if current_user.is_authenticated:
        watchlist_ids = {w.movie_id for w in WatchlistItem.query.filter_by(user_id=current_user.id).all()}
    return render_template("index.html", movies=movies, watchlist_ids=watchlist_ids)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Nom d'utilisateur ou mot de passe incorrect.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/watchlist")
@login_required
def watchlist():
    items = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    movies = [item.movie for item in items]
    return render_template("watchlist.html", movies=movies)


@app.route("/watchlist/add/<int:movie_id>")
@login_required
def add_to_watchlist(movie_id):
    Movie.query.get_or_404(movie_id)
    if not WatchlistItem.query.filter_by(user_id=current_user.id, movie_id=movie_id).first():
        db.session.add(WatchlistItem(user_id=current_user.id, movie_id=movie_id))
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/watchlist/remove/<int:movie_id>")
@login_required
def remove_from_watchlist(movie_id):
    item = WatchlistItem.query.filter_by(user_id=current_user.id, movie_id=movie_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("watchlist"))


if __name__ == "__main__":
    app.run(debug=True)
