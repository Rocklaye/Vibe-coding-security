from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User, Vehicle, Driver, Tour, GPSPosition, Incident
from datetime import datetime, timedelta
import random
import json
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_tres_longue_et_complexe'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fleet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Contexte global pour le thread de simulation GPS
gps_simulation_active = False
gps_thread = None

def init_database():
    """Initialise la base de données avec des données de test"""
    db.create_all()
    
    # Vérifier si la base de données est déjà initialisée
    if User.query.first() is not None:
        return
    
    # Création des utilisateurs
    users = [
        User(username='admin', password=generate_password_hash('admin123'), 
             role='admin', full_name='Administrateur Système', email='admin@fleet.com'),
        User(username='dispatcher', password=generate_password_hash('dispatch123'), 
             role='dispatcher', full_name='Jean Dupont', email='dispatcher@fleet.com'),
        User(username='driver1', password=generate_password_hash('driver123'), 
             role='driver', full_name='Pierre Martin', email='pierre@fleet.com'),
        User(username='driver2', password=generate_password_hash('driver123'), 
             role='driver', full_name='Marie Lambert', email='marie@fleet.com'),
        User(username='driver3', password=generate_password_hash('driver123'), 
             role='driver', full_name='Luc Bernard', email='luc@fleet.com'),
    ]
    
    # Création des véhicules
    vehicles = [
        Vehicle(registration='AA-123-BB', brand='Renault', model='Master', 
                type='fourgon', year=2020, status='disponible', mileage=45000,
                fuel_type='diesel', capacity_kg=1500, capacity_m3=12,
                last_maintenance_date=datetime.now() - timedelta(days=30),
                next_maintenance_km=50000),
        Vehicle(registration='BB-456-CC', brand='Mercedes', model='Sprinter', 
                type='fourgon', year=2021, status='en_mission', mileage=32000,
                fuel_type='diesel', capacity_kg=2000, capacity_m3=15,
                last_maintenance_date=datetime.now() - timedelta(days=15),
                next_maintenance_km=40000),
        Vehicle(registration='CC-789-DD', brand='Iveco', model='Daily', 
                type='camion', year=2019, status='disponible', mileage=78000,
                fuel_type='diesel', capacity_kg=3500, capacity_m3=25,
                last_maintenance_date=datetime.now() - timedelta(days=60),
                next_maintenance_km=80000),
        Vehicle(registration='DD-012-EE', brand='Volkswagen', model='Crafter', 
                type='fourgon', year=2022, status='maintenance', mileage=15000,
                fuel_type='diesel', capacity_kg=1800, capacity_m3=14,
                last_maintenance_date=datetime.now() - timedelta(days=90),
                next_maintenance_km=30000),
        Vehicle(registration='EE-345-FF', brand='Ford', model='Transit', 
                type='utilitaire', year=2023, status='disponible', mileage=8500,
                fuel_type='essence', capacity_kg=1000, capacity_m3=8,
                last_maintenance_date=datetime.now() - timedelta(days=5),
                next_maintenance_km=20000),
    ]
    
    # Ajout dans la base de données
    db.session.add_all(users)
    db.session.commit()
    db.session.add_all(vehicles)
    db.session.commit()
    
    # Création des chauffeurs
    drivers = [
        Driver(user_id=3, vehicle_id=2, license_number='LIC123456', 
               license_type='C', license_expiry=datetime.now() + timedelta(days=365*2),
               experience_years=8, status='en_mission'),
        Driver(user_id=4, vehicle_id=1, license_number='LIC789012', 
               license_type='C', license_expiry=datetime.now() + timedelta(days=365*3),
               experience_years=5, status='disponible'),
        Driver(user_id=5, vehicle_id=None, license_number='LIC345678', 
               license_type='B', license_expiry=datetime.now() + timedelta(days=365),
               experience_years=12, status='disponible'),
    ]
    
    db.session.add_all(drivers)
    db.session.commit()
    
    # Création de quelques tournées
    tours = [
        Tour(reference='TOUR-2024-001', driver_id=3, vehicle_id=2,
             departure_address='Paris 15e - Entrepôt Central',
             departure_lat=48.8566, departure_lon=2.3522,
             arrival_address='Lyon 3e - Centre Commercial',
             arrival_lat=45.7578, arrival_lon=4.8320,
             planned_departure=datetime.now() - timedelta(hours=2),
             planned_arrival=datetime.now() + timedelta(hours=4),
             actual_departure=datetime.now() - timedelta(hours=2),
             status='en_cours', distance_km=465.0,
             cargo_description='Produits électroniques',
             cargo_weight_kg=1200.0),
        Tour(reference='TOUR-2024-002', driver_id=None, vehicle_id=1,
             departure_address='Paris 20e - Dépôt Nord',
             departure_lat=48.8647, departure_lon=2.3992,
             arrival_address='Marseille 1er - Port',
             arrival_lat=43.2965, arrival_lon=5.3698,
             planned_departure=datetime.now() + timedelta(hours=6),
             planned_arrival=datetime.now() + timedelta(hours=14),
             status='planifie', distance_km=775.0,
             cargo_description='Matériel médical',
             cargo_weight_kg=800.0),
        Tour(reference='TOUR-2024-003', driver_id=None, vehicle_id=3,
             departure_address='Lille Centre - Agence',
             departure_lat=50.6292, departure_lon=3.0573,
             arrival_address='Bruxelles - Bureau',
             arrival_lat=50.8503, arrival_lon=4.3517,
             planned_departure=datetime.now() + timedelta(days=1),
             planned_arrival=datetime.now() + timedelta(days=1, hours=3),
             status='planifie', distance_km=110.0,
             cargo_description='Documents administratifs',
             cargo_weight_kg=50.0),
    ]
    
    db.session.add_all(tours)
    db.session.commit()
    
    # Création d'incidents
    incidents = [
        Incident(vehicle_id=4, tour_id=None, type='maintenance',
                severity='moyen', description='Révision des 15000 km',
                reported_by=1, status='en_cours',
                cost=450.0, created_at=datetime.now() - timedelta(days=2)),
        Incident(vehicle_id=2, tour_id=1, type='panne',
                severity='haut', description='Problème de climatisation',
                location='A6 - Aire de repos', reported_by=3, status='ouvert',
                created_at=datetime.now() - timedelta(hours=1)),
    ]
    
    db.session.add_all(incidents)
    db.session.commit()
    
    # Créer des positions GPS simulées pour le véhicule en mission
    positions = []
    current_lat, current_lon = 46.5, 4.5  # Point intermédiaire Paris-Lyon
    
    for i in range(5):
        positions.append(GPSPosition(
            vehicle_id=2, tour_id=1,
            latitude=current_lat + random.uniform(-0.1, 0.1),
            longitude=current_lon + random.uniform(-0.1, 0.1),
            speed=random.uniform(80, 110),
            heading=random.uniform(0, 360),
            timestamp=datetime.now() - timedelta(minutes=30*(5-i))
        ))
    
    db.session.add_all(positions)
    db.session.commit()

