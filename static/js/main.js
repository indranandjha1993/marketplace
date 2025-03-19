document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Product quantity selector
    const quantityInputs = document.querySelectorAll('.quantity-input');
    quantityInputs.forEach(input => {
        const minusBtn = input.parentElement.querySelector('.quantity-minus');
        const plusBtn = input.parentElement.querySelector('.quantity-plus');

        if (minusBtn && plusBtn) {
            minusBtn.addEventListener('click', () => {
                const currentValue = parseInt(input.value);
                if (currentValue > parseInt(input.min || 1)) {
                    input.value = currentValue - 1;
                    triggerChangeEvent(input);
                }
            });

            plusBtn.addEventListener('click', () => {
                const currentValue = parseInt(input.value);
                const max = parseInt(input.max);
                if (!max || currentValue < max) {
                    input.value = currentValue + 1;
                    triggerChangeEvent(input);
                }
            });
        }
    });

    function triggerChangeEvent(element) {
        const event = new Event('change', { bubbles: true });
        element.dispatchEvent(event);
    }

    // Auto-update cart on quantity change
    const cartQuantityInputs = document.querySelectorAll('.cart-quantity-input');
    cartQuantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) {
                form.submit();
            }
        });
    });

    // Product image gallery
    const mainImage = document.getElementById('main-product-image');
    const thumbnails = document.querySelectorAll('.thumbnail-image');

    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                // Update main image
                mainImage.src = this.src;

                // Update active thumbnail
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // Address form toggle for checkout
    const useShippingAddress = document.getElementById('use_shipping_address');
    const billingAddressForm = document.getElementById('billing-address-form');

    if (useShippingAddress && billingAddressForm) {
        useShippingAddress.addEventListener('change', function() {
            billingAddressForm.style.display = this.checked ? 'none' : 'block';
        });

        // Initialize on page load
        billingAddressForm.style.display = useShippingAddress.checked ? 'none' : 'block';
    }

    // Payment method selection
    const paymentMethods = document.querySelectorAll('input[name="payment_method"]');
    const paymentForms = document.querySelectorAll('.payment-method-form');

    if (paymentMethods.length > 0 && paymentForms.length > 0) {
        paymentMethods.forEach(method => {
            method.addEventListener('change', function() {
                const selectedMethodId = this.value;

                // Hide all payment forms
                paymentForms.forEach(form => {
                    form.style.display = 'none';
                });

                // Show selected payment form
                const selectedForm = document.getElementById(`payment-form-${selectedMethodId}`);
                if (selectedForm) {
                    selectedForm.style.display = 'block';
                }
            });
        });

        // Initialize on page load
        const checkedMethod = document.querySelector('input[name="payment_method"]:checked');
        if (checkedMethod) {
            const event = new Event('change', { bubbles: true });
            checkedMethod.dispatchEvent(event);
        }
    }

    // Product filter toggle for mobile
    const filterToggle = document.getElementById('filter-toggle');
    const filterContainer = document.getElementById('filter-container');

    if (filterToggle && filterContainer) {
        filterToggle.addEventListener('click', function() {
            filterContainer.classList.toggle('show-filter');
        });
    }

    // Flash messages auto-dismiss
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // Wishlist toggle with AJAX
    const wishlistForms = document.querySelectorAll('.wishlist-form');
    wishlistForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Only proceed with AJAX if user is authenticated
            if (document.body.classList.contains('user-authenticated')) {
                const formData = new FormData(this);
                const url = this.action;
                const wishlistBtn = this.querySelector('.wishlist-btn');

                fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    // Update button icon based on status
                    if (data.status === 'added') {
                        wishlistBtn.innerHTML = '<i class="fas fa-heart"></i>';
                        wishlistBtn.classList.add('active');
                    } else {
                        wishlistBtn.innerHTML = '<i class="far fa-heart"></i>';
                        wishlistBtn.classList.remove('active');
                    }

                    // Show toast notification
                    const toast = document.createElement('div');
                    toast.className = 'toast-notification ' +
                        (data.status === 'added' ? 'toast-success' : 'toast-info');
                    toast.textContent = data.message;
                    document.body.appendChild(toast);

                    // Remove toast after animation
                    setTimeout(() => {
                        toast.remove();
                    }, 3000);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            } else {
                // If user is not authenticated, submit the form normally
                this.submit();
            }
        });
    });
});


document.addEventListener('DOMContentLoaded', function() {
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
});

