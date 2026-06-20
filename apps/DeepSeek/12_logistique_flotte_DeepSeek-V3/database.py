from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, dispatcher, driver
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    active = db.Column(db.Boolean, default=True)
    
    driver = db.relationship('Driver', backref='user', uselist=False)
    assigned_tours = db.relationship('Tour', backref='assigned_driver', lazy=True)

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    registration = db.Column(db.String(20), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # camion, fourgon, utilitaire
    year = db.Column(db.Integer)
    status = db.Column(db.String(20), default='disponible')  # disponible, en_mission, maintenance, hors_service
    mileage = db.Column(db.Integer, default=0)
    fuel_type = db.Column(db.String(20))
    capacity_kg = db.Column(db.Float)
    capacity_m3 = db.Column(db.Float)
    gps_device_id = db.Column(db.String(50))
    last_maintenance_date = db.Column(db.DateTime)
    next_maintenance_km = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    driver = db.relationship('Driver', backref='vehicle', uselist=False)
    tours = db.relationship('Tour', backref='vehicle', lazy=True)
    gps_positions = db.relationship('GPSPosition', backref='vehicle', lazy=True)
    incidents = db.relationship('Incident', backref='vehicle', lazy=True)

class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), unique=True)
    license_number = db.Column(db.String(30), unique=True, nullable=False)
    license_type = db.Column(db.String(10))
    license_expiry = db.Column(db.DateTime)
    experience_years = db.Column(db.Integer)
    status = db.Column(db.String(20), default='disponible')  # disponible, en_mission, repos, indisponible
    
    def get_current_tour(self):
        return Tour.query.filter_by(driver_id=self.id, status='en_cours').first()

class Tour(db.Model):
    __tablename__ = 'tours'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    departure_address = db.Column(db.String(200), nullable=False)
    departure_lat = db.Column(db.Float)
    departure_lon = db.Column(db.Float)
    arrival_address = db.Column(db.String(200), nullable=False)
    arrival_lat = db.Column(db.Float)
    arrival_lon = db.Column(db.Float)
    planned_departure = db.Column(db.DateTime, nullable=False)
    planned_arrival = db.Column(db.DateTime)
    actual_departure = db.Column(db.DateTime)
    actual_arrival = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='planifie')  # planifie, en_cours, termine, annule
    distance_km = db.Column(db.Float)
    cargo_description = db.Column(db.Text)
    cargo_weight_kg = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    gps_positions = db.relationship('GPSPosition', backref='tour', lazy=True)
    incidents = db.relationship('Incident', backref='tour', lazy=True)

class GPSPosition(db.Model):
    __tablename__ = 'gps_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    tour_id = db.Column(db.Integer, db.ForeignKey('tours.id'))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float)
    heading = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    accuracy = db.Column(db.Float)

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    tour_id = db.Column(db.Integer, db.ForeignKey('tours.id'))
    type = db.Column(db.String(50), nullable=False)  # maintenance, accident, panne, infraction, autre
    severity = db.Column(db.String(20), default='moyen')  # bas, moyen, haut, critique
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200))
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='ouvert')  # ouvert, en_cours, resolu
    resolution = db.Column(db.Text)
    cost = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    reporter = db.relationship('User', backref='reported_incidents')