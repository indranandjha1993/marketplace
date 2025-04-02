/**
 * Main JavaScript file for the marketplace application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Helper function to trigger change event
    function triggerChangeEvent(element) {
        const event = new Event('change', { bubbles: true });
        element.dispatchEvent(event);
    }

    // Function to handle search submission
    function setupSearchForm(formId, inputId) {
        const form = document.getElementById(formId);
        const input = document.getElementById(inputId);

        if (form && input) {
            // Enable enter key submission
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    form.submit();
                }
            });

            // Ensure the search button works
            const button = form.querySelector('.search-button');
            if (button) {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    form.submit();
                });
            }
        }
    }

    // Setup both desktop and mobile search forms
    setupSearchForm('desktopSearchForm', 'desktopSearchInput');
    setupSearchForm('mobileSearchForm', 'mobileSearchInput');

    // Handle mobile navigation
    const mobileNavToggle = document.getElementById('mobile-nav-toggle');
    const mobileNav = document.getElementById('mobile-nav');

    if (mobileNavToggle && mobileNav) {
        mobileNavToggle.addEventListener('click', function() {
            mobileNav.classList.toggle('show');
            document.body.classList.toggle('mobile-nav-open');
        });
    }

    // Handle dropdown hover on desktop
    const dropdownItems = document.querySelectorAll('.dropdown-hover');

    if (window.innerWidth >= 992) { // Only on desktop
        dropdownItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.querySelector('.dropdown-toggle').click();
            });

            item.addEventListener('mouseleave', function() {
                this.querySelector('.dropdown-toggle').click();
            });
        });
    }

    // Back to top button
    const backToTopBtn = document.getElementById('back-to-top');

    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });

        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Add to cart buttons
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const productId = this.getAttribute('data-product-id');
            const quantity = 1;

            if (productId) {
                // Show loading state
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
                this.disabled = true;

                // Use utility function to add to cart
                if (window.marketplaceUtils) {
                    window.marketplaceUtils.addToCart(productId, quantity)
                        .then(data => {
                            if (data.success) {
                                // Show success message
                                window.marketplaceUtils.showToast('Added to cart successfully', 'success');

                                // Update cart count in header
                                const cartCountElement = document.querySelector('.cart-count');
                                if (cartCountElement && data.cart_count !== undefined) {
                                    cartCountElement.textContent = data.cart_count;
                                    cartCountElement.classList.remove('d-none');
                                }
                            } else {
                                // Show error message
                                window.marketplaceUtils.showToast(data.error || 'Failed to add to cart', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                        })
                        .finally(() => {
                            // Reset button
                            this.innerHTML = originalText;
                            this.disabled = false;
                        });
                } else {
                    // Fallback if utils not loaded
                    fetch('/cart/add/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            product_id: productId,
                            quantity: quantity
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Show success message
                            if (window.djangoToast) {
                                window.djangoToast.success('Added to cart successfully');
                            } else {
                                alert('Added to cart successfully');
                            }

                            // Update cart count in header
                            const cartCountElement = document.querySelector('.cart-count');
                            if (cartCountElement && data.cart_count !== undefined) {
                                cartCountElement.textContent = data.cart_count;
                                cartCountElement.classList.remove('d-none');
                            }
                        } else {
                            // Show error message
                            if (window.djangoToast) {
                                window.djangoToast.error(data.error || 'Failed to add to cart');
                            } else {
                                alert(data.error || 'Failed to add to cart');
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        if (window.djangoToast) {
                            window.djangoToast.error('An error occurred. Please try again.');
                        } else {
                            alert('An error occurred. Please try again.');
                        }
                    })
                    .finally(() => {
                        // Reset button
                        this.innerHTML = originalText;
                        this.disabled = false;
                    });
                }
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
