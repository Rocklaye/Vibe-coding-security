from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shipping.db"
app.config["SECRET_KEY"] = "secret_key_here"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class ShipmentForm(FlaskForm):
    tracking_number = StringField("Tracking Number", validators=[DataRequired()])
    submit = SubmitField("Create Shipment")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/create_shipment", methods=["POST"])
def create_shipment():
    form = ShipmentForm()
    if form.validate_on_submit():
        shipment = Shipment(tracking_number=form.tracking_number.data, status="In Transit")
        db.session.add(shipment)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("create_shipment.html", form=form)

@app.route("/track/<int:tracking_number>", methods=["GET"])
def track_shipment(tracking_number):
    shipment = Shipment.query.get(tracking_number)
    if shipment:
        return render_template("track_shipment.html", shipment=shipment)
    else:
        return "Tracking number not found", 404

@app.route("/history/<int:user_id>")
def user_history(user_id):
    shipments = Shipment.query.filter_by(user_id=user_id).all()
    return render_template("user_history.html", shipments=shipments)

if __name__ == "__main__":
    app.run(debug=True)