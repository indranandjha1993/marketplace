// Product Listing Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Mobile filter toggle
    const filterToggleBtn = document.getElementById('filter-toggle');
    const filterContainer = document.getElementById('filter-container');
    
    if (filterToggleBtn && filterContainer) {
        filterToggleBtn.addEventListener('click', function() {
            const isExpanded = filterContainer.classList.contains('show');
            
            if (isExpanded) {
                // Hide filters
                filterContainer.style.maxHeight = '0';
                filterContainer.style.opacity = '0';
                filterContainer.style.padding = '0';
                setTimeout(() => {
                    filterContainer.classList.remove('show');
                }, 300);
                this.innerHTML = '<i class="fas fa-filter me-2"></i> Show Filters';
                this.setAttribute('aria-expanded', 'false');
            } else {
                // Show filters
                filterContainer.classList.add('show');
                filterContainer.style.maxHeight = filterContainer.scrollHeight + 'px';
                filterContainer.style.opacity = '1';
                filterContainer.style.padding = '1rem';
                this.innerHTML = '<i class="fas fa-times me-2"></i> Hide Filters';
                this.setAttribute('aria-expanded', 'true');
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 992) {
                // Reset styles for desktop view
                filterContainer.style.maxHeight = '';
                filterContainer.style.opacity = '';
                filterContainer.style.padding = '';
                filterContainer.classList.add('show');
                if (filterToggleBtn) {
                    filterToggleBtn.innerHTML = '<i class="fas fa-filter me-2"></i> Show Filters';
                    filterToggleBtn.setAttribute('aria-expanded', 'false');
                }
            } else if (filterContainer.classList.contains('show')) {
                // Update maxHeight for mobile when filters are shown
                filterContainer.style.maxHeight = filterContainer.scrollHeight + 'px';
            }
        });
    }
    
    // Price range slider
    const priceSlider = document.getElementById('price-range');
    const minPriceInput = document.getElementById('min_price');
    const maxPriceInput = document.getElementById('max_price');
    
    if (priceSlider && minPriceInput && maxPriceInput) {
        // Initialize noUiSlider if available
        if (window.noUiSlider) {
            const minPrice = parseInt(priceSlider.getAttribute('data-min')) || 0;
            const maxPrice = parseInt(priceSlider.getAttribute('data-max')) || 10000;
            const currentMinPrice = parseInt(minPriceInput.value) || minPrice;
            const currentMaxPrice = parseInt(maxPriceInput.value) || maxPrice;
            
            noUiSlider.create(priceSlider, {
                start: [currentMinPrice, currentMaxPrice],
                connect: true,
                step: 100,
                range: {
                    'min': minPrice,
                    'max': maxPrice
                },
                format: {
                    to: function(value) {
                        return Math.round(value);
                    },
                    from: function(value) {
                        return Math.round(value);
                    }
                }
            });
            
            // Update inputs when slider changes
            priceSlider.noUiSlider.on('update', function(values, handle) {
                const value = values[handle];
                
                if (handle === 0) {
                    minPriceInput.value = value;
                } else {
                    maxPriceInput.value = value;
                }
            });
            
            // Update slider when inputs change
            minPriceInput.addEventListener('change', function() {
                priceSlider.noUiSlider.set([this.value, null]);
            });
            
            maxPriceInput.addEventListener('change', function() {
                priceSlider.noUiSlider.set([null, this.value]);
            });
        }
    }
    
    // Handle filter form submission with spinner overlay
    const filterForm = document.getElementById('filter-form');
    const spinnerOverlay = document.getElementById('spinner-overlay');
    
    if (filterForm) {
        filterForm.addEventListener('submit', function() {
            if (spinnerOverlay) {
                spinnerOverlay.classList.add('active');
            }
        });
    }
    
    // Handle sort select change
    const sortSelect = document.getElementById('sort-select');
    
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            // Get current URL and parameters
            const url = new URL(window.location.href);
            const params = url.searchParams;
            
            // Update or add sort parameter
            params.set('sort', this.value);
            
            // Redirect to new URL
            if (spinnerOverlay) {
                spinnerOverlay.classList.add('active');
            }
            
            window.location.href = url.toString();
        });
    }
    
    // Handle clear all filters
    const clearAllBtn = document.getElementById('clear-all-filters');
    
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get base URL without query parameters
            const url = window.location.href.split('?')[0];
            
            // Redirect to base URL
            if (spinnerOverlay) {
                spinnerOverlay.classList.add('active');
            }
            
            window.location.href = url;
        });
    }
    
    // Handle remove filter pill
    const filterPills = document.querySelectorAll('.filter-pill');
    
    filterPills.forEach(pill => {
        const removeBtn = pill.querySelector('.pill-remove');
        
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                const filterType = pill.getAttribute('data-filter-type');
                const filterValue = pill.getAttribute('data-filter-value');
                
                if (filterType && filterValue) {
                    // Get current URL and parameters
                    const url = new URL(window.location.href);
                    const params = url.searchParams;
                    
                    // Handle different filter types
                    if (filterType === 'category') {
                        params.delete('category');
                    } else if (filterType === 'brand') {
                        params.delete('brand');
                    } else if (filterType === 'price') {
                        params.delete('min_price');
                        params.delete('max_price');
                    } else if (filterType === 'rating') {
                        params.delete('rating');
                    } else if (filterType === 'attribute') {
                        // Get current attributes
                        const attrParam = params.get('attrs');
                        if (attrParam) {
                            // Parse attributes
                            const attrs = attrParam.split(',');
                            // Remove the specific attribute
                            const newAttrs = attrs.filter(attr => attr !== filterValue);
                            
                            if (newAttrs.length > 0) {
                                params.set('attrs', newAttrs.join(','));
                            } else {
                                params.delete('attrs');
                            }
                        }
                    } else if (filterType === 'search') {
                        params.delete('q');
                    }
                    
                    // Redirect to new URL
                    if (spinnerOverlay) {
                        spinnerOverlay.classList.add('active');
                    }
                    
                    window.location.href = url.toString();
                }
            });
        }
    });
    
    // Handle infinite scroll if enabled
    const productGrid = document.getElementById('product-grid');
    const loadMoreBtn = document.getElementById('load-more-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    if (productGrid && loadMoreBtn) {
        let page = 2; // Start from page 2 since page 1 is already loaded
        let loading = false;
        
        loadMoreBtn.addEventListener('click', function() {
            if (!loading) {
                loading = true;
                
                // Show loading spinner
                if (loadingSpinner) {
                    loadingSpinner.classList.remove('d-none');
                }
                
                // Hide load more button
                loadMoreBtn.classList.add('d-none');
                
                // Get current URL and parameters
                const url = new URL(window.location.href);
                const params = url.searchParams;
                
                // Set page parameter
                params.set('page', page);
                params.set('ajax', '1'); // Indicate AJAX request
                
                // Fetch next page
                fetch(url.toString())
                    .then(response => response.json())
                    .then(data => {
                        if (data.html) {
                            // Append new products
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = data.html;
                            
                            // Get all product cards from the response
                            const newProducts = tempDiv.querySelectorAll('.product-card-wrapper');
                            
                            // Append each product to the grid
                            newProducts.forEach(product => {
                                productGrid.appendChild(product);
                            });
                            
                            // Increment page
                            page++;
                            
                            // Show load more button if there are more pages
                            if (data.has_next) {
                                loadMoreBtn.classList.remove('d-none');
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        // Show error message
                        if (window.djangoToast) {
                            window.djangoToast.error('Failed to load more products. Please try again.');
                        }
                    })
                    .finally(() => {
                        // Hide loading spinner
                        if (loadingSpinner) {
                            loadingSpinner.classList.add('d-none');
                        }
                        
                        loading = false;
                    });
            }
        });
    }
    
    // Handle wishlist toggle
    const wishlistButtons = document.querySelectorAll('.wishlist-btn');
    
    wishlistButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const productId = this.getAttribute('data-product-id');
            const isAuthenticated = this.getAttribute('data-authenticated') === 'true';
            
            if (!isAuthenticated) {
                // Redirect to login page
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                return;
            }
            
            if (productId) {
                // Toggle wishlist status
                fetch('/accounts/wishlist/toggle/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        product_id: productId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Toggle active class
                        this.classList.toggle('active');
                        
                        // Update icon
                        const icon = this.querySelector('i');
                        if (icon) {
                            if (data.added) {
                                icon.classList.remove('far');
                                icon.classList.add('fas');
                                
                                // Show success message
                                if (window.djangoToast) {
                                    window.djangoToast.success('Added to wishlist');
                                }
                            } else {
                                icon.classList.remove('fas');
                                icon.classList.add('far');
                                
                                // Show success message
                                if (window.djangoToast) {
                                    window.djangoToast.success('Removed from wishlist');
                                }
                            }
                        }
                    } else {
                        // Show error message
                        if (window.djangoToast) {
                            window.djangoToast.error(data.error || 'Failed to update wishlist');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (window.djangoToast) {
                        window.djangoToast.error('An error occurred. Please try again.');
                    }
                });
            }
        });
    });
    
    // Helper function to get CSRF token from cookies
    function getCookie(name) {
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
    }
});