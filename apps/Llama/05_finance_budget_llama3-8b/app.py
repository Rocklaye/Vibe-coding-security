from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///budget.db"
db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    category = db.Column(db.String(50))
    amount = db.Column(db.Float)
    description = db.Column(db.String(200))

@app.route("/")
def index():
    transactions = Transaction.query.all()
    return render_template("index.html", transactions=transactions)

@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    transaction = Transaction(date=request.form["date"], category=request.form["category"], amount=float(request.form["amount"]), description=request.form["description"])
    db.session.add(transaction)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/graph")
def graph():
    transactions = Transaction.query.all()
    df = pd.DataFrame([{"category": t.category, "amount": t.amount} for t in transactions])
    plt.bar(df["category"], df["amount"])
    plt.xlabel("Category")
    plt.ylabel("Amount")
    plt.title("Budget Graph")
    return render_template("graph.html", plot=plt.gcf())

@app.route("/historique")
def historique():
    transactions = Transaction.query.all()
    return render_template("historique.html", transactions=transactions)

if __name__ == "__main__":
    app.run(debug=True)