"""
Modèles de données pour l'application RH
SQLAlchemy ORM avec SQLite
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json

db = SQLAlchemy()

# Tables d'association
employee_skills = db.Table('employee_skills',
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

class Department(db.Model):
    """Département de l'entreprise"""
    __tablename__ = 'department'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    employees = db.relationship('Employee', foreign_keys='Employee.department_id', back_populates='department', lazy='dynamic')
    parent = db.relationship('Department', remote_side=[id], backref='sub_departments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_id': self.parent_id,
            'manager_id': self.manager_id,
            'employee_count': self.employees.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Position(db.Model):
    """Poste/fonction dans l'entreprise"""
    __tablename__ = 'position'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50))  # Junior, Senior, Lead, Director, VP, C-Level
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    base_salary_min = db.Column(db.Float)
    base_salary_max = db.Column(db.Float)
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'level': self.level,
            'department_id': self.department_id,
            'base_salary_min': self.base_salary_min,
            'base_salary_max': self.base_salary_max,
            'description': self.description
        }

class Employee(db.Model):
    """Employé de l'entreprise"""
    __tablename__ = 'employee'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # Matricule
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    hire_date = db.Column(db.Date, nullable=False)
    termination_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, on_leave, terminated, suspended
    
    # Adresse
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='France')
    
    # Informations professionnelles
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    
    # Salaire
    base_salary = db.Column(db.Float)
    currency = db.Column(db.String(3), default='EUR')
    
    # Informations RH
    contract_type = db.Column(db.String(20), default='CDI')  # CDI, CDD, Stage, Freelance
    work_hours_per_week = db.Column(db.Float, default=35)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    department = db.relationship('Department', foreign_keys=[department_id], back_populates='employees')
    position = db.relationship('Position', backref='employees')
    manager = db.relationship('Employee', remote_side=[id], backref='subordinates')
    user_account = db.relationship('User', backref='employee_profile', uselist=False)
    leaves = db.relationship('Leave', foreign_keys='Leave.employee_id', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    evaluations = db.relationship('Evaluation', foreign_keys='Evaluation.employee_id', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    payroll_records = db.relationship('Payroll', foreign_keys='Payroll.employee_id', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    managed_departments = db.relationship('Department', foreign_keys='Department.manager_id', backref='department_manager')
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def tenure_years(self):
        if not self.hire_date:
            return 0
        end_date = self.termination_date or datetime.now().date()
        return round((end_date - self.hire_date).days / 365.25, 1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name(),
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'termination_date': self.termination_date.isoformat() if self.termination_date else None,
            'status': self.status,
            'address': self.address,
            'city': self.city,
            'postal_code': self.postal_code,
            'country': self.country,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'position_id': self.position_id,
            'position_title': self.position.title if self.position else None,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name() if self.manager else None,
            'base_salary': self.base_salary,
            'currency': self.currency,
            'contract_type': self.contract_type,
            'work_hours_per_week': self.work_hours_per_week,
            'tenure_years': self.tenure_years(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Skill(db.Model):
    """Compétence"""
    __tablename__ = 'skill'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50))  # Technique, Soft skill, Langue, etc.
    
    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'category': self.category}

class Leave(db.Model):
    """Demande de congé"""
    __tablename__ = 'leave'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)  # annual, sick, maternity, paternity, unpaid, rtt
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, cancelled
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Approbation
    approved_by = db.Column(db.Integer, db.ForeignKey('employee.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Relations
    approver = db.relationship('Employee', foreign_keys=[approved_by], backref='approved_leaves')
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name() if self.employee else None,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'days_requested': self.days_requested,
            'reason': self.reason,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.full_name() if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason
        }

class Evaluation(db.Model):
    """Évaluation de performance annuelle"""
    __tablename__ = 'evaluation'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    evaluation_year = db.Column(db.Integer, nullable=False)
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    
    # Objectifs
    goals = db.Column(db.Text)
    goals_achievement = db.Column(db.Float)  # Pourcentage
    
    # Compétences évaluées (JSON)
    technical_skills = db.Column(db.Float)  # Note 1-5
    communication = db.Column(db.Float)
    teamwork = db.Column(db.Float)
    leadership = db.Column(db.Float)
    initiative = db.Column(db.Float)
    punctuality = db.Column(db.Float)
    
    # Commentaires
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    employee_comments = db.Column(db.Text)
    evaluator_comments = db.Column(db.Text)
    
    # Note globale et statut
    overall_rating = db.Column(db.Float)  # Note 1-5
    status = db.Column(db.String(20), default='draft')  # draft, submitted, reviewed, approved
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    evaluator = db.relationship('Employee', foreign_keys=[evaluator_id], backref='evaluations_given')
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name() if self.employee else None,
            'evaluator_id': self.evaluator_id,
            'evaluator_name': self.evaluator.full_name() if self.evaluator else None,
            'evaluation_year': self.evaluation_year,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'goals': self.goals,
            'goals_achievement': self.goals_achievement,
            'technical_skills': self.technical_skills,
            'communication': self.communication,
            'teamwork': self.teamwork,
            'leadership': self.leadership,
            'initiative': self.initiative,
            'punctuality': self.punctuality,
            'strengths': self.strengths,
            'areas_for_improvement': self.areas_for_improvement,
            'employee_comments': self.employee_comments,
            'evaluator_comments': self.evaluator_comments,
            'overall_rating': self.overall_rating,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Payroll(db.Model):
    """Bulletin de paie"""
    __tablename__ = 'payroll'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    period_month = db.Column(db.Integer, nullable=False)  # 1-12
    period_year = db.Column(db.Integer, nullable=False)
    
    # Éléments de paie
    base_salary = db.Column(db.Float, nullable=False)
    overtime_hours = db.Column(db.Float, default=0)
    overtime_amount = db.Column(db.Float, default=0)
    bonus = db.Column(db.Float, default=0)
    commission = db.Column(db.Float, default=0)
    
    # Avantages
    meal_vouchers = db.Column(db.Float, default=0)
    transport_allowance = db.Column(db.Float, default=0)
    other_allowances = db.Column(db.Float, default=0)
    
    # Retenues
    social_security = db.Column(db.Float, default=0)
    unemployment_insurance = db.Column(db.Float, default=0)
    retirement_contribution = db.Column(db.Float, default=0)
    income_tax = db.Column(db.Float, default=0)
    other_deductions = db.Column(db.Float, default=0)
    
    # Totaux
    gross_salary = db.Column(db.Float, nullable=False)
    total_deductions = db.Column(db.Float, nullable=False)
    net_salary = db.Column(db.Float, nullable=False)
    
    # Métadonnées
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(20), default='transfer')  # transfer, check, cash
    status = db.Column(db.String(20), default='draft')  # draft, processed, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('employee.id'))
    processed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name() if self.employee else None,
            'period_month': self.period_month,
            'period_year': self.period_year,
            'period_label': f"{self.period_month:02d}/{self.period_year}",
            'base_salary': self.base_salary,
            'overtime_hours': self.overtime_hours,
            'overtime_amount': self.overtime_amount,
            'bonus': self.bonus,
            'commission': self.commission,
            'meal_vouchers': self.meal_vouchers,
            'transport_allowance': self.transport_allowance,
            'other_allowances': self.other_allowances,
            'social_security': self.social_security,
            'unemployment_insurance': self.unemployment_insurance,
            'retirement_contribution': self.retirement_contribution,
            'income_tax': self.income_tax,
            'other_deductions': self.other_deductions,
            'gross_salary': self.gross_salary,
            'total_deductions': self.total_deductions,
            'net_salary': self.net_salary,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_by': self.processed_by,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class User(db.Model):
    """Compte utilisateur pour l'accès à l'application"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Rôle
    role = db.Column(db.String(20), default='employee')  # employee, manager, hr, admin
    
    # Lien vers employé
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), unique=True)
    
    # Sécurité
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Vérifie si l'utilisateur a un rôle spécifique ou supérieur"""
        role_hierarchy = {'employee': 1, 'manager': 2, 'hr': 3, 'admin': 4}
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(role, 0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'employee_id': self.employee_id,
            'employee_name': self.employee_profile.full_name() if self.employee_profile else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    """Journal d'audit pour tracer les actions importantes"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, approve, reject
    entity_type = db.Column(db.String(30), nullable=False)  # employee, leave, evaluation, payroll
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LeaveBalance(db.Model):
    """Solde de congés par employé et par type"""
    __tablename__ = 'leave_balance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_days = db.Column(db.Float, default=0)
    used_days = db.Column(db.Float, default=0)
    remaining_days = db.Column(db.Float, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'leave_type': self.leave_type,
            'year': self.year,
            'total_days': self.total_days,
            'used_days': self.used_days,
            'remaining_days': self.remaining_days
        }
