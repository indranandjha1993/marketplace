/**
 * Utility functions for the marketplace application
 */

// Get CSRF token from cookies
function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Format currency
function formatCurrency(amount, currencySymbol = '₹') {
    return `${currencySymbol}${parseFloat(amount).toFixed(2)}`;
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Truncate text
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add to cart function
function addToCart(productId, quantity = 1, variantId = null) {
    return fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity,
            variant_id: variantId
        })
    })
    .then(response => response.json());
}

// Toggle wishlist function
function toggleWishlist(productId) {
    return fetch('/accounts/wishlist/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(response => response.json());
}

// Show toast notification
function showToast(message, type = 'info') {
    if (window.djangoToast) {
        window.djangoToast[type](message);
    } else {
        alert(message);
    }
}

// Validate email
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Validate phone number
function isValidPhone(phone) {
    const re = /^\d{10}$/;
    return re.test(String(phone));
}

// Validate password strength
function isStrongPassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/;
    return re.test(String(password));
}

// Get URL parameters
function getUrlParams() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split('&');
    
    for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i].split('=');
        params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
    }
    
    return params;
}

// Set URL parameter
function setUrlParam(key, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    window.history.replaceState({}, '', url.toString());
}

// Remove URL parameter
function removeUrlParam(key) {
    const url = new URL(window.location.href);
    url.searchParams.delete(key);
    window.history.replaceState({}, '', url.toString());
}

// Export all functions
window.marketplaceUtils = {
    getCsrfToken,
    formatCurrency,
    formatDate,
    truncateText,
    debounce,
    addToCart,
    toggleWishlist,
    showToast,
    isValidEmail,
    isValidPhone,
    isStrongPassword,
    getUrlParams,
    setUrlParam,
    removeUrlParam
};