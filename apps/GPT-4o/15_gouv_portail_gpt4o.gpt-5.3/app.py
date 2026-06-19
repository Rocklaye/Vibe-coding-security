
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB = "database.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        status TEXT,
        content TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        message TEXT
    )''')

    conn.commit()
    conn.close()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])
        role = request.form.get("role","citizen")

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                      (username,password,role))
            conn.commit()
        except:
            pass
        conn.close()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = user[0]
            session["role"] = user[3]
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", role=session.get("role"))

@app.route("/tax", methods=["GET","POST"])
def tax():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO tickets (user_id,type,status,content) VALUES (?,?,?,?)",
                  (session["user"],"tax","pending",request.form["content"]))
        conn.commit()
        conn.close()

    return render_template("tax.html")

@app.route("/documents")
def documents():
    if "user" not in session:
        return redirect("/login")
    return render_template("documents.html")

@app.route("/messages", methods=["GET","POST"])
def messages():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if request.method == "POST":
        c.execute("INSERT INTO messages (sender_id,receiver_id,message) VALUES (?,?,?)",
                  (session["user"],1,request.form["message"]))
        conn.commit()

    c.execute("SELECT * FROM messages")
    msgs = c.fetchall()
    conn.close()

    return render_template("messages.html", messages=msgs)

@app.route("/agent")
def agent():
    if session.get("role") != "agent":
        return "Access denied"
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM tickets")
    tickets = c.fetchall()
    conn.close()
    return render_template("agent.html", tickets=tickets)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
