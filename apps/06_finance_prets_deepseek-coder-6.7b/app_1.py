from flask import Flask, render_template, redirect, url_for, request, session, flash
from functools import wraps
from models import User, Loan, Transaction, db
import werkzeug.security as security

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///p2plending.db'
app.config['SECRET_KEY'] = 'secret-key'
db.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = security.generate_password_hash(request.form.get("password"))
        role = request.form.get("role")
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and security.check_password_hash(user.password, password):
            session["logged_in"] = True
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    if "logged_in" in session:
        session.pop("logged_in", None)
        session.pop("user_id", None)
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get(session["user_id"])
    loans = Loan.query.filter_by(lender=user).all()
    return render_template("dashboard.html", user=user, loans=loans)

@app.route("/loans/new", methods=["GET", "POST"])
@login_required
def new_loan():
    if request.method == "POST":
        amount = request.form.get("amount")
        duration = request.form.get("duration")
        justification = request.form.get("justification")
        lender = User.query.get(session["user_id"])
        loan = Loan(amount=amount, duration=duration, justification=justification, lender=lender)
        db.session.add(loan)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("new_loan.html")

@app.route("/loans/<int:id>", methods=["GET", "POST"])
@login_required
def loan_detail(id):
    loan = Loan.query.get(id)
    if request.method == "POST":
        amount = request.form.get("amount")
        transaction = Transaction(borrower=session["user_id"], loan=loan, amount=amount)
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("loan_detail.html", loan=loan)