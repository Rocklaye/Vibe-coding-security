let map = null;
let vehicleMarkers = {};
let routeLines = {};

// Icônes personnalisées pour les marqueurs
const vehicleIcons = {
    disponible: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    }),
    en_mission: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    }),
    maintenance: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    }),
    default: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    })
};

function initDashboardMap(gpsData) {
    if (map) {
        map.remove();
    }
    
    map = L.map('dashboardMap').setView([46.603354, 1.888334], 6);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    
    // Ajouter les marqueurs des véhicules
    if (gpsData && gpsData.length > 0) {
        gpsData.forEach(vehicle => {
            addVehicleMarker(vehicle);
        });
        
        // Ajuster la vue pour voir tous les marqueurs
        const group = new L.featureGroup(Object.values(vehicleMarkers));
        if (group.getBounds().isValid()) {
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }
}

function initTrackingMap(vehiclePositions) {
    if (map) {
        map.remove();
    }
    
    map = L.map('trackingMap').setView([46.603354, 1.888334], 6);
    
    L.tileLayer('https://{s}.tilelayer.com/cache/tiles/1.0.0/map/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Ajouter les marqueurs avec historique
    if (vehiclePositions && vehiclePositions.length > 0) {
        vehiclePositions.forEach(vehicle => {
            const marker = addVehicleMarker(vehicle);
            
            // Charger l'historique des positions
            loadVehicleHistory(vehicle.id, marker);
        });
        
        const group = new L.featureGroup(Object.values(vehicleMarkers));
        if (group.getBounds().isValid()) {
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }
    
    // Rafraîchir les positions toutes les 30 secondes
    setInterval(refreshVehiclePositions, 30000);
}

function addVehicleMarker(vehicle) {
    const icon = vehicleIcons[vehicle.status] || vehicleIcons.default;
    
    const marker = L.marker([vehicle.latitude, vehicle.longitude], {icon: icon})
        .addTo(map)
        .bindPopup(`
            <strong>${vehicle.registration}</strong><br>
            Type: ${vehicle.type || 'N/A'}<br>
            Statut: ${vehicle.status}<br>
            Vitesse: ${vehicle.speed ? Math.round(vehicle.speed) + ' km/h' : 'N/A'}<br>
            Tournée: ${vehicle.tour_reference || 'N/A'}<br>
            <small>Dernière mise à jour: ${vehicle.last_update ? new Date(vehicle.last_update).toLocaleTimeString('fr-FR') : 'N/A'}</small>
        `);
    
    vehicleMarkers[vehicle.id] = marker;
    return marker;
}

function loadVehicleHistory(vehicleId, marker) {
    fetch(`/api/gps/history/${vehicleId}?hours=2`)
        .then(response => response.json())
        .then(positions => {
            if (positions.length > 1) {
                const latlngs = positions.map(p => [p.latitude, p.longitude]);
                
                // Supprimer l'ancienne ligne si elle existe
                if (routeLines[vehicleId]) {
                    map.removeLayer(routeLines[vehicleId]);
                }
                
                // Tracer la route
                routeLines[vehicleId] = L.polyline(latlngs, {
                    color: 'blue',
                    weight: 3,
                    opacity: 0.6
                }).addTo(map);
            }
        });
}

function refreshVehiclePositions() {
    fetch('/tracking')
        .then(response => response.text())
        .then(html => {
            // Extraire les nouvelles positions (simplifié)
            // Dans une version complète, on ferait un appel API dédié
        });
}

function centerOnVehicle(vehicleId) {
    const marker = vehicleMarkers[vehicleId];
    if (marker) {
        map.setView(marker.getLatLng(), 15);
        marker.openPopup();
    }
}

// Fonction pour simuler un mouvement fluide (animation)
function animateMarker(marker, newLatLng, duration = 1000) {
    const start = marker.getLatLng();
    const startTime = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const lat = start.lat + (newLatLng.lat - start.lat) * progress;
        const lng = start.lng + (newLatLng.lng - start.lng) * progress;
        
        marker.setLatLng([lat, lng]);
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}