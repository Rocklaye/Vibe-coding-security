import io
import base64
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib
matplotlib.use("Agg")
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


with app.app_context():
    db.create_all()


@app.route("/")
def index():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template("index.html", transactions=transactions)


@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
    transaction = Transaction(
        date=date,
        category=request.form["category"],
        amount=float(request.form["amount"]),
        description=request.form["description"],
    )
    db.session.add(transaction)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete_transaction/<int:id>")
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/graph")
def graph():
    transactions = Transaction.query.all()
    if not transactions:
        return render_template("graph.html", plot_url=None)

    df = pd.DataFrame([{"category": t.category, "amount": t.amount} for t in transactions])
    grouped = df.groupby("category")["amount"].sum()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(grouped.index, grouped.values, color="steelblue")
    ax.set_xlabel("Catégorie")
    ax.set_ylabel("Montant (€)")
    ax.set_title("Budget par catégorie")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plot_url = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)

    return render_template("graph.html", plot_url=plot_url)


@app.route("/historique")
def historique():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template("historique.html", transactions=transactions)


if __name__ == "__main__":
    app.run(debug=True)