def simulate_gps_updates():
    """Thread de simulation GPS pour les véhicules en mission"""
    global gps_simulation_active
    
    while gps_simulation_active:
        with app.app_context():
            # Récupérer les véhicules en mission
            active_vehicles = Vehicle.query.filter_by(status='en_mission').all()
            
            for vehicle in active_vehicles:
                # Vérifier si le véhicule a une tournée en cours
                active_tour = Tour.query.filter_by(
                    vehicle_id=vehicle.id, 
                    status='en_cours'
                ).first()
                
                if active_tour:
                    # Simuler une nouvelle position
                    if active_tour.departure_lat and active_tour.arrival_lat:
                        progress = random.random()
                        new_lat = active_tour.departure_lat + (active_tour.arrival_lat - active_tour.departure_lat) * progress
                        new_lon = active_tour.departure_lon + (active_tour.arrival_lon - active_tour.departure_lon) * progress
                    else:
                        new_lat = 48.8566 + random.uniform(-0.05, 0.05)
                        new_lon = 2.3522 + random.uniform(-0.05, 0.05)
                    
                    # Créer la position GPS
                    position = GPSPosition(
                        vehicle_id=vehicle.id,
                        tour_id=active_tour.id,
                        latitude=new_lat + random.uniform(-0.01, 0.01),
                        longitude=new_lon + random.uniform(-0.01, 0.01),
                        speed=random.uniform(70, 130),
                        heading=random.uniform(0, 360)
                    )
                    
                    db.session.add(position)
                    
                    # Mettre à jour le kilométrage du véhicule
                    vehicle.mileage += int(random.uniform(0.1, 0.5))
                    
            db.session.commit()
        
        time.sleep(30)  # Mise à jour toutes les 30 secondes

