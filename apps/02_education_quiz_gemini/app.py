from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'cle_secrete_super_securisee'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modèles de base de données ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'teacher' ou 'student'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    results = db.relationship('Result', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    opt_a = db.Column(db.String(200), nullable=False)
    opt_b = db.Column(db.String(200), nullable=False)
    opt_c = db.Column(db.String(200), nullable=False)
    opt_d = db.Column(db.String(200), nullable=False)
    correct_opt = db.Column(db.String(1), nullable=False) # 'A', 'B', 'C', ou 'D'

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)

    student = db.relationship('User', backref='results')

# --- Routes de l'application ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, role=role)
            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if session['role'] == 'teacher':
        quizzes = Quiz.query.filter_by(teacher_id=session['user_id']).all()
        # Récupérer tous les résultats pour les quiz de cet enseignant
        quiz_ids = [q.id for q in quizzes]
        results = Result.query.filter(Result.quiz_id.in_(quiz_ids)).all() if quiz_ids else []
        return render_template('teacher_dashboard.html', quizzes=quizzes, results=results)
    else:
        # Étudiant
        quizzes = Quiz.query.all()
        my_results = Result.query.filter_by(student_id=session['user_id']).all()
        taken_quiz_ids = [r.quiz_id for r in my_results]
        return render_template('student_dashboard.html', quizzes=quizzes, results=my_results, taken_quiz_ids=taken_quiz_ids)

@app.route('/teacher/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        title = request.form['title']
        questions = request.form.getlist('question[]')
        opts_a = request.form.getlist('optA[]')
        opts_b = request.form.getlist('optB[]')
        opts_c = request.form.getlist('optC[]')
        opts_d = request.form.getlist('optD[]')
        corrects = request.form.getlist('correct[]')
        
        new_quiz = Quiz(title=title, teacher_id=session['user_id'])
        db.session.add(new_quiz)
        db.session.commit()
        
        for i in range(len(questions)):
            q = Question(
                quiz_id=new_quiz.id,
                text=questions[i],
                opt_a=opts_a[i],
                opt_b=opts_b[i],
                opt_c=opts_c[i],
                opt_d=opts_d[i],
                correct_opt=corrects[i]
            )
            db.session.add(q)
        db.session.commit()
        flash('Quiz créé avec succès!', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('create_quiz.html')

@app.route('/student/take_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('index'))
        
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Vérifier si l'étudiant a déjà fait ce quiz
    existing_result = Result.query.filter_by(student_id=session['user_id'], quiz_id=quiz_id).first()
    if existing_result:
        flash('Vous avez déjà complété ce quiz.', 'warning')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        score = 0
        total = len(quiz.questions)
        
        for q in quiz.questions:
            student_answer = request.form.get(f'q_{q.id}')
            if student_answer == q.correct_opt:
                score += 1
                
        new_result = Result(student_id=session['user_id'], quiz_id=quiz.id, score=score, total=total)
        db.session.add(new_result)
        db.session.commit()
        
        return render_template('quiz_result.html', score=score, total=total, quiz=quiz)
        
    return render_template('take_quiz.html', quiz=quiz)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)