document.addEventListener('DOMContentLoaded', function() {
    // Image Zoom Modal Functionality
    const container = document.getElementById('img-container');
    const mainImg = document.getElementById('main-product-image');
    const zoomModal = document.getElementById('zoom-modal');
    const zoomedImg = document.getElementById('zoomed-image');
    const closeBtn = document.getElementById('zoom-close');

    if (container && mainImg && zoomModal && zoomedImg) {
        // Open zoom modal when clicking on the main image
        container.addEventListener('click', function() {
            zoomModal.style.display = 'block';
            zoomedImg.src = mainImg.src;
            document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open

            // Reset zoom level and position when opening modal
            scale = 1;
            currentTranslate = { x: 0, y: 0 };
            zoomedImg.style.transform = '';
        });

        // Close modal when clicking the close button
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                zoomModal.style.display = 'none';
                document.body.style.overflow = 'auto'; // Restore scrolling
            });
        }

        // Close modal when clicking outside the image in the modal
        zoomModal.addEventListener('click', function(e) {
            if (e.target === zoomModal) {
                zoomModal.style.display = 'none';
                document.body.style.overflow = 'auto'; // Restore scrolling
            }
        });

        // Close modal when pressing ESC key (for accessibility)
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && zoomModal.style.display === 'block') {
                zoomModal.style.display = 'none';
                document.body.style.overflow = 'auto'; // Restore scrolling
            }
        });

        // Variables for pan/zoom functionality
        let scale = 1;
        let currentTranslate = { x: 0, y: 0 };
        let isDragging = false;
        let dragStart = { x: 0, y: 0 };
        let lastTap = 0; // For double-tap detection on mobile

        // Mouse wheel zoom
        zoomedImg.addEventListener('wheel', function(e) {
            e.preventDefault();

            // Get mouse position
            const rect = zoomedImg.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // Determine zoom direction
            const delta = e.deltaY > 0 ? -0.1 : 0.1;

            // Calculate new scale
            const newScale = Math.min(Math.max(0.5, scale + delta), 3);

            // Get scale factor
            const factor = newScale / scale;

            // Calculate new translate values to zoom toward mouse pointer
            currentTranslate.x = mouseX - (mouseX - currentTranslate.x * scale) / (scale * factor);
            currentTranslate.y = mouseY - (mouseY - currentTranslate.y * scale) / (scale * factor);

            // Update scale
            scale = newScale;

            // Apply transformation
            zoomedImg.style.transform = `scale(${scale}) translate(${currentTranslate.x}px, ${currentTranslate.y}px)`;
        });

        // Mouse drag functionality for panning
        zoomedImg.addEventListener('mousedown', function(e) {
            if (scale > 1) {
                isDragging = true;
                dragStart.x = e.clientX;
                dragStart.y = e.clientY;
                zoomedImg.style.cursor = 'grabbing';
            }
        });

        document.addEventListener('mousemove', function(e) {
            if (isDragging && scale > 1) {
                e.preventDefault();

                const dx = e.clientX - dragStart.x;
                const dy = e.clientY - dragStart.y;

                currentTranslate.x += dx / scale;
                currentTranslate.y += dy / scale;

                zoomedImg.style.transform = `scale(${scale}) translate(${currentTranslate.x}px, ${currentTranslate.y}px)`;

                dragStart.x = e.clientX;
                dragStart.y = e.clientY;
            }
        });

        document.addEventListener('mouseup', function() {
            isDragging = false;
            if (zoomedImg) zoomedImg.style.cursor = 'grab';
        });

        // Double-click to reset zoom
        zoomedImg.addEventListener('dblclick', function() {
            scale = 1;
            currentTranslate = { x: 0, y: 0 };
            zoomedImg.style.transform = '';
        });

        // Touch events for mobile
        zoomedImg.addEventListener('touchstart', function(e) {
            // Double tap detection
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;

            if (tapLength < 300 && tapLength > 0) {
                // Double tap detected - reset zoom
                scale = 1;
                currentTranslate = { x: 0, y: 0 };
                zoomedImg.style.transform = '';
                e.preventDefault();
            } else if (e.touches.length === 2) {
                // Pinch-to-zoom start
                e.preventDefault();
                const touch1 = e.touches[0];
                const touch2 = e.touches[1];

                // Store initial distance
                const initialDistance = getDistance(touch1, touch2);

                // Store initial touches and scale
                this._initialDistance = initialDistance;
                this._initialScale = scale;
            } else if (e.touches.length === 1 && scale > 1) {
                // Pan start with one finger when zoomed in
                isDragging = true;
                dragStart.x = e.touches[0].clientX;
                dragStart.y = e.touches[0].clientY;
            }

            lastTap = currentTime;
        });

        zoomedImg.addEventListener('touchmove', function(e) {
            if (e.touches.length === 2) {
                // Pinch-to-zoom move
                e.preventDefault();

                const touch1 = e.touches[0];
                const touch2 = e.touches[1];

                const currentDistance = getDistance(touch1, touch2);

                // Calculate new scale based on distance change
                const newScale = Math.min(Math.max(0.5, this._initialScale * (currentDistance / this._initialDistance)), 3);

                // Update scale
                scale = newScale;

                // Apply transformation
                zoomedImg.style.transform = `scale(${scale}) translate(${currentTranslate.x}px, ${currentTranslate.y}px)`;
            } else if (e.touches.length === 1 && isDragging && scale > 1) {
                // Pan move with one finger when zoomed in
                e.preventDefault();

                const dx = e.touches[0].clientX - dragStart.x;
                const dy = e.touches[0].clientY - dragStart.y;

                currentTranslate.x += dx / scale;
                currentTranslate.y += dy / scale;

                zoomedImg.style.transform = `scale(${scale}) translate(${currentTranslate.x}px, ${currentTranslate.y}px)`;

                dragStart.x = e.touches[0].clientX;
                dragStart.y = e.touches[0].clientY;
            }
        });

        zoomedImg.addEventListener('touchend', function() {
            isDragging = false;
        });

        // Helper function to calculate distance between two touch points
        function getDistance(touch1, touch2) {
            const dx = touch1.clientX - touch2.clientX;
            const dy = touch1.clientY - touch2.clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }
    }

    // Horizontal Scroll Functionality for Thumbnails
    const thumbnailsContainer = document.getElementById('thumbnails-container');
    const scrollContainer = document.getElementById('thumbnails-scroll');
    const leftBtn = document.getElementById('scroll-left');
    const rightBtn = document.getElementById('scroll-right');
    const thumbnails = document.querySelectorAll('.product-thumbnail-image');

    if (scrollContainer && leftBtn && rightBtn && thumbnailsContainer) {
        // Check if scrolling is needed
        function checkScrollNeeded() {
            const isScrollNeeded = scrollContainer.scrollWidth > scrollContainer.clientWidth;

            // Add/remove class that hides scroll buttons when not needed
            thumbnailsContainer.classList.toggle('no-scroll-needed', !isScrollNeeded);

            if (isScrollNeeded) {
                // Update scroll buttons state
                updateScrollButtons();
            } else {
                // Center thumbnails when they fit without scrolling
                scrollContainer.style.justifyContent = 'center';
            }
        }

        // Update scroll buttons state
        function updateScrollButtons() {
            // Left button is disabled if scrolled all the way to the left
            leftBtn.classList.toggle('hidden', scrollContainer.scrollLeft <= 0);

            // Right button is disabled if scrolled all the way to the right
            const maxScrollLeft = scrollContainer.scrollWidth - scrollContainer.clientWidth;
            rightBtn.classList.toggle('hidden', scrollContainer.scrollLeft >= maxScrollLeft - 5);
        }

        // Scroll left/right when buttons are clicked
        leftBtn.addEventListener('click', () => {
            const thumbnailWidth = thumbnails[0].offsetWidth + 10; // 10px is the gap
            scrollContainer.scrollBy({ left: -thumbnailWidth * 2, behavior: 'smooth' });
        });

        rightBtn.addEventListener('click', () => {
            const thumbnailWidth = thumbnails[0].offsetWidth + 10; // 10px is the gap
            scrollContainer.scrollBy({ left: thumbnailWidth * 2, behavior: 'smooth' });
        });

        // Update button states when scrolling
        scrollContainer.addEventListener('scroll', updateScrollButtons);

        // Check if scrolling is needed when page loads and when window resizes
        checkScrollNeeded();
        window.addEventListener('resize', checkScrollNeeded);

        // Enable touch scrolling with mouse drag (for desktop)
        let isDown = false;
        let startX;
        let scrollLeft;

        scrollContainer.addEventListener('mousedown', (e) => {
            isDown = true;
            scrollContainer.style.cursor = 'grabbing';
            startX = e.pageX - scrollContainer.offsetLeft;
            scrollLeft = scrollContainer.scrollLeft;
        });

        scrollContainer.addEventListener('mouseleave', () => {
            isDown = false;
            scrollContainer.style.cursor = 'grab';
        });

        scrollContainer.addEventListener('mouseup', () => {
            isDown = false;
            scrollContainer.style.cursor = 'grab';
        });

        scrollContainer.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - scrollContainer.offsetLeft;
            const walk = (x - startX) * 1.5; // Scroll speed multiplier
            scrollContainer.scrollLeft = scrollLeft - walk;
            updateScrollButtons();
        });
    }

    // Thumbnail click functionality
    if (thumbnails.length > 0 && mainImg) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                // Update main image
                const fullImg = this.getAttribute('data-full-img');
                mainImg.src = fullImg;

                // Update active thumbnail
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // If zoomed image is visible, update it too
                if (zoomedImg && zoomModal.style.display === 'block') {
                    zoomedImg.src = fullImg;

                    // Reset zoom when changing image
                    scale = 1;
                    currentTranslate = { x: 0, y: 0 };
                    zoomedImg.style.transform = '';
                }
            });

            // Add keyboard navigation for accessibility
            thumbnail.setAttribute('tabindex', '0'); // Make focusable
            thumbnail.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });
    }
});
