/**
 * Main JavaScript file for the marketplace application
 * Handles core UI interactions and initializations
 *
 * @version 1.0.0
 */

(function() {
    'use strict';

    // Store frequently accessed DOM elements
    const elements = {};

    /**
     * Initialize Bootstrap components
     */
    function initBootstrapComponents() {
        // Initialize tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        if (tooltipTriggerList.length > 0) {
            [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }

        // Initialize popovers
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        if (popoverTriggerList.length > 0) {
            [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
        }
    }

    /**
     * Setup search functionality
     */
    function setupSearch() {
        // Function to handle search submission
        function setupSearchForm(formId, inputId) {
            const form = document.getElementById(formId);
            const input = document.getElementById(inputId);

            if (!form || !input) return;

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

        // Setup both desktop and mobile search forms
        setupSearchForm('desktopSearchForm', 'desktopSearchInput');
        setupSearchForm('mobileSearchForm', 'mobileSearchInput');
    }

    /**
     * Setup mobile navigation
     */
    function setupMobileNavigation() {
        const mobileNavToggle = document.getElementById('mobile-nav-toggle');
        const mobileNav = document.getElementById('mobile-nav');

        if (mobileNavToggle && mobileNav) {
            mobileNavToggle.addEventListener('click', function() {
                mobileNav.classList.toggle('show');
                document.body.classList.toggle('mobile-nav-open');
            });

            // Close mobile nav when clicking outside
            document.addEventListener('click', function(event) {
                if (mobileNav.classList.contains('show') &&
                    !mobileNav.contains(event.target) &&
                    event.target !== mobileNavToggle) {
                    mobileNav.classList.remove('show');
                    document.body.classList.remove('mobile-nav-open');
                }
            });
        }
    }

    /**
     * Setup dropdown hover functionality for desktop
     */
    function setupDropdownHover() {
        const dropdownItems = document.querySelectorAll('.dropdown-hover');

        if (window.innerWidth >= 992 && dropdownItems.length > 0) { // Only on desktop
            dropdownItems.forEach(item => {
                const dropdownToggle = item.querySelector('.dropdown-toggle');
                if (!dropdownToggle) return;

                item.addEventListener('mouseenter', function() {
                    dropdownToggle.click();
                });

                item.addEventListener('mouseleave', function() {
                    dropdownToggle.click();
                });
            });
        }
    }

    /**
     * Setup back to top button
     */
    function setupBackToTop() {
        const backToTopBtn = document.getElementById('back-to-top');

        if (backToTopBtn) {
            // Use throttled scroll event for better performance
            const handleScroll = window.marketplaceUtils.throttle(function() {
                if (window.pageYOffset > 300) {
                    backToTopBtn.classList.add('show');
                } else {
                    backToTopBtn.classList.remove('show');
                }
            }, 100);

            window.addEventListener('scroll', handleScroll);

            backToTopBtn.addEventListener('click', function() {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
        }
    }

    /**
     * Setup add to cart functionality
     */
    function setupAddToCart() {
        const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');

        if (!addToCartButtons.length) return;

        addToCartButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();

                const productId = this.getAttribute('data-product-id');
                const quantity = parseInt(this.getAttribute('data-quantity') || '1', 10);
                const variantId = this.getAttribute('data-variant-id') || null;

                if (!productId) return;

                // Show loading state
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
                this.disabled = true;

                // Use utility function to add to cart
                if (window.marketplaceUtils) {
                    window.marketplaceUtils.addToCart(productId, quantity, variantId)
                        .then(data => {
                            if (data.success) {
                                // Show success message
                                window.marketplaceUtils.showToast('Added to cart successfully', 'success');

                                // Update cart count in header
                                updateCartCount(data.cart_count);

                                // Trigger custom event for other components to react
                                document.dispatchEvent(new CustomEvent('cart:updated', {
                                    detail: { cartCount: data.cart_count }
                                }));
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
                }
            });
        });
    }

    /**
     * Setup wishlist toggle functionality
     */
    function setupWishlistToggle() {
        const wishlistButtons = document.querySelectorAll('.wishlist-btn');

        if (!wishlistButtons.length) return;

        wishlistButtons.forEach(button => {
            if (button.closest('form')) {
                // If button is inside a form, let the form handle it
                return;
            }

            button.addEventListener('click', function(e) {
                e.preventDefault();

                const productId = this.getAttribute('data-product-id');
                if (!productId) return;

                // Show loading state
                const icon = this.querySelector('i');
                const originalClass = icon.className;
                icon.className = 'fas fa-spinner fa-spin';
                this.disabled = true;

                // Use utility function to toggle wishlist
                if (window.marketplaceUtils) {
                    window.marketplaceUtils.toggleWishlist(productId)
                        .then(data => {
                            if (data.success) {
                                // Update button state
                                if (data.in_wishlist) {
                                    this.classList.add('active');
                                    icon.className = 'fas fa-heart';
                                } else {
                                    this.classList.remove('active');
                                    icon.className = 'far fa-heart';
                                }

                                // Show success message
                                window.marketplaceUtils.showToast(
                                    data.in_wishlist ? 'Added to wishlist' : 'Removed from wishlist',
                                    'success'
                                );

                                // Trigger custom event
                                document.dispatchEvent(new CustomEvent('wishlist:updated', {
                                    detail: { inWishlist: data.in_wishlist, productId }
                                }));
                            } else {
                                // Restore original icon
                                icon.className = originalClass;
                                // Show error message
                                window.marketplaceUtils.showToast(data.error || 'Failed to update wishlist', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            icon.className = originalClass;
                            window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                        })
                        .finally(() => {
                            this.disabled = false;
                        });
                }
            });
        });
    }

    /**
     * Update cart count in the header
     * @param {number} count - New cart count
     */
    function updateCartCount(count) {
        if (typeof count !== 'undefined') {
            const cartCountElements = document.querySelectorAll('.cart-count');
            cartCountElements.forEach(element => {
                element.textContent = count;
                if (count > 0) {
                    element.classList.remove('d-none');
                } else {
                    element.classList.add('d-none');
                }
            });
        }
    }

    /**
     * Setup lazy loading for images
     */
    function setupLazyLoading() {
        if ('loading' in HTMLImageElement.prototype) {
            // Browser supports native lazy loading
            const lazyImages = document.querySelectorAll('img[loading="lazy"]');
            lazyImages.forEach(img => {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    delete img.dataset.src;
                }
            });
        } else {
            // Fallback for browsers that don't support native lazy loading
            const lazyImages = document.querySelectorAll('img[data-src]');
            if (lazyImages.length === 0) return;

            const lazyLoadObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        delete img.dataset.src;
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                });
            });

            lazyImages.forEach(img => {
                lazyLoadObserver.observe(img);
            });
        }
    }

    /**
     * Initialize all components
     */
    function init() {
        // Initialize components
        initBootstrapComponents();
        setupSearch();
        setupMobileNavigation();
        setupDropdownHover();
        setupBackToTop();
        setupAddToCart();
        setupWishlistToggle();
        setupLazyLoading();

        // Add any page-specific initializations here

        // Log initialization complete
        console.log('Marketplace UI initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
