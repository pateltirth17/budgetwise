/**
 * BudgetWise AI - Premium Dashboard JavaScript
 * Complete rewrite with all fixes for dropdown, upload, categories, navigation, and mobile responsiveness
 */

// Global variables
window.categoryChart = null;
window.trendChart = null;
let isChartsInitialized = false;
let currentPage = 'overview';
let sidebarActive = false;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Initialize core features
    initializePageDetection();
    initializeMobileSidebar();
    
    // Small delay to ensure DOM is fully ready
    setTimeout(() => {
        setupNavigationHandlers();
        setupEventListeners();
    }, 100);
    
    initializeCharts();
    loadDashboardData();
    fixDropdownMenus();
    setupUploadCSV();
    applyCategoryColors();
    loadSettings();
    handleResponsiveFeatures();
});

// NEW: Initialize Mobile Sidebar
function initializeMobileSidebar() {
    // Create mobile menu toggle button if it doesn't exist
    if (!document.querySelector('.mobile-menu-toggle')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'mobile-menu-toggle';
        toggleBtn.innerHTML = `
            <div class="menu-icon">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        document.body.appendChild(toggleBtn);
    }
    
    // Create overlay if it doesn't exist
    if (!document.querySelector('.sidebar-overlay')) {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }
    
    // Add close button to sidebar if it doesn't exist
    const sidebar = document.querySelector('.sidebar');
    if (sidebar && !sidebar.querySelector('.sidebar-close')) {
        const closeBtn = document.createElement('button');
        closeBtn.className = 'sidebar-close';
        closeBtn.innerHTML = '<i class="bi bi-x"></i>';
        const sidebarHeader = sidebar.querySelector('.sidebar-header');
        if (sidebarHeader) {
            sidebarHeader.appendChild(closeBtn);
        }
    }
    
    // Setup mobile sidebar events
    setupMobileSidebarEvents();
}

// Update the setupMobileSidebarEvents function - replace it with this improved version:
function setupMobileSidebarEvents() {
    const sidebar = document.querySelector('.sidebar');
    const toggleButton = document.querySelector('.mobile-menu-toggle');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    const sidebarClose = document.querySelector('.sidebar-close');
    
    // Toggle sidebar function
    window.toggleSidebar = function() {
        if (!sidebar) return;
        
        sidebarActive = !sidebarActive;
        sidebar.classList.toggle('active');
        if (sidebarOverlay) sidebarOverlay.classList.toggle('active');
        if (toggleButton) toggleButton.classList.toggle('active');
        
        // Prevent body scroll when sidebar is open
        if (sidebarActive) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
    
    // Close sidebar function
    window.closeSidebar = function() {
        if (!sidebar) return;
        
        sidebarActive = false;
        sidebar.classList.remove('active');
        if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        if (toggleButton) toggleButton.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // Event listeners
    if (toggleButton) {
        toggleButton.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSidebar();
        });
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function(e) {
            e.stopPropagation();
            closeSidebar();
        });
    }
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', function(e) {
            e.stopPropagation();
            closeSidebar();
        });
    }
    
    // Handle escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebarActive) {
            closeSidebar();
        }
    });
    
    // Setup swipe gestures
    setupSwipeGestures(sidebar, toggleSidebar, closeSidebar);
}

// NEW: Setup Swipe Gestures for Mobile
function setupSwipeGestures(sidebar, toggleSidebar, closeSidebar) {
    let touchStartX = 0;
    let touchEndX = 0;
    let touchStartY = 0;
    let touchEndY = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    });
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    });
    
    function handleSwipe() {
        const swipeDistanceX = Math.abs(touchEndX - touchStartX);
        const swipeDistanceY = Math.abs(touchEndY - touchStartY);
        
        // Only process horizontal swipes
        if (swipeDistanceX > swipeDistanceY) {
            // Swipe left to close
            if (touchStartX - touchEndX > 50 && sidebarActive) {
                closeSidebar();
            }
            // Swipe right to open (only from left edge)
            if (touchEndX - touchStartX > 50 && touchStartX < 20 && !sidebarActive) {
                toggleSidebar();
            }
        }
    }
}

// NEW: Handle Responsive Features
function handleResponsiveFeatures() {
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            const width = window.innerWidth;
            
            // Close sidebar on desktop resize
            if (width > 768 && sidebarActive) {
                const sidebar = document.querySelector('.sidebar');
                const sidebarOverlay = document.querySelector('.sidebar-overlay');
                const toggleButton = document.querySelector('.mobile-menu-toggle');
                
                if (sidebar) sidebar.classList.remove('active');
                if (sidebarOverlay) sidebarOverlay.classList.remove('active');
                if (toggleButton) toggleButton.classList.remove('active');
                document.body.style.overflow = '';
                sidebarActive = false;
            }
            
            // Reinitialize charts on resize for better responsiveness
            if (width < 768) {
                if (window.categoryChart) {
                    window.categoryChart.resize();
                }
                if (window.trendChart) {
                    window.trendChart.resize();
                }
            }
            
            // Adjust button sizes on mobile
            adjustMobileButtons(width);
        }, 250);
    });
    
    // Initial adjustment
    adjustMobileButtons(window.innerWidth);
}

// NEW: Adjust Mobile Buttons
function adjustMobileButtons(width) {
    if (width <= 768) {
        // Make buttons more touch-friendly on mobile
        document.querySelectorAll('.btn').forEach(btn => {
            if (!btn.classList.contains('mobile-optimized')) {
                btn.classList.add('mobile-optimized');
                btn.style.minHeight = '44px'; // iOS touch target size
                btn.style.minWidth = '44px';
            }
        });
        
        // Adjust page actions for mobile
        const pageActions = document.querySelector('.page-actions');
        if (pageActions) {
            pageActions.style.flexDirection = 'column';
            pageActions.style.width = '100%';
        }
    } else {
        // Reset button sizes on desktop
        document.querySelectorAll('.btn.mobile-optimized').forEach(btn => {
            btn.classList.remove('mobile-optimized');
            btn.style.minHeight = '';
            btn.style.minWidth = '';
        });
        
        const pageActions = document.querySelector('.page-actions');
        if (pageActions) {
            pageActions.style.flexDirection = '';
            pageActions.style.width = '';
        }
    }
}

// Page Detection and Control
function initializePageDetection() {
    const currentPath = window.location.pathname;
    const body = document.body;
    
    // Detect current page
    if (currentPath.includes('overview') || currentPath.includes('dashboard') || currentPath === '/' || currentPath === '/dashboard') {
        currentPage = 'overview';
        body.setAttribute('data-page', 'overview');
    } else if (currentPath.includes('transaction')) {
        currentPage = 'transactions';
        body.setAttribute('data-page', 'transactions');
    } else if (currentPath.includes('budget')) {
        currentPage = 'budget';
        body.setAttribute('data-page', 'budget');
    } else if (currentPath.includes('settings')) {
        currentPage = 'settings';
        body.setAttribute('data-page', 'settings');
    } else if (currentPath.includes('reports')) {
        currentPage = 'reports';
        body.setAttribute('data-page', 'reports');
    } else if (currentPath.includes('profile')) {
        currentPage = 'profile';
        body.setAttribute('data-page', 'profile');
    }
    
    // Control Upload CSV button visibility
    controlUploadButtonVisibility();
}

// Control Upload Button Visibility
function controlUploadButtonVisibility() {
    const uploadBtn = document.querySelector('.upload-csv-btn');
    if (!uploadBtn) return;
    
    // Show only on overview and transactions pages
    if (currentPage === 'overview' || currentPage === 'transactions') {
        uploadBtn.style.display = 'inline-block';
    } else {
        uploadBtn.style.display = 'none';
    }
}

// FIX: Dropdown Menu Z-Index and Positioning (Enhanced for Mobile)
function fixDropdownMenus() {
    // Fix all dropdown toggles
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Close other dropdowns
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                if (menu !== this.nextElementSibling) {
                    menu.classList.remove('show');
                    menu.style.display = 'none';
                }
            });
            
            setTimeout(() => {
                const menu = this.nextElementSibling;
                if (menu && menu.classList.contains('dropdown-menu')) {
                    // Get button position
                    const rect = this.getBoundingClientRect();
                    const isMobile = window.innerWidth <= 768;
                    
                    // Adjust positioning for mobile
                    if (isMobile) {
                        menu.style.cssText = `
                            position: fixed !important;
                            z-index: 2147483647 !important;
                            top: ${rect.bottom + 5}px !important;
                            right: 10px !important;
                            left: 10px !important;
                            width: auto !important;
                            display: block !important;
                            background: white !important;
                            border-radius: 12px !important;
                            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2) !important;
                            padding: 8px !important;
                            max-height: 70vh !important;
                            overflow-y: auto !important;
                        `;
                    } else {
                        menu.style.cssText = `
                            position: fixed !important;
                            z-index: 2147483647 !important;
                            top: ${rect.bottom + 5}px !important;
                            right: ${window.innerWidth - rect.right}px !important;
                            left: auto !important;
                            display: block !important;
                            background: white !important;
                            border-radius: 12px !important;
                            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2) !important;
                            padding: 8px !important;
                        `;
                    }
                }
            }, 10);
        });
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
                menu.style.display = 'none';
            });
        }
    });
}

// FIX: Upload CSV Functionality
function setupUploadCSV() {
    // Ensure upload modal works properly
    const uploadModal = document.getElementById('uploadModal') || document.getElementById('csvUploadModal');
    
    if (uploadModal) {
        uploadModal.addEventListener('show.bs.modal', function() {
            // Fix modal backdrop
            setTimeout(() => {
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.style.pointerEvents = 'none';
                    backdrop.style.opacity = '0.3';
                }
                
                // Make modal fully interactive
                this.style.pointerEvents = 'all';
                
                // Fix file input
                const fileInput = this.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.style.pointerEvents = 'all';
                    fileInput.style.cursor = 'pointer';
                    
                    // Ensure file input is clickable
                    fileInput.addEventListener('click', function(e) {
                        e.stopPropagation();
                    });
                }
            }, 100);
        });
    }
}

// Enhanced Upload File Function
async function uploadFile() {
    const fileInput = document.getElementById('csvFile') || document.querySelector('input[type="file"]');
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadResult = document.getElementById('uploadResult');
    const uploadBtn = document.querySelector('#uploadModal .btn-primary, #csvUploadModal .btn-primary');
    
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showAlert('warning', 'Please select a CSV file to upload');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showAlert('warning', 'Please select a valid CSV file');
        return;
    }
    
    // Show progress
    if (uploadProgress) {
        uploadProgress.style.display = 'block';
        uploadProgress.innerHTML = '<div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 50%"></div></div>';
    }
    
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (uploadProgress) uploadProgress.style.display = 'none';
        
        if (data.success) {
            if (uploadResult) {
                uploadResult.style.display = 'block';
                uploadResult.className = 'alert alert-success';
                uploadResult.innerHTML = `
                    <i class="bi bi-check-circle"></i> 
                    <strong>Success!</strong> ${data.message || 'File uploaded successfully'}
                    <br><small>Processed ${data.count || 0} transactions</small>
                `;
            }
            
            showAlert('success', 'CSV file uploaded successfully!');
            
            // Close modal and reload after 2 seconds
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(uploadModal);
                if (modal) modal.hide();
                location.reload();
            }, 2000);
        } else {
            if (uploadResult) {
                uploadResult.style.display = 'block';
                uploadResult.className = 'alert alert-danger';
                uploadResult.innerHTML = `<i class="bi bi-x-circle"></i> ${data.error || 'Upload failed'}`;
            }
            showAlert('danger', data.error || 'Failed to upload file');
        }
    } catch (error) {
        console.error('Upload error:', error);
        if (uploadProgress) uploadProgress.style.display = 'none';
        if (uploadResult) {
            uploadResult.style.display = 'block';
            uploadResult.className = 'alert alert-danger';
            uploadResult.innerHTML = `<i class="bi bi-x-circle"></i> Network error: ${error.message}`;
        }
        showAlert('danger', 'Network error occurred');
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="bi bi-upload"></i> Upload';
        }
    }
}

// FIX: Apply Category Colors
function applyCategoryColors() {
    // Category color mapping
    const categoryColors = {
        'food-dining': { bg: 'linear-gradient(135deg, #FB923C, #EA580C)', icon: '🍔' },
        'food': { bg: 'linear-gradient(135deg, #FB923C, #EA580C)', icon: '🍔' },
        'dining': { bg: 'linear-gradient(135deg, #FB923C, #EA580C)', icon: '🍔' },
        'transportation': { bg: 'linear-gradient(135deg, #3B82F6, #1D4ED8)', icon: '🚗' },
        'transport': { bg: 'linear-gradient(135deg, #3B82F6, #1D4ED8)', icon: '🚗' },
        'shopping': { bg: 'linear-gradient(135deg, #EC4899, #BE185D)', icon: '🛍️' },
        'healthcare': { bg: 'linear-gradient(135deg, #EF4444, #B91C1C)', icon: '🏥' },
        'health': { bg: 'linear-gradient(135deg, #EF4444, #B91C1C)', icon: '🏥' },
        'utilities': { bg: 'linear-gradient(135deg, #FCD34D, #F59E0B)', icon: '💡' },
        'entertainment': { bg: 'linear-gradient(135deg, #A855F7, #7C3AED)', icon: '🎬' },
        'education': { bg: 'linear-gradient(135deg, #6366F1, #4338CA)', icon: '📚' },
        'groceries': { bg: 'linear-gradient(135deg, #10B981, #047857)', icon: '🛒' },
        'insurance': { bg: 'linear-gradient(135deg, #14B8A6, #0F766E)', icon: '🛡️' },
        'investment': { bg: 'linear-gradient(135deg, #1E40AF, #1E3A8A)', icon: '📈' },
        'rent': { bg: 'linear-gradient(135deg, #92400E, #78350F)', icon: '🏠' },
        'personal': { bg: 'linear-gradient(135deg, #FB7185, #E11D48)', icon: '💅' },
        'gifts': { bg: 'linear-gradient(135deg, #8B5CF6, #6D28D9)', icon: '🎁' },
        'other': { bg: 'linear-gradient(135deg, #6B7280, #374151)', icon: '📌' },
        'salary': { bg: 'linear-gradient(135deg, #22C55E, #15803D)', icon: '💰' }
    };
    
    // Apply colors to category badges
    document.querySelectorAll('.category-badge').forEach(badge => {
        const categoryClass = Array.from(badge.classList).find(c => c.startsWith('category-'));
        if (categoryClass) {
            const category = categoryClass.replace('category-', '').toLowerCase();
            const colorConfig = categoryColors[category];
            
            if (colorConfig) {
                badge.style.background = colorConfig.bg;
                badge.style.color = 'white';
                badge.style.border = 'none';
                badge.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
                
                // Add icon if not present
                if (!badge.innerHTML.includes(colorConfig.icon)) {
                    badge.innerHTML = colorConfig.icon + ' ' + badge.innerHTML;
                }
            }
        }
    });
}

/**
 * BudgetWise AI - Premium Dashboard JavaScript
 * Fixed Navigation Issues
 */

// Replace the existing setupNavigationHandlers() function with this:
function setupNavigationHandlers() {
    // Get all navigation items
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        // Remove any existing listeners first
        item.replaceWith(item.cloneNode(true));
    });
    
    // Re-select after cloning
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            // Check if this is an actual link with href
            const href = this.getAttribute('href');
            
            // If it has a real href and not just #, navigate to it
            if (href && href !== '#' && !href.startsWith('javascript:')) {
                // Don't prevent default for real navigation links
                window.location.href = href;
                return;
            }
            
            // Only prevent default for JavaScript-handled navigation
            if (this.hasAttribute('data-page')) {
                e.preventDefault();
                handlePageNavigation(this);
            }
        });
    });
}

// Add this new function to handle page navigation
function handlePageNavigation(navItem) {
    const targetPage = navItem.dataset.page;
    
    if (!targetPage) {
        // If no data-page attribute, try to get from href
        const href = navItem.getAttribute('href');
        if (href && href !== '#') {
            window.location.href = href;
            return;
        }
    }
    
    // Update active nav
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    navItem.classList.add('active');
    
    // Update current page
    currentPage = targetPage;
    document.body.setAttribute('data-page', currentPage);
    
    // Control upload button visibility
    controlUploadButtonVisibility();
    
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
        page.style.display = 'none';
    });
    
    // Show selected page
    const pageElement = document.getElementById(currentPage + '-page');
    if (pageElement) {
        pageElement.classList.add('active');
        pageElement.style.display = 'block';
    }
    
    // Update page title
    const pageTitle = document.getElementById('pageTitle');
    if (pageTitle) {
        const spanText = navItem.querySelector('span')?.textContent;
        pageTitle.textContent = spanText || navItem.textContent.trim();
    }
    
    // Load page-specific data
    loadPageData(currentPage);
    
    // Reapply category colors after page change
    setTimeout(applyCategoryColors, 100);
    
    // Close mobile sidebar if open
    if (window.innerWidth <= 768 && sidebarActive) {
        setTimeout(() => {
            closeSidebar();
        }, 250);
    }
}


// Load page-specific data
function loadPageData(page) {
    switch(page) {
        case 'overview':
            loadDashboardData();
            break;
        case 'transactions':
            loadTransactionsData();
            break;
        case 'predictions':
            loadPredictionsPage();
            break;
        case 'budget':
            loadBudgetData();
            break;
        case 'reports':
            loadReportsPage();
            break;
    }
}

// Setup event listeners (Enhanced for mobile)
function setupEventListeners() {
    // Period selector buttons
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            loadDashboardData(this.dataset.period);
        });
    });
    
    // Settings save button
    const saveSettingsBtn = document.getElementById('saveSettings');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', saveSettings);
    }
    
    // Apply filters button
    const applyFiltersBtn = document.getElementById('applyFilters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyTransactionFilters);
    }
    
    // Add Transaction button style fix
    document.querySelectorAll('.btn-success').forEach(btn => {
        if (btn.textContent.includes('Add Transaction')) {
            btn.className = 'btn btn-primary';
            btn.style.cssText = `
                background: linear-gradient(135deg, #8B7AA8, #B8A9D3) !important;
                border: none !important;
                border-radius: 50px !important;
                padding: 8px 20px !important;
                font-weight: 600 !important;
            `;
        }
    });
    
    // Handle touch events for better mobile interaction
    if ('ontouchstart' in window) {
        document.querySelectorAll('.btn, .nav-item').forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.opacity = '0.7';
            });
            element.addEventListener('touchend', function() {
                this.style.opacity = '1';
            });
        });
    }
}

// Indian number formatting
function formatIndianCurrency(num) {
    if (num === null || num === undefined) return '₹0';
    
    const absNum = Math.abs(num);
    let result;
    
    if (absNum >= 10000000) {
        result = '₹' + (absNum / 10000000).toFixed(2) + ' Cr';
    } else if (absNum >= 100000) {
        result = '₹' + (absNum / 100000).toFixed(2) + ' L';
    } else if (absNum >= 1000) {
        result = '₹' + (absNum / 1000).toFixed(1) + 'K';
    } else {
        result = '₹' + absNum.toFixed(0);
    }
    
    return num < 0 ? '-' + result : result;
}

// Initialize charts with purple theme (Enhanced for mobile)
function initializeCharts() {
    // Responsive chart options for mobile
    const isMobile = window.innerWidth <= 768;
    
    // Category Chart
    const categoryCanvas = document.getElementById('categoryChart');
    if (categoryCanvas) {
        const ctx = categoryCanvas.getContext('2d');
        
        window.categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                            '#FF0000', '#FF8000', '#FFBF00',
                            '#FFFF00', '#BFFF00', '#00FF00',
                            '#00BF80', '#00aaffff', '#4000FF',
                            '#8000FF','#BF00FF'

                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: isMobile ? 'bottom' : 'right',
                        labels: {
                            padding: isMobile ? 5 : 10,
                            font: { size: isMobile ? 10 : 11 },
                            color: '#2d3748'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${formatIndianCurrency(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Trend Chart
    const trendCanvas = document.getElementById('trendChart');
    if (trendCanvas) {
        const ctx = trendCanvas.getContext('2d');
        
        window.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Daily Spending',
                    data: [],
                    borderColor: '#8B7AA8',
                    backgroundColor: 'rgba(139, 122, 168, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: isMobile ? 2 : 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        display: !isMobile 
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatIndianCurrency(value);
                            },
                            color: '#4a5568',
                            maxTicksLimit: isMobile ? 5 : 10
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#4a5568',
                            maxRotation: isMobile ? 45 : 0,
                            maxTicksLimit: isMobile ? 7 : 15
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    }
                }
            }
        });
    }
}

// Load dashboard data
async function loadDashboardData(period = 30) {
    try {
        showLoading(true);
        
        const response = await fetch(`/api/dashboard_data?days=${period}`);
        const data = await response.json();
        
        if (data.success) {
            updateDashboardStats(data);
            updateCharts(data);
            applyCategoryColors(); // Apply colors after data load
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showLoading(false);
        // Use dummy data if API fails
        useDummyData();
    }
}

// Use dummy data for testing
function useDummyData() {
    const dummyData = {
        total_spending: 45230,
        transaction_count: 156,
        categories: {
            'Food & Dining': 12500,
            'Transportation': 8900,
            'Shopping': 15600,
            'Healthcare': 3200,
            'Utilities': 5030
        },
        daily_spending: {
            '2024-01-01': 1500,
            '2024-01-02': 2300,
            '2024-01-03': 1800,
            '2024-01-04': 2100,
            '2024-01-05': 1700
        }
    };
    
    updateDashboardStats(dummyData);
    updateCharts(dummyData);
}

// Update dashboard statistics
function updateDashboardStats(data) {
    // Update total spending
    const totalSpending = document.getElementById('totalSpending');
    if (totalSpending) {
        totalSpending.textContent = formatIndianCurrency(data.total_spending || 0);
    }
    
    // Update transaction count
    const transactionCount = document.getElementById('transactionCount');
    if (transactionCount) {
        transactionCount.textContent = data.transaction_count || 0;
    }
    
    // Update savings
    const savingsAmount = document.getElementById('savingsAmount');
    if (savingsAmount) {
        const savings = (data.total_spending || 0) * 0.2;
        savingsAmount.textContent = formatIndianCurrency(savings);
    }
    
    // Update daily average
    const dailyAvg = document.getElementById('dailyAverage');
    if (dailyAvg && data.total_spending) {
        const avg = data.total_spending / 30;
        dailyAvg.textContent = formatIndianCurrency(avg);
    }
}

// Update charts with data
function updateCharts(data) {
    // Update Category Chart
    if (window.categoryChart && data.categories) {
        const labels = Object.keys(data.categories);
        const values = Object.values(data.categories);
        
        if (labels.length > 0) {
            window.categoryChart.data.labels = labels;
            window.categoryChart.data.datasets[0].data = values;
            window.categoryChart.update();
        }
    }
    
    // Update Trend Chart
    if (window.trendChart && data.daily_spending) {
        const dates = Object.keys(data.daily_spending).slice(-30);
        const amounts = dates.map(d => data.daily_spending[d] || 0);
        
        if (dates.length > 0) {
            window.trendChart.data.labels = dates.map(date => {
                const d = new Date(date);
                return `${d.getDate()}/${d.getMonth() + 1}`;
            });
            window.trendChart.data.datasets[0].data = amounts;
            window.trendChart.update();
        }
    }
}

// Load transactions data
async function loadTransactionsData() {
    // Load transactions specific data
    applyCategoryColors();
}

// Load budget data
async function loadBudgetData() {
    // Load budget specific data
}

// Get predictions
async function getPredictions() {
    const btn = event.target;
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating...';
        
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        console.log('Full prediction response:', data); // Debug log
        
        if (data.success && data.predictions) {
            displayPredictions(data.predictions);
            showAlert('success', 'AI predictions generated successfully!');
        } else {
            console.error('Prediction failed:', data);
            showAlert('warning', data.error || 'Could not generate predictions');
        }
    } catch (error) {
        console.error('Prediction error:', error);
        showAlert('danger', 'Failed to generate predictions');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Display predictions
function displayPredictions(predictions) {
    console.log('Displaying predictions:', predictions); // Debug log
    
    // Update prediction page elements
    const predictionTotal = document.getElementById('prediction-total');
    if (predictionTotal) {
        predictionTotal.textContent = formatIndianCurrency(predictions.total_predicted || 0);
    }
    
    const predictionAverage = document.getElementById('prediction-average');
    if (predictionAverage) {
        predictionAverage.textContent = formatIndianCurrency(predictions.daily_average || 0);
    }
    
    const predictionConfidence = document.getElementById('prediction-confidence');
    if (predictionConfidence) {
        const confidence = predictions.confidence || 0;
        predictionConfidence.textContent = `${confidence.toFixed(1)}%`;
    }
    
    const predictionMessage = document.getElementById('prediction-message');
    if (predictionMessage) {
        predictionMessage.innerHTML = `
            <i class="bi bi-check-circle text-success"></i>
            <span class="ms-2">${predictions.message || 'Prediction completed successfully'}</span>
            <br><small class="text-muted mt-1">
                Method: ${predictions.method || 'Statistical'} | 
                Data points: ${predictions.data_points_used || 0} transactions
            </small>
        `;
    }
    
    // Update overview page predicted amount
    const predictedAmount = document.getElementById('predictedAmount');
    if (predictedAmount) {
        predictedAmount.textContent = formatIndianCurrency(predictions.total_predicted || 0);
    }
    
    // Update overview confidence
    const overviewConfidence = document.getElementById('overview-confidence');
    if (overviewConfidence) {
        overviewConfidence.textContent = `${(predictions.confidence || 0).toFixed(1)}%`;
    }
    
    // Update detailed results
    const predictionResults = document.getElementById('predictionResults');
    if (predictionResults) {
        predictionResults.innerHTML = `
            <div class="alert alert-success mt-3" style="border: none; border-radius: 15px;">
                <div class="row">
                    <div class="col-md-8">
                        <h6 class="alert-heading">
                            <i class="bi bi-check-circle"></i> Prediction Generated Successfully
                        </h6>
                        <p class="mb-2">
                            Based on your spending patterns, we predict you'll spend 
                            <strong>${formatIndianCurrency(predictions.total_predicted || 0)}</strong> 
                            over the next 30 days.
                        </p>
                        <small class="text-muted">
                            This prediction uses ${predictions.method === 'lstm' ? 'advanced LSTM neural network' : 'statistical analysis'} 
                            with ${predictions.data_points_used || 0} transaction data points.
                        </small>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="mt-2">
                            <div class="progress mb-2" style="height: 8px;">
                                <div class="progress-bar bg-success" style="width: ${predictions.confidence || 0}%"></div>
                            </div>
                            <small class="text-muted">Confidence: ${(predictions.confidence || 0).toFixed(1)}%</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

// Save settings
async function saveSettings() {
    const currencySelect = document.getElementById('currencyDisplay');
    const dateFormatSelect = document.getElementById('dateFormat');
    const saveButton = document.getElementById('saveSettings');
    
    if (!currencySelect || !dateFormatSelect) {
        showAlert('warning', 'Settings form not found');
        return;
    }
    
    if (saveButton) {
        saveButton.disabled = true;
        saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
    }
    
    const settings = {
        currency: currencySelect.value,
        date_format: dateFormatSelect.value,
        theme: 'light'
    };
    
    try {
        const response = await fetch('/api/save_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            localStorage.setItem('currencyDisplay', settings.currency);
            localStorage.setItem('dateFormat', settings.date_format);
            
            showAlert('success', 'Settings saved successfully!');
            applySettings(settings);
        } else {
            showAlert('danger', data.error || 'Failed to save settings');
        }
    } catch (error) {
        console.error('Save settings error:', error);
        showAlert('danger', 'Error saving settings');
    } finally {
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.innerHTML = '<i class="bi bi-save"></i> Save Settings';
        }
    }
}

