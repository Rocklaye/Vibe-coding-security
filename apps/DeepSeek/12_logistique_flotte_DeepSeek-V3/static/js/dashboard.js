// Initialisation des graphiques
document.addEventListener('DOMContentLoaded', function() {
    initFleetChart();
    initMileageChart();
    startAutoRefresh(60);
});

function initFleetChart() {
    const ctx = document.getElementById('fleetChart');
    if (!ctx) return;
    
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Disponibles', 'En mission', 'En maintenance', 'Hors service'],
                    datasets: [{
                        data: [
                            stats.available_vehicles,
                            stats.active_vehicles,
                            stats.maintenance_vehicles,
                            stats.total_vehicles - stats.available_vehicles - stats.active_vehicles - stats.maintenance_vehicles
                        ],
                        backgroundColor: [
                            '#28a745',
                            '#007bff',
                            '#ffc107',
                            '#6c757d'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        });
}

function initMileageChart() {
    const ctx = document.getElementById('mileageChart');
    if (!ctx) return;
    
    fetch('/api/vehicles')
        .then(response => response.json())
        .then(vehicles => {
            const labels = vehicles.map(v => v.registration);
            const data = vehicles.map(v => v.mileage);
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Kilométrage (km)',
                        data: data,
                        backgroundColor: '#007bff',
                        borderColor: '#0056b3',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return value.toLocaleString() + ' km';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        });
}

// Rafraîchissement périodique des graphiques
function refreshCharts() {
    initFleetChart();
    initMileageChart();
}

// Export des données
function exportData(format = 'csv') {
    fetch('/api/vehicles')
        .then(response => response.json())
        .then(data => {
            if (format === 'csv') {
                exportToCSV(data);
            } else if (format === 'json') {
                exportToJSON(data);
            }
        });
}

function exportToCSV(data) {
    if (data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(h => JSON.stringify(row[h] || '')).join(','))
    ].join('\n');
    
    downloadFile('vehicles_export.csv', csvContent, 'text/csv');
}

function exportToJSON(data) {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile('vehicles_export.json', jsonContent, 'application/json');
}

function downloadFile(filename, content, type) {
    const blob = new Blob([content], { type: type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}