# Routes pour l'authentification
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Routes pour le tableau de bord
@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_vehicles': Vehicle.query.count(),
        'active_vehicles': Vehicle.query.filter_by(status='en_mission').count(),
        'available_vehicles': Vehicle.query.filter_by(status='disponible').count(),
        'maintenance_vehicles': Vehicle.query.filter_by(status='maintenance').count(),
        'total_drivers': Driver.query.count(),
        'active_tours': Tour.query.filter_by(status='en_cours').count(),
        'planned_tours': Tour.query.filter_by(status='planifie').count(),
        'open_incidents': Incident.query.filter_by(status='ouvert').count(),
        'total_mileage': db.session.query(db.func.sum(Vehicle.mileage)).scalar() or 0
    }
    
    recent_incidents = Incident.query.order_by(Incident.created_at.desc()).limit(5).all()
    active_tours_list = Tour.query.filter_by(status='en_cours').all()
    
    # Récupérer les positions GPS récentes pour la carte
    gps_data = []
    for tour in active_tours_list:
        if tour.vehicle:
            last_position = GPSPosition.query.filter_by(
                vehicle_id=tour.vehicle_id
            ).order_by(GPSPosition.timestamp.desc()).first()
            
            if last_position:
                gps_data.append({
                    'vehicle_id': tour.vehicle.id,
                    'registration': tour.vehicle.registration,
                    'latitude': last_position.latitude,
                    'longitude': last_position.longitude,
                    'tour_reference': tour.reference,
                    'status': 'active'
                })
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_incidents=recent_incidents,
                         gps_data=json.dumps(gps_data))

# Routes pour la gestion des véhicules
@app.route('/vehicles')
@login_required
def vehicles():
    if current_user.role not in ['admin', 'dispatcher']:
        return redirect(url_for('dashboard'))
    
    all_vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=all_vehicles)

@app.route('/api/vehicles', methods=['GET'])
@login_required
def get_vehicles():
    vehicles = Vehicle.query.all()
    return jsonify([{
        'id': v.id,
        'registration': v.registration,
        'brand': v.brand,
        'model': v.model,
        'type': v.type,
        'status': v.status,
        'mileage': v.mileage,
        'driver': f"{v.driver.user.full_name}" if v.driver else None
    } for v in vehicles])