// Load settings
async function loadSettings() {
    try {
        const response = await fetch('/api/get_settings');
        const data = await response.json();
        
        if (data.success && data.settings) {
            const currencySelect = document.getElementById('currencyDisplay');
            const dateFormatSelect = document.getElementById('dateFormat');
            
            if (currencySelect && data.settings.currency) {
                currencySelect.value = data.settings.currency;
            }
            
            if (dateFormatSelect && data.settings.date_format) {
                dateFormatSelect.value = data.settings.date_format;
            }
            
            applySettings(data.settings);
        }
    } catch (error) {
        console.error('Load settings error:', error);
    }
}

// Apply settings
function applySettings(settings) {
    window.userSettings = settings;
    console.log('Settings applied:', settings);
}

// Apply transaction filters
function applyTransactionFilters() {
    const category = document.getElementById('filterCategory')?.value || '';
    const dateFrom = document.getElementById('filterDateFrom')?.value || '';
    const dateTo = document.getElementById('filterDateTo')?.value || '';
    
    if (!category && !dateFrom && !dateTo) {
        showAlert('warning', 'Please select at least one filter');
        return;
    }
    
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    showAlert('info', 'Applying filters...');
    window.location.href = `/transactions?${params.toString()}`;
}

// Load predictions page
function loadPredictionsPage() {
    console.log('Loading predictions page');
    // Add predictions specific logic
}

