"""
HR Manager - Application de Gestion des Ressources Humaines
Flask + SQLite
"""

import os
import calendar
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from models import db, Employee, Department, Position, Leave, Evaluation, Payroll, User, LeaveBalance, Skill
from auth import login_required, role_required, get_current_user, log_action

# Configuration de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hr-manager-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///hr_manager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser la base de données
db.init_app(app)

# ============================================================
# CRÉATION DES TABLES ET DONNÉES DE TEST
# ============================================================

def create_tables():
    with app.app_context():
        db.create_all()

def seed_data():
    """Crée des données de démonstration"""
    with app.app_context():
        # Vérifier si des données existent déjà
        if Department.query.first():
            return
        
        # Départements
        departments = [
            Department(name='Direction Générale', code='DG', description='Direction stratégique de l\'entreprise'),
            Department(name='Ressources Humaines', code='RH', description='Gestion du personnel et recrutement'),
            Department(name='Informatique', code='IT', description='Développement et infrastructure IT'),
            Department(name='Marketing', code='MKT', description='Marketing et communication'),
            Department(name='Ventes', code='SALES', description='Commerce et relations clients'),
            Department(name='Finance', code='FIN', description='Comptabilité et finance'),
            Department(name='Production', code='PROD', description='Fabrication et logistique'),
            Department(name='Recherche & Développement', code='R&D', description='Innovation et développement produit'),
        ]
        for dept in departments:
            db.session.add(dept)
        db.session.commit()
        
        # Postes
        positions = [
            Position(title='Directeur Général', level='C-Level', department_id=1, base_salary_min=80000, base_salary_max=150000),
            Position(title='DRH', level='Director', department_id=2, base_salary_min=55000, base_salary_max=85000),
            Position(title='Responsable Recrutement', level='Manager', department_id=2, base_salary_min=40000, base_salary_max=60000),
            Position(title='Développeur Senior', level='Senior', department_id=3, base_salary_min=45000, base_salary_max=65000),
            Position(title='Développeur Junior', level='Junior', department_id=3, base_salary_min=32000, base_salary_max=42000),
            Position(title='Lead Developer', level='Lead', department_id=3, base_salary_min=55000, base_salary_max=75000),
            Position(title='Chef de Projet Marketing', level='Manager', department_id=4, base_salary_min=42000, base_salary_max=62000),
            Position(title='Responsable Commercial', level='Director', department_id=5, base_salary_min=55000, base_salary_max=85000),
            Position(title='Commercial', level='Junior', department_id=5, base_salary_min=30000, base_salary_max=45000),
            Position(title='Comptable', level='Senior', department_id=6, base_salary_min=38000, base_salary_max=52000),
            Position(title='Responsable Production', level='Manager', department_id=7, base_salary_min=45000, base_salary_max=65000),
            Position(title='Ingénieur R&D', level='Senior', department_id=8, base_salary_min=48000, base_salary_max=70000),
        ]
        for pos in positions:
            db.session.add(pos)
        db.session.commit()
        
        # Employés (direction)
        ceo = Employee(
            employee_id='EMP001',
            first_name='Marie',
            last_name='Dubois',
            email='marie.dubois@entreprise.fr',
            phone='06 12 34 56 78',
            date_of_birth=date(1975, 3, 15),
            hire_date=date(2018, 1, 15),
            status='active',
            address='15 Rue de la Paix',
            city='Paris',
            postal_code='75002',
            department_id=1,
            position_id=1,
            base_salary=120000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(ceo)
        db.session.commit()
        
        # Mettre à jour le manager du DG
        ceo.manager_id = ceo.id  # Auto-référence pour le DG
        
        # DRH
        hr_director = Employee(
            employee_id='EMP002',
            first_name='Jean',
            last_name='Martin',
            email='jean.martin@entreprise.fr',
            phone='06 23 45 67 89',
            date_of_birth=date(1980, 7, 22),
            hire_date=date(2019, 3, 1),
            status='active',
            address='28 Avenue Victor Hugo',
            city='Paris',
            postal_code='75016',
            department_id=2,
            position_id=2,
            manager_id=ceo.id,
            base_salary=68000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(hr_director)
        db.session.commit()
        
        # Responsable Recrutement
        recruiter = Employee(
            employee_id='EMP003',
            first_name='Sophie',
            last_name='Bernard',
            email='sophie.bernard@entreprise.fr',
            phone='06 34 56 78 90',
            date_of_birth=date(1988, 11, 5),
            hire_date=date(2020, 6, 15),
            status='active',
            address='45 Rue du Commerce',
            city='Paris',
            postal_code='75015',
            department_id=2,
            position_id=3,
            manager_id=hr_director.id,
            base_salary=48000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(recruiter)
        
        # Lead Developer
        lead_dev = Employee(
            employee_id='EMP004',
            first_name='Thomas',
            last_name='Petit',
            email='thomas.petit@entreprise.fr',
            phone='06 45 67 89 01',
            date_of_birth=date(1985, 1, 30),
            hire_date=date(2019, 9, 1),
            status='active',
            address='12 Rue de Rivoli',
            city='Paris',
            postal_code='75004',
            department_id=3,
            position_id=6,
            manager_id=ceo.id,
            base_salary=62000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(lead_dev)
        
        # Développeur Senior
        dev_senior = Employee(
            employee_id='EMP005',
            first_name='Camille',
            last_name='Moreau',
            email='camille.moreau@entreprise.fr',
            phone='06 56 78 90 12',
            date_of_birth=date(1990, 5, 18),
            hire_date=date(2021, 2, 1),
            status='active',
            address='8 Boulevard Saint-Germain',
            city='Paris',
            postal_code='75005',
            department_id=3,
            position_id=4,
            manager_id=lead_dev.id,
            base_salary=52000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(dev_senior)
        
        # Développeur Junior
        dev_junior = Employee(
            employee_id='EMP006',
            first_name='Lucas',
            last_name='Richard',
            email='lucas.richard@entreprise.fr',
            phone='06 67 89 01 23',
            date_of_birth=date(1995, 9, 12),
            hire_date=date(2023, 6, 1),
            status='active',
            address='22 Rue de la Boétie',
            city='Paris',
            postal_code='75008',
            department_id=3,
            position_id=5,
            manager_id=lead_dev.id,
            base_salary=36000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(dev_junior)
        
        # Chef de Projet Marketing
        marketing_manager = Employee(
            employee_id='EMP007',
            first_name='Emma',
            last_name='Durand',
            email='emma.durand@entreprise.fr',
            phone='06 78 90 12 34',
            date_of_birth=date(1987, 4, 25),
            hire_date=date(2020, 1, 10),
            status='active',
            address='33 Rue de Passy',
            city='Paris',
            postal_code='75016',
            department_id=4,
            position_id=7,
            manager_id=ceo.id,
            base_salary=54000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(marketing_manager)
        
        # Responsable Commercial
        sales_director = Employee(
            employee_id='EMP008',
            first_name='Nicolas',
            last_name='Leroy',
            email='nicolas.leroy@entreprise.fr',
            phone='06 89 01 23 45',
            date_of_birth=date(1982, 8, 8),
            hire_date=date(2019, 5, 20),
            status='active',
            address='5 Rue de la Pompe',
            city='Paris',
            postal_code='75016',
            department_id=5,
            position_id=8,
            manager_id=ceo.id,
            base_salary=70000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(sales_director)
        
        # Commercial
        sales_rep = Employee(
            employee_id='EMP009',
            first_name='Julie',
            last_name='Roux',
            email='julie.roux@entreprise.fr',
            phone='06 90 12 34 56',
            date_of_birth=date(1992, 12, 3),
            hire_date=date(2022, 3, 15),
            status='active',
            address='17 Rue de Tocqueville',
            city='Paris',
            postal_code='75017',
            department_id=5,
            position_id=9,
            manager_id=sales_director.id,
            base_salary=38000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(sales_rep)
        
        # Comptable
        accountant = Employee(
            employee_id='EMP010',
            first_name='Philippe',
            last_name='Garcia',
            email='philippe.garcia@entreprise.fr',
            phone='06 01 23 45 67',
            date_of_birth=date(1978, 6, 20),
            hire_date=date(2020, 8, 1),
            status='active',
            address='9 Rue de Courcelles',
            city='Paris',
            postal_code='75008',
            department_id=6,
            position_id=10,
            manager_id=ceo.id,
            base_salary=46000,
            contract_type='CDI',
            work_hours_per_week=35
        )
        db.session.add(accountant)
        db.session.commit()
        
        # Utilisateurs
        users_data = [
            ('admin', 'admin@entreprise.fr', 'admin123', 'admin', ceo.id),
            ('rh', 'rh@entreprise.fr', 'rh123', 'hr', hr_director.id),
            ('manager', 'manager@entreprise.fr', 'manager123', 'manager', lead_dev.id),
            ('employe', 'employe@entreprise.fr', 'employe123', 'employee', dev_senior.id),
        ]
        
        for username, email, password, role, emp_id in users_data:
            user = User(
                username=username,
                email=email,
                role=role,
                employee_id=emp_id,
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
        db.session.commit()
        
        # Solde de congés
        leave_balances = [
            (ceo.id, 'annual', 2024, 25),
            (hr_director.id, 'annual', 2024, 25),
            (recruiter.id, 'annual', 2024, 25),
            (lead_dev.id, 'annual', 2024, 25),
            (dev_senior.id, 'annual', 2024, 25),
            (dev_junior.id, 'annual', 2024, 25),
            (marketing_manager.id, 'annual', 2024, 25),
            (sales_director.id, 'annual', 2024, 25),
            (sales_rep.id, 'annual', 2024, 25),
            (accountant.id, 'annual', 2024, 25),
        ]
        for emp_id, ltype, year, total in leave_balances:
            lb = LeaveBalance(
                employee_id=emp_id,
                leave_type=ltype,
                year=year,
                total_days=total,
                used_days=0,
                remaining_days=total
            )
            db.session.add(lb)
        db.session.commit()
        
        # Quelques demandes de congés
        leaves = [
            Leave(employee_id=dev_senior.id, leave_type='annual', start_date=date(2024, 7, 15), end_date=date(2024, 7, 30), days_requested=12, reason='Vacances d\'été en famille', status='approved', approved_by=lead_dev.id, approved_at=datetime(2024, 6, 1)),
            Leave(employee_id=dev_junior.id, leave_type='annual', start_date=date(2024, 8, 5), end_date=date(2024, 8, 12), days_requested=5, reason='Voyage', status='pending'),
            Leave(employee_id=recruiter.id, leave_type='sick', start_date=date(2024, 6, 10), end_date=date(2024, 6, 12), days_requested=2, reason='Maladie', status='approved', approved_by=hr_director.id, approved_at=datetime(2024, 6, 10)),
            Leave(employee_id=sales_rep.id, leave_type='annual', start_date=date(2024, 9, 1), end_date=date(2024, 9, 10), days_requested=7, reason='Congés', status='pending'),
        ]
        for leave in leaves:
            db.session.add(leave)
        db.session.commit()
        
        # Mise à jour des solde
        for leave in leaves:
            if leave.status == 'approved':
                lb = LeaveBalance.query.filter_by(employee_id=leave.employee_id, leave_type=leave.leave_type, year=2024).first()
                if lb:
                    lb.used_days += leave.days_requested
                    lb.remaining_days -= leave.days_requested
        db.session.commit()
        
        # Évaluations
        evaluations = [
            Evaluation(
                employee_id=dev_senior.id,
                evaluator_id=lead_dev.id,
                evaluation_year=2023,
                period_start=date(2023, 1, 1),
                period_end=date(2023, 12, 31),
                goals='Améliorer les performances des applications;Mentorat des juniors;Certification AWS',
                goals_achievement=85,
                technical_skills=4.5,
                communication=4.0,
                teamwork=4.5,
                leadership=3.5,
                initiative=4.0,
                punctuality=5.0,
                strengths='Excellente maîtrise technique, bonne collaboration',
                areas_for_improvement='Leadership à développer',
                overall_rating=4.2,
                status='approved'
            ),
            Evaluation(
                employee_id=lead_dev.id,
                evaluator_id=ceo.id,
                evaluation_year=2023,
                period_start=date(2023, 1, 1),
                period_end=date(2023, 12, 31),
                goals='Livraison projet Alpha;Formation équipe;Architecture microservices',
                goals_achievement=90,
                technical_skills=5.0,
                communication=4.5,
                teamwork=4.5,
                leadership=4.5,
                initiative=4.5,
                punctuality=5.0,
                strengths='Leadership naturel, vision technique',
                areas_for_improvement='Communication ascendante',
                overall_rating=4.7,
                status='approved'
            ),
        ]
        for ev in evaluations:
            db.session.add(ev)
        db.session.commit()
        
        # Fiches de paie
        payrolls = []
        for month in range(1, 7):  # Janvier à Juin 2024
            for emp in Employee.query.filter(Employee.status == 'active').all():
                base = emp.base_salary / 12
                gross = base * 1.1  # +10% charges patronales approx
                deductions = base * 0.22  # ~22% de charges salariales
                net = gross - deductions
                
                payroll = Payroll(
                    employee_id=emp.id,
                    period_month=month,
                    period_year=2024,
                    base_salary=round(base, 2),
                    overtime_hours=0,
                    overtime_amount=0,
                    bonus=round(base * 0.05, 2) if month == 12 else 0,
                    commission=0,
                    meal_vouchers=round(8.5 * 22, 2),
                    transport_allowance=round(emp.base_salary * 0.005, 2),
                    other_allowances=0,
                    social_security=round(base * 0.065, 2),
                    unemployment_insurance=round(base * 0.024, 2),
                    retirement_contribution=round(base * 0.071, 2),
                    income_tax=round(base * 0.12, 2),
                    other_deductions=0,
                    gross_salary=round(gross, 2),
                    total_deductions=round(deductions, 2),
                    net_salary=round(net, 2),
                    payment_date=date(2024, month, 28),
                    status='paid'
                )
                payrolls.append(payroll)
        
        for p in payrolls:
            db.session.add(p)
        db.session.commit()
        
        print("Données de démonstration créées avec succès!")
        print("Comptes de test:")
        print("  - admin / admin123 (rôle: admin)")
        print("  - rh / rh123 (rôle: RH)")
        print("  - manager / manager123 (rôle: manager)")
        print("  - employe / employe123 (rôle: employé)")


# ============================================================
# ROUTES - PAGES
# ============================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Connexion réussie!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants invalides', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    return render_template('dashboard.html', user=user)

@app.route('/employees')
@login_required
def employees():
    user = get_current_user()
    return render_template('employees.html', user=user)

@app.route('/employees/<int:id>')
@login_required
def employee_detail(id):
    user = get_current_user()
    employee = Employee.query.get_or_404(id)
    return render_template('employee_detail.html', user=user, employee=employee)

@app.route('/leaves')
@login_required
def leaves():
    user = get_current_user()
    return render_template('leaves.html', user=user)

@app.route('/evaluations')
@login_required
def evaluations():
    user = get_current_user()
    return render_template('evaluations.html', user=user)

@app.route('/payroll')
@login_required
def payroll():
    user = get_current_user()
    return render_template('payroll.html', user=user)

@app.route('/org-chart')
@login_required
def org_chart():
    user = get_current_user()
    return render_template('org_chart.html', user=user)

@app.route('/settings')
@login_required
def settings():
    user = get_current_user()
    return render_template('settings.html', user=user)


# ============================================================
# API - TABLEAU DE BORD / STATISTIQUES
# ============================================================

@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Statistiques pour le tableau de bord"""
    total_employees = Employee.query.filter(Employee.status == 'active').count()
    total_departments = Department.query.count()
    
    # Congés en attente
    pending_leaves = Leave.query.filter_by(status='pending').count()
    
    # Nouveaux employés ce mois
    today = date.today()
    first_day_month = today.replace(day=1)
    new_employees = Employee.query.filter(Employee.hire_date >= first_day_month).count()
    
    # Masss salariale mensuelle
    payroll_sum = db.session.query(db.func.sum(Payroll.net_salary)).filter(
        Payroll.period_month == today.month,
        Payroll.period_year == today.year
    ).scalar() or 0
    
    # Taux de turnover (approximatif)
    terminated_this_year = Employee.query.filter(
        Employee.termination_date >= date(today.year, 1, 1)
    ).count()
    turnover_rate = round((terminated_this_year / total_employees * 100), 1) if total_employees > 0 else 0
    
    # Distribution par département
    dept_distribution = []
    for dept in Department.query.all():
        count = Employee.query.filter_by(department_id=dept.id, status='active').count()
        dept_distribution.append({'name': dept.name, 'count': count})
    
    # Congés récents
    recent_leaves = Leave.query.order_by(Leave.requested_at.desc()).limit(5).all()
    
    # Activité récente (journal d'audit)
    from models import AuditLog
    recent_activity = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return jsonify({
        'total_employees': total_employees,
        'total_departments': total_departments,
        'pending_leaves': pending_leaves,
        'new_employees': new_employees,
        'payroll_total': round(payroll_sum, 2),
        'turnover_rate': turnover_rate,
        'dept_distribution': dept_distribution,
        'recent_leaves': [l.to_dict() for l in recent_leaves],
        'recent_activity': [a.to_dict() for a in recent_activity]
    })


# ============================================================
# API - EMPLOYÉS
# ============================================================

@app.route('/api/employees', methods=['GET'])
@login_required
def api_employees_list():
    """Liste des employés avec filtres"""
    query = Employee.query
    
    # Filtres
    department = request.args.get('department')
    status = request.args.get('status', 'active')
    search = request.args.get('search')
    
    if department:
        query = query.filter_by(department_id=department)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(f'%{search}%'),
                Employee.last_name.ilike(f'%{search}%'),
                Employee.email.ilike(f'%{search}%'),
                Employee.employee_id.ilike(f'%{search}%')
            )
        )
    
    employees = query.order_by(Employee.last_name).all()
    return jsonify([e.to_dict() for e in employees])

@app.route('/api/employees/<int:id>', methods=['GET'])
@login_required
def api_employee_get(id):
    """Détail d'un employé"""
    employee = Employee.query.get_or_404(id)
    data = employee.to_dict()
    
    # Ajouter les congés récents
    data['recent_leaves'] = [l.to_dict() for l in employee.leaves.order_by(Leave.start_date.desc()).limit(5)]
    
    # Ajouter les évaluations
    data['evaluations'] = [e.to_dict() for e in employee.evaluations.order_by(Evaluation.evaluation_year.desc())]
    
    # Ajouter les fiches de paie récentes
    data['recent_payrolls'] = [p.to_dict() for p in employee.payroll_records.order_by(Payroll.period_year.desc(), Payroll.period_month.desc()).limit(6)]
    
    # Solde de congés
    data['leave_balances'] = [lb.to_dict() for lb in LeaveBalance.query.filter_by(employee_id=id).all()]
    
    return jsonify(data)

@app.route('/api/employees', methods=['POST'])
@login_required
@role_required('hr')
def api_employee_create():
    """Créer un employé"""
    data = request.get_json()
    
    # Générer un matricule
    last_emp = Employee.query.order_by(Employee.id.desc()).first()
    new_id = f"EMP{last_emp.id + 1:03d}" if last_emp else "EMP001"
    
    employee = Employee(
        employee_id=data.get('employee_id', new_id),
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data.get('phone'),
        date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
        hire_date=datetime.strptime(data['hire_date'], '%Y-%m-%d').date(),
        status=data.get('status', 'active'),
        address=data.get('address'),
        city=data.get('city'),
        postal_code=data.get('postal_code'),
        department_id=data.get('department_id'),
        position_id=data.get('position_id'),
        manager_id=data.get('manager_id'),
        base_salary=data.get('base_salary'),
        contract_type=data.get('contract_type', 'CDI'),
        work_hours_per_week=data.get('work_hours_per_week', 35)
    )
    
    db.session.add(employee)
    db.session.commit()
    
    # Créer le solde de congés
    current_year = date.today().year
    lb = LeaveBalance(
        employee_id=employee.id,
        leave_type='annual',
        year=current_year,
        total_days=25,
        used_days=0,
        remaining_days=25
    )
    db.session.add(lb)
    db.session.commit()
    
    log_action('employee', employee.id, 'create', f"Création employé: {employee.full_name()}")
    
    return jsonify(employee.to_dict()), 201

@app.route('/api/employees/<int:id>', methods=['PUT'])
@login_required
@role_required('hr')
def api_employee_update(id):
    """Modifier un employé"""
    employee = Employee.query.get_or_404(id)
    data = request.get_json()
    
    fields = ['first_name', 'last_name', 'email', 'phone', 'status',
              'address', 'city', 'postal_code', 'department_id', 'position_id',
              'manager_id', 'base_salary', 'contract_type', 'work_hours_per_week']
    
    for field in fields:
        if field in data:
            setattr(employee, field, data[field])
    
    if 'date_of_birth' in data and data['date_of_birth']:
        employee.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    
    if 'hire_date' in data and data['hire_date']:
        employee.hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
    
    if 'termination_date' in data and data['termination_date']:
        employee.termination_date = datetime.strptime(data['termination_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    log_action('employee', id, 'update', f"Modification employé: {employee.full_name()}")
    
    return jsonify(employee.to_dict())

@app.route('/api/employees/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin')
def api_employee_delete(id):
    """Supprimer un employé"""
    employee = Employee.query.get_or_404(id)
    
    # Supprimer le compte utilisateur associé
    user = User.query.filter_by(employee_id=id).first()
    if user:
        db.session.delete(user)
    
    db.session.delete(employee)
    db.session.commit()
    
    log_action('employee', id, 'delete', f"Suppression employé: {employee.full_name()}")
    
    return jsonify({'message': 'Employé supprimé'})


# ============================================================
# API - DÉPARTEMENTS ET POSTES
# ============================================================

@app.route('/api/departments', methods=['GET'])
@login_required
def api_departments_list():
    """Liste des départements"""
    departments = Department.query.all()
    return jsonify([d.to_dict() for d in departments])

@app.route('/api/positions', methods=['GET'])
@login_required
def api_positions_list():
    """Liste des postes"""
    positions = Position.query.all()
    return jsonify([p.to_dict() for p in positions])


# ============================================================
# API - CONGÉS
# ============================================================

@app.route('/api/leaves', methods=['GET'])
@login_required
def api_leaves_list():
    """Liste des demandes de congés"""
    user = get_current_user()
    query = Leave.query
    
    # Filtrer selon le rôle
    if user.role == 'employee':
        query = query.filter_by(employee_id=user.employee_id)
    elif user.role == 'manager':
        # Voir ses propres congés + ceux de son équipe
        team_ids = [e.id for e in Employee.query.filter_by(manager_id=user.employee_id).all()]
        query = query.filter(Leave.employee_id.in_([user.employee_id] + team_ids))
    
    # Filtres optionnels
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    leaves = query.order_by(Leave.requested_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves])

@app.route('/api/leaves', methods=['POST'])
@login_required
def api_leave_create():
    """Créer une demande de congé"""
    user = get_current_user()
    data = request.get_json()
    
    employee_id = data.get('employee_id', user.employee_id)
    
    # Vérifier les droits
    if user.role == 'employee' and employee_id != user.employee_id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    days_requested = (end_date - start_date).days + 1
    
    # Vérifier le solde
    year = start_date.year
    lb = LeaveBalance.query.filter_by(employee_id=employee_id, leave_type=data['leave_type'], year=year).first()
    if lb and lb.remaining_days < days_requested:
        return jsonify({'error': f'Solde insuffisant. Restant: {lb.remaining_days} jours'}), 400
    
    leave = Leave(
        employee_id=employee_id,
        leave_type=data['leave_type'],
        start_date=start_date,
        end_date=end_date,
        days_requested=days_requested,
        reason=data.get('reason', ''),
        status='pending'
    )
    
    db.session.add(leave)
    db.session.commit()
    
    log_action('leave', leave.id, 'create', f"Demande de congé: {leave.days_requested} jours")
    
    return jsonify(leave.to_dict()), 201

@app.route('/api/leaves/<int:id>/approve', methods=['POST'])
@login_required
@role_required('manager')
def api_leave_approve(id):
    """Approuver une demande de congé"""
    leave = Leave.query.get_or_404(id)
    user = get_current_user()
    
    # Vérifier que l'approbateur est le manager de l'employé
    employee = Employee.query.get(leave.employee_id)
    if user.role == 'manager' and employee.manager_id != user.employee_id:
        return jsonify({'error': 'Vous n\'êtes pas le manager de cet employé'}), 403
    
    leave.status = 'approved'
    leave.approved_by = user.employee_id
    leave.approved_at = datetime.utcnow()
    
    # Mettre à jour le solde
    year = leave.start_date.year
    lb = LeaveBalance.query.filter_by(employee_id=leave.employee_id, leave_type=leave.leave_type, year=year).first()
    if lb:
        lb.used_days += leave.days_requested
        lb.remaining_days -= leave.days_requested
    
    db.session.commit()
    log_action('leave', id, 'approve', f"Congé approuvé: {leave.days_requested} jours")
    
    return jsonify(leave.to_dict())

@app.route('/api/leaves/<int:id>/reject', methods=['POST'])
@login_required
@role_required('manager')
def api_leave_reject(id):
    """Rejeter une demande de congé"""
    leave = Leave.query.get_or_404(id)
    user = get_current_user()
    data = request.get_json()
    
    employee = Employee.query.get(leave.employee_id)
    if user.role == 'manager' and employee.manager_id != user.employee_id:
        return jsonify({'error': 'Vous n\'êtes pas le manager de cet employé'}), 403
    
    leave.status = 'rejected'
    leave.rejection_reason = data.get('reason', '')
    
    db.session.commit()
    log_action('leave', id, 'reject', f"Congé rejeté: {data.get('reason', '')}")
    
    return jsonify(leave.to_dict())

@app.route('/api/leaves/balance')
@login_required
def api_leave_balance():
    """Solde de congés de l'employé connecté"""
    user = get_current_user()
    year = request.args.get('year', date.today().year, type=int)
    
    balances = LeaveBalance.query.filter_by(employee_id=user.employee_id, year=year).all()
    return jsonify([b.to_dict() for b in balances])


# ============================================================
# API - ÉVALUATIONS
# ============================================================

@app.route('/api/evaluations', methods=['GET'])
@login_required
def api_evaluations_list():
    """Liste des évaluations"""
    user = get_current_user()
    query = Evaluation.query
    
    if user.role == 'employee':
        query = query.filter_by(employee_id=user.employee_id)
    elif user.role == 'manager':
        team_ids = [e.id for e in Employee.query.filter_by(manager_id=user.employee_id).all()]
        query = query.filter(db.or_(
            Evaluation.employee_id == user.employee_id,
            Evaluation.employee_id.in_(team_ids)
        ))
    
    evaluations = query.order_by(Evaluation.evaluation_year.desc()).all()
    return jsonify([e.to_dict() for e in evaluations])

@app.route('/api/evaluations', methods=['POST'])
@login_required
@role_required('manager')
def api_evaluation_create():
    """Créer une évaluation"""
    data = request.get_json()
    user = get_current_user()
    
    evaluation = Evaluation(
        employee_id=data['employee_id'],
        evaluator_id=user.employee_id,
        evaluation_year=data['evaluation_year'],
        period_start=datetime.strptime(data['period_start'], '%Y-%m-%d').date() if data.get('period_start') else None,
        period_end=datetime.strptime(data['period_end'], '%Y-%m-%d').date() if data.get('period_end') else None,
        goals=data.get('goals', ''),
        status='draft'
    )
    
    db.session.add(evaluation)
    db.session.commit()
    
    log_action('evaluation', evaluation.id, 'create', f"Évaluation créée pour {data['employee_id']}")
    
    return jsonify(evaluation.to_dict()), 201

@app.route('/api/evaluations/<int:id>', methods=['PUT'])
@login_required
@role_required('manager')
def api_evaluation_update(id):
    """Mettre à jour une évaluation"""
    evaluation = Evaluation.query.get_or_404(id)
    data = request.get_json()
    
    fields = ['goals', 'goals_achievement', 'technical_skills', 'communication',
              'teamwork', 'leadership', 'initiative', 'punctuality',
              'strengths', 'areas_for_improvement', 'employee_comments',
              'evaluator_comments', 'status']
    
    for field in fields:
        if field in data:
            setattr(evaluation, field, data[field])
    
    # Calculer la note globale
    ratings = [evaluation.technical_skills, evaluation.communication,
               evaluation.teamwork, evaluation.leadership,
               evaluation.initiative, evaluation.punctuality]
    valid_ratings = [r for r in ratings if r is not None]
    if valid_ratings:
        evaluation.overall_rating = round(sum(valid_ratings) / len(valid_ratings), 2)
    
    db.session.commit()
    log_action('evaluation', id, 'update', f"Évaluation mise à jour")
    
    return jsonify(evaluation.to_dict())


# ============================================================
# API - PAIE
# ============================================================

@app.route('/api/payroll', methods=['GET'])
@login_required
def api_payroll_list():
    """Liste des fiches de paie"""
    user = get_current_user()
    query = Payroll.query
    
    if user.role == 'employee':
        query = query.filter_by(employee_id=user.employee_id)
    
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    if month:
        query = query.filter_by(period_month=month)
    if year:
        query = query.filter_by(period_year=year)
    
    payrolls = query.order_by(Payroll.period_year.desc(), Payroll.period_month.desc()).all()
    return jsonify([p.to_dict() for p in payrolls])

@app.route('/api/payroll', methods=['POST'])
@login_required
@role_required('hr')
def api_payroll_create():
    """Créer une fiche de paie"""
    data = request.get_json()
    user = get_current_user()
    
    employee = Employee.query.get_or_404(data['employee_id'])
    base = employee.base_salary / 12 if employee.base_salary else 0
    
    # Calcul automatique
    overtime_amount = data.get('overtime_amount', 0)
    bonus = data.get('bonus', 0)
    allowances = data.get('meal_vouchers', 0) + data.get('transport_allowance', 0) + data.get('other_allowances', 0)
    gross = base + overtime_amount + bonus + allowances
    
    # Charges (taux simplifiés France)
    ss = round(base * 0.065, 2)  # Sécurité sociale
    chomage = round(base * 0.024, 2)  # Assurance chômage
    retraite = round(base * 0.071, 2)  # Retraite
    ir = round(gross * 0.12, 2)  # Impôt sur le revenu (simplifié)
    deductions = ss + chomage + retraite + ir + data.get('other_deductions', 0)
    
    payroll = Payroll(
        employee_id=data['employee_id'],
        period_month=data['period_month'],
        period_year=data['period_year'],
        base_salary=round(base, 2),
        overtime_hours=data.get('overtime_hours', 0),
        overtime_amount=overtime_amount,
        bonus=bonus,
        commission=data.get('commission', 0),
        meal_vouchers=data.get('meal_vouchers', 0),
        transport_allowance=data.get('transport_allowance', 0),
        other_allowances=data.get('other_allowances', 0),
        social_security=ss,
        unemployment_insurance=chomage,
        retirement_contribution=retraite,
        income_tax=ir,
        other_deductions=data.get('other_deductions', 0),
        gross_salary=round(gross, 2),
        total_deductions=round(deductions, 2),
        net_salary=round(gross - deductions, 2),
        payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d').date() if data.get('payment_date') else None,
        payment_method=data.get('payment_method', 'transfer'),
        status='processed',
        processed_by=user.employee_id,
        processed_at=datetime.utcnow()
    )
    
    db.session.add(payroll)
    db.session.commit()
    
    log_action('payroll', payroll.id, 'create', f"Fiche de paie créée: {employee.full_name()} - {payroll.period_month}/{payroll.period_year}")
    
    return jsonify(payroll.to_dict()), 201


# ============================================================
# API - ORGANIGRAMME
# ============================================================

@app.route('/api/org-chart')
@login_required
def api_org_chart():
    """Données pour l'organigramme"""
    employees = Employee.query.filter(Employee.status == 'active').all()
    departments = Department.query.all()
    
    nodes = []
    for emp in employees:
        nodes.append({
            'id': emp.id,
            'name': emp.full_name(),
            'title': emp.position.title if emp.position else 'N/A',
            'department': emp.department.name if emp.department else 'N/A',
            'manager_id': emp.manager_id,
            'photo_url': f"https://ui-avatars.com/api/?name={emp.first_name}+{emp.last_name}&background=random"
        })
    
    dept_data = [{'id': d.id, 'name': d.name, 'code': d.code, 'manager_id': d.manager_id} for d in departments]
    
    return jsonify({
        'employees': nodes,
        'departments': dept_data
    })


# ============================================================
# API - UTILISATEURS / PARAMÈTRES
# ============================================================

@app.route('/api/users', methods=['GET'])
@login_required
@role_required('admin')
def api_users_list():
    """Liste des utilisateurs (admin only)"""
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/users', methods=['POST'])
@login_required
@role_required('admin')
def api_user_create():
    """Créer un utilisateur"""
    data = request.get_json()
    
    # Vérifier si l'email ou username existe déjà
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Cet email existe déjà'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'employee'),
        employee_id=data.get('employee_id'),
        is_active=data.get('is_active', True)
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    log_action('user', user.id, 'create', f"Utilisateur créé: {user.username}")
    
    return jsonify(user.to_dict()), 201

@app.route('/api/users/<int:id>', methods=['PUT'])
@login_required
@role_required('admin')
def api_user_update(id):
    """Modifier un utilisateur"""
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    db.session.commit()
    log_action('user', id, 'update', f"Utilisateur modifié: {user.username}")
    
    return jsonify(user.to_dict())

@app.route('/api/me', methods=['GET'])
@login_required
def api_me():
    """Informations de l'utilisateur connecté"""
    user = get_current_user()
    return jsonify(user.to_dict())

@app.route('/api/me/password', methods=['PUT'])
@login_required
def api_change_password():
    """Changer le mot de passe"""
    user = get_current_user()
    data = request.get_json()
    
    if not user.check_password(data.get('current_password')):
        return jsonify({'error': 'Mot de passe actuel incorrect'}), 400
    
    user.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Mot de passe mis à jour'})


# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == '__main__':
    create_tables()
    seed_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    create_tables()
    seed_data()
