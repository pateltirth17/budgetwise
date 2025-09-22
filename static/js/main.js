/**
 * BudgetWise AI - Main JavaScript File
 * Handles form submission, API communication, and chart rendering
 */

// Global variables for Chart instances
let categoryChart = null;
let trendChart = null;

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('BudgetWise AI initialized');
    
    // Handle form submission only if the form exists
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Initialize other components if they exist
    initializeComponents();
});

/**
 * Initialize page components
 */
function initializeComponents() {
    // Check if we're on a page with specific components
    const csvFile = document.getElementById('csvFile');
    const categoryChartCanvas = document.getElementById('categoryChart');
    const trendChartCanvas = document.getElementById('trendChart');
    
    // Only initialize if elements exist
    if (csvFile) {
        console.log('CSV upload component found');
    }
    
    if (categoryChartCanvas) {
        console.log('Category chart canvas found');
    }
    
    if (trendChartCanvas) {
        console.log('Trend chart canvas found');
    }
}

/**
 * Handle CSV file upload form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Get form elements
    const fileInput = document.getElementById('csvFile');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorAlert = document.getElementById('errorAlert');
    const resultsSection = document.getElementById('resultsSection');
    
    // Validate file selection
    if (!fileInput.files || fileInput.files.length === 0) {
        showError('Please select a CSV file to upload');
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    // Show loading state
    loadingSpinner.style.display = 'block';
    errorAlert.style.display = 'none';
    resultsSection.style.display = 'none';
    
    try {
        // Send file to backend
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        
        // Parse response
        const data = await response.json();
        
        // Hide loading spinner
        loadingSpinner.style.display = 'none';
        
        if (response.ok && data.success) {
            // Process and display results
            displayResults(data);
            resultsSection.style.display = 'block';
            
            // Smooth scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            showError(data.error || 'Failed to process file');
        }
        
    } catch (error) {
        console.error('Error uploading file:', error);
        loadingSpinner.style.display = 'none';
        showError('Network error. Please check your connection and try again.');
    }
}

/**
 * Display error message
 */
function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message;
    errorAlert.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorAlert.style.display = 'none';
    }, 5000);
}

/**
 * Display analysis results
 */
function displayResults(data) {
    console.log('Displaying results:', data);
    
    // Update summary cards
    updateSummaryCards(data);
    
    // Render charts
    renderCategoryChart(data.current_month.categories);
    renderTrendChart(data.historical, data.forecast);
    
    // Display insights
    displayInsights(data.insights);
}

/**
 * Update summary cards with data
 */
function updateSummaryCards(data) {
    // Current month total
    document.getElementById('currentTotal').textContent = 
        `₹${data.current_month.total_spending.toLocaleString('en-IN')}`;
    
    // Predicted total
    document.getElementById('predictedTotal').textContent = 
        `₹${data.forecast.estimated_total.toLocaleString('en-IN')}`;
    
    // Transaction count
    document.getElementById('transactionCount').textContent = 
        data.current_month.transaction_count;
    
    // Top category
    const categories = data.current_month.categories;
    const topCategory = Object.keys(categories).reduce((a, b) => 
        categories[a] > categories[b] ? a : b
    );
    document.getElementById('topCategory').textContent = topCategory;
}

/**
 * Render category breakdown pie chart
 */
function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    // Prepare data
    const labels = Object.keys(categories);
    const data = Object.values(categories);
    
    // Indian-themed colors
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
        '#4BC0C0', '#FF6384'
    ];
    
    // Create new chart
    categoryChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ₹${value.toLocaleString('en-IN')} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render spending trend and forecast line chart
 */
function renderTrendChart(historical, forecast) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (trendChart) {
        trendChart.destroy();
    }
    
    // Combine historical and forecast dates
    const allDates = [...historical.dates, ...forecast.dates];
    
    // Prepare datasets
    const historicalData = historical.amounts;
    const forecastData = new Array(historical.dates.length).fill(null)
        .concat(forecast.next_30_days);
    
    // Create chart
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: [
                {
                    label: 'Historical Spending',
                    data: historicalData.concat(new Array(forecast.dates.length).fill(null)),
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'AI Forecast',
                    data: forecastData,
                    borderColor: '#FF6384',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (context.parsed.y !== null) {
                                label += `: ₹${context.parsed.y.toLocaleString('en-IN')}`;
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Amount (₹)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    }
                }
            }
        }
    });
}

/**
 * Display AI-generated insights
 */
function displayInsights(insights) {
    const insightsList = document.getElementById('insightsList');
    insightsList.innerHTML = '';
    
    if (!insights || insights.length === 0) {
        insightsList.innerHTML = '<p class="text-muted">No insights available</p>';
        return;
    }
    
    insights.forEach(insight => {
        // Determine alert class based on insight type
        let alertClass = 'alert-info';
        let iconClass = 'bi-info-circle';
        
        if (insight.type === 'warning') {
            alertClass = 'alert-warning';
            iconClass = 'bi-exclamation-triangle';
        } else if (insight.type === 'success') {
            alertClass = 'alert-success';
            iconClass = 'bi-check-circle';
        }
        
        // Create insight element
        const insightElement = document.createElement('div');
        insightElement.className = `alert ${alertClass} d-flex align-items-center`;
        insightElement.innerHTML = `
            <i class="bi ${iconClass} me-2"></i>
            <span>${insight.message}</span>
        `;
        
        insightsList.appendChild(insightElement);
    });
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short'
    });
}

/**
 * Export results as PDF (future enhancement)
 */
function exportResults() {
    // Placeholder for PDF export functionality
    alert('PDF export feature coming soon!');
}