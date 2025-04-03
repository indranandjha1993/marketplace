/**
 * Marketplace Utility Functions
 * A comprehensive set of utility functions for the marketplace application
 *
 * @version 1.0.0
 */

const MarketplaceUtils = (function() {
    'use strict';

    /**
     * Cookie and Authentication Utilities
     */
    const cookies = {
        /**
         * Get CSRF token from cookies
         * @returns {string|null} CSRF token or null if not found
         */
        getCsrfToken: function() {
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
        },

        /**
         * Get any cookie by name
         * @param {string} name - Cookie name
         * @returns {string|null} Cookie value or null if not found
         */
        getCookie: function(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        /**
         * Set a cookie
         * @param {string} name - Cookie name
         * @param {string} value - Cookie value
         * @param {number} days - Days until expiration
         */
        setCookie: function(name, value, days) {
            let expires = '';
            if (days) {
                const date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                expires = '; expires=' + date.toUTCString();
            }
            document.cookie = name + '=' + encodeURIComponent(value) + expires + '; path=/';
        }
    };

    /**
     * Formatting Utilities
     */
    const formatters = {
        /**
         * Format currency
         * @param {number} amount - Amount to format
         * @param {string} currencySymbol - Currency symbol
         * @returns {string} Formatted currency string
         */
        formatCurrency: function(amount, currencySymbol = '₹') {
            return `${currencySymbol}${parseFloat(amount).toFixed(2)}`;
        },

        /**
         * Format date
         * @param {string|Date} dateString - Date to format
         * @param {Object} options - Intl.DateTimeFormat options
         * @returns {string} Formatted date string
         */
        formatDate: function(dateString, options = { year: 'numeric', month: 'long', day: 'numeric' }) {
            return new Date(dateString).toLocaleDateString(undefined, options);
        },

        /**
         * Format relative time (e.g., "2 hours ago")
         * @param {string|Date} dateString - Date to format
         * @returns {string} Relative time string
         */
        formatRelativeTime: function(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);

            if (diffInSeconds < 60) {
                return 'just now';
            }

            const diffInMinutes = Math.floor(diffInSeconds / 60);
            if (diffInMinutes < 60) {
                return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
            }

            const diffInHours = Math.floor(diffInMinutes / 60);
            if (diffInHours < 24) {
                return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
            }

            const diffInDays = Math.floor(diffInHours / 24);
            if (diffInDays < 30) {
                return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
            }

            const diffInMonths = Math.floor(diffInDays / 30);
            if (diffInMonths < 12) {
                return `${diffInMonths} month${diffInMonths > 1 ? 's' : ''} ago`;
            }

            const diffInYears = Math.floor(diffInMonths / 12);
            return `${diffInYears} year${diffInYears > 1 ? 's' : ''} ago`;
        },

        /**
         * Truncate text with ellipsis
         * @param {string} text - Text to truncate
         * @param {number} maxLength - Maximum length
         * @returns {string} Truncated text
         */
        truncateText: function(text, maxLength) {
            if (!text || text.length <= maxLength) return text;
            return text.substr(0, maxLength) + '...';
        }
    };

    /**
     * Validation Utilities
     */
    const validators = {
        /**
         * Validate email
         * @param {string} email - Email to validate
         * @returns {boolean} Whether email is valid
         */
        isValidEmail: function(email) {
            const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
            return re.test(String(email).toLowerCase());
        },

        /**
         * Validate phone number
         * @param {string} phone - Phone number to validate
         * @returns {boolean} Whether phone number is valid
         */
        isValidPhone: function(phone) {
            const re = /^\d{10}$/;
            return re.test(String(phone));
        },

        /**
         * Validate password strength
         * @param {string} password - Password to validate
         * @returns {boolean} Whether password is strong
         */
        isStrongPassword: function(password) {
            // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
            const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/;
            return re.test(String(password));
        }
    };

    /**
     * URL and Navigation Utilities
     */
    const url = {
        /**
         * Get URL parameters as an object
         * @returns {Object} URL parameters
         */
        getUrlParams: function() {
            const params = {};
            const queryString = window.location.search.substring(1);
            if (!queryString) return params;

            const pairs = queryString.split('&');
            for (let i = 0; i < pairs.length; i++) {
                const pair = pairs[i].split('=');
                if (pair[0]) {
                    params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
                }
            }

            return params;
        },

        /**
         * Set URL parameter without page reload
         * @param {string} key - Parameter key
         * @param {string} value - Parameter value
         */
        setUrlParam: function(key, value) {
            const url = new URL(window.location.href);
            url.searchParams.set(key, value);
            window.history.replaceState({}, '', url.toString());
        },

        /**
         * Remove URL parameter without page reload
         * @param {string} key - Parameter key to remove
         */
        removeUrlParam: function(key) {
            const url = new URL(window.location.href);
            url.searchParams.delete(key);
            window.history.replaceState({}, '', url.toString());
        },

        /**
         * Update multiple URL parameters at once
         * @param {Object} params - Parameters to update
         */
        updateUrlParams: function(params) {
            const url = new URL(window.location.href);

            // Remove parameters with null or undefined values
            Object.keys(params).forEach(key => {
                if (params[key] === null || params[key] === undefined) {
                    url.searchParams.delete(key);
                } else {
                    url.searchParams.set(key, params[key]);
                }
            });

            window.history.replaceState({}, '', url.toString());
        }
    };

    /**
     * UI Utilities
     */
    const ui = {
        /**
         * Show toast notification
         * @param {string} message - Message to display
         * @param {string} type - Notification type (success, error, info, warning)
         * @param {number} duration - Duration in milliseconds
         */
        showToast: function(message, type = 'info', duration = 3000) {
            if (window.djangoToast) {
                window.djangoToast[type](message);
            } else {
                // Fallback toast implementation
                const toast = document.createElement('div');
                toast.className = `toast toast-${type}`;
                toast.textContent = message;

                const container = document.querySelector('.toast-container') || (() => {
                    const newContainer = document.createElement('div');
                    newContainer.className = 'toast-container';
                    document.body.appendChild(newContainer);
                    return newContainer;
                })();

                container.appendChild(toast);

                // Trigger reflow to enable transition
                toast.offsetHeight;

                // Show toast
                toast.classList.add('show');

                // Auto-remove after duration
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => {
                        container.removeChild(toast);
                        if (container.children.length === 0) {
                            document.body.removeChild(container);
                        }
                    }, 300); // Match transition duration
                }, duration);
            }
        },

        /**
         * Debounce function for search inputs and other frequent events
         * @param {Function} func - Function to debounce
         * @param {number} wait - Wait time in milliseconds
         * @returns {Function} Debounced function
         */
        debounce: function(func, wait = 300) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Throttle function for scroll and resize events
         * @param {Function} func - Function to throttle
         * @param {number} limit - Limit in milliseconds
         * @returns {Function} Throttled function
         */
        throttle: function(func, limit = 300) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    };

    /**
     * API Utilities
     */
    const api = {
        /**
         * Make a fetch request with CSRF token
         * @param {string} url - API endpoint
         * @param {Object} options - Fetch options
         * @returns {Promise} Fetch promise
         */
        fetchWithAuth: function(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': cookies.getCsrfToken()
                }
            };

            const mergedOptions = {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers
                }
            };

            return fetch(url, mergedOptions)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                });
        },

        /**
         * Add product to cart
         * @param {number} productId - Product ID
         * @param {number} quantity - Quantity
         * @param {number|null} variantId - Variant ID (optional)
         * @returns {Promise} API response
         */
        addToCart: function(productId, quantity = 1, variantId = null) {
            return this.fetchWithAuth('/cart/add/', {
                method: 'POST',
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity,
                    variant_id: variantId
                })
            });
        },

        /**
         * Toggle product in wishlist
         * @param {number} productId - Product ID
         * @returns {Promise} API response
         */
        toggleWishlist: function(productId) {
            return this.fetchWithAuth('/accounts/wishlist/toggle/', {
                method: 'POST',
                body: JSON.stringify({
                    product_id: productId
                })
            });
        }
    };

    // Public API
    return {
        // Cookie utilities
        getCsrfToken: cookies.getCsrfToken,
        getCookie: cookies.getCookie,
        setCookie: cookies.setCookie,

        // Formatting utilities
        formatCurrency: formatters.formatCurrency,
        formatDate: formatters.formatDate,
        formatRelativeTime: formatters.formatRelativeTime,
        truncateText: formatters.truncateText,

        // Validation utilities
        isValidEmail: validators.isValidEmail,
        isValidPhone: validators.isValidPhone,
        isStrongPassword: validators.isStrongPassword,

        // URL utilities
        getUrlParams: url.getUrlParams,
        setUrlParam: url.setUrlParam,
        removeUrlParam: url.removeUrlParam,
        updateUrlParams: url.updateUrlParams,

        // UI utilities
        showToast: ui.showToast,
        debounce: ui.debounce,
        throttle: ui.throttle,

        // API utilities
        fetchWithAuth: api.fetchWithAuth,
        addToCart: api.addToCart.bind(api),
        toggleWishlist: api.toggleWishlist.bind(api)
    };
})();

// Export to global scope
window.marketplaceUtils = MarketplaceUtils;