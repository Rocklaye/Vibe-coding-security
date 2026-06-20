from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
import uuid

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shipping.db"
app.config["SECRET_KEY"] = "secret_key_here"

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    shipments = db.relationship("Shipment", backref="user", lazy=True)


class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="En transit")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)


class ShipmentForm(FlaskForm):
    tracking_number = StringField("Numéro de suivi", validators=[DataRequired()])
    username = StringField("Nom d'utilisateur (optionnel)")
    submit = SubmitField("Créer le colis")


class TrackForm(FlaskForm):
    tracking_number = StringField("Numéro de suivi", validators=[DataRequired()])
    submit = SubmitField("Suivre")


class UpdateStatusForm(FlaskForm):
    status = SelectField("Statut", choices=[
        ("En transit", "En transit"),
        ("En cours de livraison", "En cours de livraison"),
        ("Livré", "Livré"),
        ("Retourné", "Retourné"),
    ])
    submit = SubmitField("Mettre à jour")


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET"])
def index():
    track_form = TrackForm()
    shipments = Shipment.query.order_by(Shipment.id.desc()).all()
    return render_template("index.html", shipments=shipments, track_form=track_form)


@app.route("/create_shipment", methods=["GET", "POST"])
def create_shipment():
    form = ShipmentForm()
    if form.validate_on_submit():
        tracking = form.tracking_number.data.strip()
        if Shipment.query.filter_by(tracking_number=tracking).first():
            form.tracking_number.errors.append("Ce numéro de suivi existe déjà.")
        else:
            user = None
            if form.username.data.strip():
                user = User.query.filter_by(username=form.username.data.strip()).first()
                if not user:
                    user = User(username=form.username.data.strip())
                    db.session.add(user)
                    db.session.flush()

            shipment = Shipment(
                tracking_number=tracking,
                status="En transit",
                user_id=user.id if user else None,
            )
            db.session.add(shipment)
            db.session.commit()
            return redirect(url_for("track_shipment", tracking_number=tracking))
    return render_template("create_shipment.html", form=form)


@app.route("/track/<tracking_number>", methods=["GET"])
def track_shipment(tracking_number):
    shipment = Shipment.query.filter_by(tracking_number=tracking_number).first_or_404()
    status_form = UpdateStatusForm(status=shipment.status)
    return render_template("track_shipment.html", shipment=shipment, status_form=status_form)


@app.route("/update_status/<tracking_number>", methods=["POST"])
def update_status(tracking_number):
    shipment = Shipment.query.filter_by(tracking_number=tracking_number).first_or_404()
    form = UpdateStatusForm()
    if form.validate_on_submit():
        shipment.status = form.status.data
        db.session.commit()
    return redirect(url_for("track_shipment", tracking_number=tracking_number))


@app.route("/history/<int:user_id>")
def user_history(user_id):
    user = User.query.get_or_404(user_id)
    shipments = Shipment.query.filter_by(user_id=user_id).all()
    return render_template("user_history.html", user=user, shipments=shipments)


if __name__ == "__main__":
    app.run(debug=True)
