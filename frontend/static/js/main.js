// Main application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
    
    // Handle form submissions with loading state
    document.querySelectorAll('form[data-loading]').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            }
        });
    });
    
    // Product search with debounce
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = this.value.trim();
                if (query.length > 2) {
                    performSearch(query);
                }
            }, 300);
        });
    }
});

function performSearch(query) {
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.results) {
                // Update UI with search results
                updateSearchResults(data.results);
            }
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

function updateSearchResults(results) {
    const container = document.getElementById('searchResults');
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No results found</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    results.forEach(product => {
        html += `
            <a href="/product/${product.id}" class="list-group-item list-group-item-action">
                <div class="d-flex justify-content-between">
                    <strong>${product.title}</strong>
                    <span class="text-primary">$${product.price}</span>
                </div>
                <small class="text-muted">${product.category}</small>
            </a>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

// Utility function for time ago
function timeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return interval + ' ' + unit + (interval === 1 ? '' : 's') + ' ago';
        }
    }
    return 'just now';
}

// Make timeAgo available to templates
window.timeAgo = timeAgo;

// Theme toggle (optional)
let isDarkMode = localStorage.getItem('darkMode') === 'true';

function toggleTheme() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark-mode', isDarkMode);
    localStorage.setItem('darkMode', isDarkMode);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Dark mode toggle availability
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        updateThemeIcon();
    }
});

// Handle recommendation refresh with animation
function refreshRecommendations() {
    const btn = document.querySelector('.refresh-recommendations');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Refreshing...';
        
        fetch('/api/refresh-recommendations', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to refresh recommendations');
            }
        })
        .catch(error => {
            alert('Error refreshing recommendations');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Refresh';
        });
    }
}

// Handle product filter
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const category = this.dataset.category;
        const url = category ? `/products?category=${category}` : '/products';
        window.location.href = url;
    });
});

// Add to cart animation
function addToCart(productId) {
    const btn = event.target.closest('button');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adding...';
        
        fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ product_id: productId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                btn.innerHTML = '<i class="fas fa-check me-2"></i>Added!';
                setTimeout(() => {
                    btn.innerHTML = '<i class="fas fa-shopping-cart me-2"></i>Add to Cart';
                    btn.disabled = false;
                }, 2000);
            } else {
                btn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error';
                setTimeout(() => {
                    btn.innerHTML = '<i class="fas fa-shopping-cart me-2"></i>Add to Cart';
                    btn.disabled = false;
                }, 2000);
            }
        })
        .catch(error => {
            btn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error';
            setTimeout(() => {
                btn.innerHTML = '<i class="fas fa-shopping-cart me-2"></i>Add to Cart';
                btn.disabled = false;
            }, 2000);
        });
    }
}