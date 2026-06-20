// Variables globales
let expenseChart = null;
let currentMonth = new Date().toISOString().slice(0, 7);

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/dashboard') {
        initializeDashboard();
    }
});

// Initialisation du tableau de bord
function initializeDashboard() {
    loadCategories();
    setupTransactionForm();
    setupMonthSelector();
    setupFilters();
    loadSummary();
    loadAllTransactions();
}

// Chargement des catégories
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        
        const categorySelect = document.getElementById('category');
        categorySelect.innerHTML = '';
        
        // Filtrer par type sélectionné
        const type = document.getElementById('type').value;
        const filteredCategories = categories.filter(cat => cat.type === type);
        
        filteredCategories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name;
            categorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des catégories:', error);
    }
}

// Mise à jour des catégories quand le type change
if (document.getElementById('type')) {
    document.getElementById('type').addEventListener('change', loadCategories);
}

// Configuration du formulaire de transaction
function setupTransactionForm() {
    const form = document.getElementById('transaction-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const transaction = {
            type: document.getElementById('type').value,
            category_id: document.getElementById('category').value,
            amount: document.getElementById('amount').value,
            transaction_date: document.getElementById('date').value,
            description: document.getElementById('description').value
        };
        
        try {
            const response = await fetch('/api/transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(transaction)
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Transaction ajoutée avec succès !');
                form.reset();
                document.getElementById('date').value = new Date().toISOString().split('T')[0];
                loadSummary();
                loadAllTransactions();
            } else {
                alert('Erreur : ' + data.message);
            }
        } catch (error) {
            console.error('Erreur lors de l\'ajout de la transaction:', error);
            alert('Erreur lors de l\'ajout de la transaction');
        }
    });
    
    // Date par défaut
    document.getElementById('date').value = new Date().toISOString().split('T')[0];
}

// Configuration du sélecteur de mois
function setupMonthSelector() {
    const monthSelector = document.getElementById('month-selector');
    monthSelector.value = currentMonth;
    monthSelector.addEventListener('change', (e) => {
        currentMonth = e.target.value;
        loadSummary();
    });
}

// Configuration des filtres
function setupFilters() {
    document.getElementById('filter-btn').addEventListener('click', () => {
        const startDate = document.getElementById('filter-start').value;
        const endDate = document.getElementById('filter-end').value;
        
        if (startDate && endDate) {
            loadFilteredTransactions(startDate, endDate);
        } else {
            loadAllTransactions();
        }
    });
}

// Chargement du résumé mensuel
async function loadSummary() {
    try {
        const response = await fetch(`/api/summary?month=${currentMonth}`);
        const data = await response.json();
        
        document.getElementById('total-income').textContent = `${data.total_income.toFixed(2)} €`;
        document.getElementById('total-expense').textContent = `${data.total_expense.toFixed(2)} €`;
        
        const balance = document.getElementById('balance');
        balance.textContent = `${data.balance.toFixed(2)} €`;
        
        // Couleur du solde
        if (data.balance >= 0) {
            balance.style.color = '#28a745';
        } else {
            balance.style.color = '#dc3545';
        }
        
        updateExpenseChart(data.expense_by_category);
    } catch (error) {
        console.error('Erreur lors du chargement du résumé:', error);
    }
}

// Mise à jour du graphique des dépenses
function updateExpenseChart(expenseByCategory) {
    const ctx = document.getElementById('expense-chart').getContext('2d');
    
    // Détruire l'ancien graphique
    if (expenseChart) {
        expenseChart.destroy();
    }
    
    const labels = Object.keys(expenseByCategory);
    const data = Object.values(expenseByCategory);
    
    // Couleurs pour le graphique
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#7BC8A4', '#E8C3B9'
    ];
    
    expenseChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: 'white'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 20,
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value.toFixed(2)} € (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Chargement de toutes les transactions
async function loadAllTransactions() {
    try {
        const response = await fetch('/api/transactions');
        const transactions = await response.json();
        displayTransactions(transactions);
    } catch (error) {
        console.error('Erreur lors du chargement des transactions:', error);
    }
}

// Chargement des transactions filtrées
async function loadFilteredTransactions(startDate, endDate) {
    try {
        const response = await fetch(`/api/transactions/filter?start_date=${startDate}&end_date=${endDate}`);
        const transactions = await response.json();
        displayTransactions(transactions);
    } catch (error) {
        console.error('Erreur lors du filtrage des transactions:', error);
    }
}

// Affichage des transactions
function displayTransactions(transactions) {
    const tbody = document.getElementById('transactions-body');
    tbody.innerHTML = '';
    
    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Aucune transaction trouvée</td></tr>';
        return;
    }
    
    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.className = transaction.type === 'income' ? 'income-row' : 'expense-row';
        
        const typeLabel = transaction.type === 'income' ? 'Revenu' : 'Dépense';
        const amountPrefix = transaction.type === 'income' ? '+' : '-';
        
        row.innerHTML = `
            <td>${formatDate(transaction.transaction_date)}</td>
            <td>${typeLabel}</td>
            <td>${transaction.category}</td>
            <td>${transaction.description || '-'}</td>
            <td><strong>${amountPrefix}${transaction.amount.toFixed(2)} €</strong></td>
        `;
        
        tbody.appendChild(row);
    });
}

// Formatage de la date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}