@app.route('/api/vehicles', methods=['POST'])
@login_required
def add_vehicle():
    if current_user.role not in ['admin', 'dispatcher']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.json
    
    try:
        vehicle = Vehicle(
            registration=data['registration'],
            brand=data['brand'],
            model=data['model'],
            type=data['type'],
            year=data.get('year'),
            status='disponible',
            mileage=data.get('mileage', 0),
            fuel_type=data.get('fuel_type'),
            capacity_kg=data.get('capacity_kg'),
            capacity_m3=data.get('capacity_m3')
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        return jsonify({'success': True, 'id': vehicle.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
@login_required
def update_vehicle(vehicle_id):
    if current_user.role not in ['admin', 'dispatcher']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.json
    
    try:
        for key, value in data.items():
            if hasattr(vehicle, key):
                setattr(vehicle, key, value)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
@login_required
def delete_vehicle(vehicle_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    try:
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Routes pour la gestion des chauffeurs
@app.route('/drivers')
@login_required
def drivers():
    if current_user.role not in ['admin', 'dispatcher']:
        return redirect(url_for('dashboard'))
    
    all_drivers = Driver.query.all()
    available_vehicles = Vehicle.query.filter_by(status='disponible').all()
    return render_template('drivers.html', drivers=all_drivers, vehicles=available_vehicles)

@app.route('/api/drivers/assign', methods=['POST'])
@login_required
def assign_driver():
    if current_user.role not in ['admin', 'dispatcher']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.json
    driver_id = data.get('driver_id')
    vehicle_id = data.get('vehicle_id')
    
    driver = Driver.query.get_or_404(driver_id)
    
    # Libérer l'ancien véhicule
    if driver.vehicle_id:
        old_vehicle = Vehicle.query.get(driver.vehicle_id)
        if old_vehicle:
            old_vehicle.status = 'disponible'
    
    # Assigner le nouveau véhicule
    if vehicle_id:
        vehicle = Vehicle.query.get(vehicle_id)
        if vehicle:
            vehicle.status = 'en_mission' if driver.status == 'en_mission' else 'disponible'
            driver.vehicle_id = vehicle_id
    else:
        driver.vehicle_id = None
    
    db.session.commit()
    return jsonify({'success': True})

# Routes pour les tournées
@app.route('/tours')
@login_required
def tours():
    all_tours = Tour.query.order_by(Tour.planned_departure.desc()).all()
    available_drivers = Driver.query.filter(
        Driver.status.in_(['disponible']),
        Driver.user_id.isnot(None)
    ).all()
    available_vehicles = Vehicle.query.filter(
        Vehicle.status.in_(['disponible'])
    ).all()
    
    return render_template('tours.html', 
                         tours=all_tours,
                         drivers=available_drivers,
                         vehicles=available_vehicles)

@app.route('/api/tours', methods=['POST'])
@login_required
def create_tour():
    if current_user.role not in ['admin', 'dispatcher']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.json
    
    try:
        tour = Tour(
            reference=f"TOUR-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
            driver_id=data.get('driver_id'),
            vehicle_id=data.get('vehicle_id'),
            departure_address=data['departure_address'],
            departure_lat=data.get('departure_lat'),
            departure_lon=data.get('departure_lon'),
            arrival_address=data['arrival_address'],
            arrival_lat=data.get('arrival_lat'),
            arrival_lon=data.get('arrival_lon'),
            planned_departure=datetime.fromisoformat(data['planned_departure']),
            planned_arrival=datetime.fromisoformat(data['planned_arrival']) if data.get('planned_arrival') else None,
            distance_km=data.get('distance_km'),
            cargo_description=data.get('cargo_description'),
            cargo_weight_kg=data.get('cargo_weight_kg'),
            notes=data.get('notes')
        )
        
        # Mettre à jour le statut du chauffeur et du véhicule
        if tour.driver_id:
            driver = Driver.query.get(tour.driver_id)
            if driver:
                driver.status = 'en_mission'
        
        if tour.vehicle_id:
            vehicle = Vehicle.query.get(tour.vehicle_id)
            if vehicle:
                vehicle.status = 'en_mission'
        
        db.session.add(tour)
        db.session.commit()
        
        return jsonify({'success': True, 'id': tour.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/tours/<int:tour_id>/status', methods=['PUT'])
@login_required
def update_tour_status(tour_id):
    tour = Tour.query.get_or_404(tour_id)
    data = request.json
    new_status = data.get('status')
    
    tour.status = new_status
    
    if new_status == 'en_cours':
        tour.actual_departure = datetime.now()
    elif new_status == 'termine':
        tour.actual_arrival = datetime.now()
        
        # Libérer le chauffeur et le véhicule
        if tour.driver_id:
            driver = Driver.query.get(tour.driver_id)
            if driver:
                driver.status = 'disponible'
        
        if tour.vehicle_id:
            vehicle = Vehicle.query.get(tour.vehicle_id)
            if vehicle:
                vehicle.status = 'disponible'
                # Ajouter la distance au kilométrage
                if tour.distance_km:
                    vehicle.mileage += int(tour.distance_km)
    
    db.session.commit()
    return jsonify({'success': True})

# Routes pour le suivi GPS
@app.route('/tracking')
@login_required
def tracking():
    if current_user.role not in ['admin', 'dispatcher']:
        return redirect(url_for('dashboard'))
    
    active_tours = Tour.query.filter_by(status='en_cours').all()
    all_vehicles = Vehicle.query.all()
    
    # Récupérer toutes les positions récentes
    recent_positions = db.session.query(
        GPSPosition.vehicle_id,
        db.func.max(GPSPosition.timestamp).label('max_timestamp')
    ).group_by(GPSPosition.vehicle_id).subquery()
    
    latest_positions = GPSPosition.query.join(
        recent_positions,
        db.and_(
            GPSPosition.vehicle_id == recent_positions.c.vehicle_id,
            GPSPosition.timestamp == recent_positions.c.max_timestamp
        )
    ).all()
    
    # Préparer les données pour la carte
    vehicle_positions = []
    for pos in latest_positions:
        vehicle = Vehicle.query.get(pos.vehicle_id)
        tour = Tour.query.filter_by(
            vehicle_id=pos.vehicle_id, 
            status='en_cours'
        ).first()
        
        vehicle_positions.append({
            'id': vehicle.id,
            'registration': vehicle.registration,
            'type': vehicle.type,
            'status': vehicle.status,
            'latitude': pos.latitude,
            'longitude': pos.longitude,
            'speed': pos.speed,
            'heading': pos.heading,
            'last_update': pos.timestamp.isoformat(),
            'tour_reference': tour.reference if tour else None
        })
    
    return render_template('tracking.html', 
                         positions=vehicle_positions,
                         active_tours=active_tours)

@app.route('/api/gps/history/<int:vehicle_id>')
@login_required
def gps_history(vehicle_id):
    hours = request.args.get('hours', 2, type=int)
    since = datetime.now() - timedelta(hours=hours)
    
    positions = GPSPosition.query.filter(
        GPSPosition.vehicle_id == vehicle_id,
        GPSPosition.timestamp >= since
    ).order_by(GPSPosition.timestamp.asc()).all()
    
    return jsonify([{
        'latitude': pos.latitude,
        'longitude': pos.longitude,
        'speed': pos.speed,
        'timestamp': pos.timestamp.isoformat()
    } for pos in positions])

# Routes pour les incidents
@app.route('/incidents')
@login_required
def incidents():
    all_incidents = Incident.query.order_by(Incident.created_at.desc()).all()
    vehicles = Vehicle.query.all()
    tours = Tour.query.all()
    
    return render_template('incidents.html', 
                         incidents=all_incidents,
                         vehicles=vehicles,
                         tours=tours)

@app.route('/api/incidents', methods=['POST'])
@login_required
def create_incident():
    data = request.json
    
    try:
        incident = Incident(
            vehicle_id=data.get('vehicle_id'),
            tour_id=data.get('tour_id'),
            type=data['type'],
            severity=data.get('severity', 'moyen'),
            description=data['description'],
            location=data.get('location'),
            reported_by=current_user.id,
            cost=data.get('cost')
        )
        
        db.session.add(incident)
        
        # Mettre à jour le statut du véhicule si nécessaire
        if data.get('vehicle_id') and data['type'] in ['maintenance', 'panne']:
            vehicle = Vehicle.query.get(data['vehicle_id'])
            if vehicle:
                vehicle.status = 'maintenance'
        
        db.session.commit()
        return jsonify({'success': True, 'id': incident.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/incidents/<int:incident_id>', methods=['PUT'])
@login_required
def update_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    data = request.json
    
    try:
        for key, value in data.items():
            if hasattr(incident, key):
                setattr(incident, key, value)
        
        if data.get('status') == 'resolu':
            incident.resolved_at = datetime.now()
            
            # Remettre le véhicule en service si l'incident est résolu
            if incident.vehicle_id:
                vehicle = Vehicle.query.get(incident.vehicle_id)
                if vehicle and vehicle.status == 'maintenance':
                    vehicle.status = 'disponible'
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# API pour le tableau de bord
@app.route('/api/stats')
@login_required
def get_stats():
    stats = {
        'total_vehicles': Vehicle.query.count(),
        'active_vehicles': Vehicle.query.filter_by(status='en_mission').count(),
        'available_vehicles': Vehicle.query.filter_by(status='disponible').count(),
        'maintenance_vehicles': Vehicle.query.filter_by(status='maintenance').count(),
        'total_drivers': Driver.query.count(),
        'active_tours': Tour.query.filter_by(status='en_cours').count(),
        'planned_tours': Tour.query.filter_by(status='planifie').count(),
        'completed_tours_today': Tour.query.filter(
            Tour.status == 'termine',
            Tour.actual_arrival >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count(),
        'open_incidents': Incident.query.filter_by(status='ouvert').count(),
        'total_mileage': db.session.query(db.func.sum(Vehicle.mileage)).scalar() or 0,
        'fuel_efficiency': round(random.uniform(8, 12), 1)  # Simulation L/100km
    }
    
    return jsonify(stats)

@app.route('/api/start_gps_simulation')
@login_required
def start_gps_simulation():
    global gps_simulation_active, gps_thread
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    if not gps_simulation_active:
        gps_simulation_active = True
        gps_thread = threading.Thread(target=simulate_gps_updates)
        gps_thread.daemon = True
        gps_thread.start()
    
    return jsonify({'success': True, 'message': 'Simulation GPS démarrée'})

@app.route('/api/stop_gps_simulation')
@login_required
def stop_gps_simulation():
    global gps_simulation_active
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    gps_simulation_active = False
    return jsonify({'success': True, 'message': 'Simulation GPS arrêtée'})

if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True, port=5000)