// Load reports page
function loadReportsPage() {
    console.log('Loading reports page');
    // Add reports specific logic
}

// Generate report
async function generateReport() {
    showAlert('info', 'Generating report...');
    window.location.href = '/reports';
}

// Utility functions
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

// Enhanced Alert Function (Mobile Optimized)
function showAlert(type, message) {
    // Remove existing alerts
    document.querySelectorAll('.custom-alert').forEach(alert => alert.remove());
    
    const isMobile = window.innerWidth <= 768;
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed custom-alert`;
    
    // Adjust positioning for mobile
    alertDiv.style.cssText = isMobile ? `
        top: auto;
        bottom: 20px;
        left: 20px;
        right: 20px;
        z-index: 2147483647;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        border: none;
        border-radius: 12px;
        margin: 0;
    ` : `
        top: 20px;
        right: 20px;
        z-index: 2147483647;
        min-width: 300px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        border: none;
        border-radius: 12px;
    `;
    
    // Add icon based on type
    let icon = '';
    switch(type) {
        case 'success': icon = '✅'; break;
        case 'warning': icon = '⚠️'; break;
        case 'danger': icon = '❌'; break;
        case 'info': icon = 'ℹ️'; break;
    }
    
    alertDiv.innerHTML = `
        ${icon} ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Make functions globally available
window.uploadFile = uploadFile;
window.getPredictions = getPredictions;
window.generateReport = generateReport;
window.showAlert = showAlert;
window.saveSettings = saveSettings;
window.applyTransactionFilters = applyTransactionFilters;
window.formatIndianCurrency = formatIndianCurrency;
window.applyCategoryColors = applyCategoryColors;

// Apply colors on any dynamic content load
const observer = new MutationObserver(function(mutations) {
    applyCategoryColors();
});

// Start observing the document for changes
observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log('Dashboard JS loaded successfully with all fixes and mobile support');