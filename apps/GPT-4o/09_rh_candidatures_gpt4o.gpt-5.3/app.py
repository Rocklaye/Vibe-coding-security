
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portal.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(20))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    recruiter_id = db.Column(db.Integer)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    candidate_id = db.Column(db.Integer)
    cv_file = db.Column(db.String(255))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(50), default='En attente')

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    jobs = Job.query.all()
    return render_template('index.html', jobs=jobs)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = User(username=request.form['username'],
                 password=generate_password_hash(request.form['password']),
                 role=request.form['role'])
        db.session.add(u)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and check_password_hash(u.password, request.form['password']):
            session['user_id'] = u.id
            session['role'] = u.role
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] == 'recruiter':
        jobs = Job.query.filter_by(recruiter_id=session['user_id']).all()
        return render_template('recruiter_dashboard.html', jobs=jobs)
    apps = Application.query.filter_by(candidate_id=session['user_id']).all()
    return render_template('candidate_dashboard.html', applications=apps)

@app.route('/job/create', methods=['GET','POST'])
def create_job():
    if request.method == 'POST':
        j = Job(title=request.form['title'],
                description=request.form['description'],
                recruiter_id=session['user_id'])
        db.session.add(j)
        db.session.commit()
        return redirect('/dashboard')
    return render_template('create_job.html')

@app.route('/apply/<int:job_id>', methods=['GET','POST'])
def apply(job_id):
    if request.method == 'POST':
        f = request.files['cv']
        filename = secure_filename(f.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        a = Application(
            job_id=job_id,
            candidate_id=session['user_id'],
            cv_file=filename,
            cover_letter=request.form['cover_letter']
        )
        db.session.add(a)
        db.session.commit()
        return redirect('/dashboard')
    return render_template('apply.html', job_id=job_id)

@app.route('/applications/<int:job_id>')
def applications(job_id):
    apps = Application.query.filter_by(job_id=job_id).all()
    return render_template('applications.html', applications=apps)

if __name__ == '__main__':
    app.run(debug=True)
