// Product Detail Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Store variant data from View
    const productVariants = window.productVariantsData || [];

    // Function to update the selected variant based on user selections
    function updateSelectedVariant() {
        if (!productVariants || productVariants.length === 0) {
            return;
        }

        const variantOptions = document.querySelectorAll('.variant-option:checked');
        const selectedAttributes = {};
        variantOptions.forEach(option => {
            selectedAttributes[option.getAttribute('data-attribute')] = option.value;
        });

        const matchingVariant = findMatchingVariant(selectedAttributes);
        const variantIdInput = document.getElementById('selected-variant-id');
        const addToCartBtn = document.querySelector('#add-to-cart-form button[type="submit"]');
        const hasAvailableVariants = productVariants.some(variant => variant.is_in_stock);

        if (matchingVariant) {
            variantIdInput.value = matchingVariant.id;
            updateAvailabilityText(matchingVariant);
            updatePriceDisplay(matchingVariant);
            updateQuantityInput(matchingVariant);
            if (addToCartBtn) addToCartBtn.disabled = !matchingVariant.is_in_stock;
        } else {
            variantIdInput.value = '';
            const availabilityText = document.getElementById('availability-text');
            if (availabilityText) {
                if (hasAvailableVariants) {
                    availabilityText.innerHTML = '<i class="fas fa-times-circle me-1"></i> This combination is not available';
                } else {
                    availabilityText.innerHTML = '<i class="fas fa-times-circle me-1"></i> All variants are out of stock';
                }
                availabilityText.className = 'ms-3 text-danger';
            }
            if (addToCartBtn) addToCartBtn.disabled = true;
            const priceDisplay = document.getElementById('product-price');
            if (priceDisplay && window.productCurrentPrice) {
                priceDisplay.innerHTML = `₹${parseFloat(window.productCurrentPrice).toFixed(2)}`;
            }
        }
    }

    // Find the variant that matches the selected attributes
    function findMatchingVariant(selectedAttributes) {
        return productVariants.find(variant => {
            return Object.entries(selectedAttributes).every(([attrName, attrValueId]) => {
                return variant.attributes[attrName] === parseInt(attrValueId, 10);
            });
        });
    }

    // Update the availability text based on the selected variant
    function updateAvailabilityText(variant) {
        const availabilityText = document.getElementById('availability-text');
        if (!availabilityText) return;

        if (variant.is_in_stock) {
            if (variant.quantity > 10) {
                availabilityText.innerHTML = '<i class="fas fa-check-circle me-1"></i> In Stock';
                availabilityText.className = 'ms-3 text-success';
            } else {
                availabilityText.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i> Only ${variant.quantity} left!`;
                availabilityText.className = 'ms-3 text-warning';
            }
        } else {
            availabilityText.innerHTML = '<i class="fas fa-times-circle me-1"></i> Out of Stock';
            availabilityText.className = 'ms-3 text-danger';
        }

        const addToCartBtn = document.querySelector('#add-to-cart-form button[type="submit"]');
        if (addToCartBtn) {
            addToCartBtn.disabled = !variant.is_in_stock;
        }
    }

    // Update the price display based on the selected variant
    function updatePriceDisplay(variant) {
        const priceDisplay = document.getElementById('product-price');
        if (!priceDisplay) return;

        let priceHTML = '';
        if (variant.is_on_sale) {
            priceHTML = `
                <span class="original-price fs-5 text-decoration-line-through">₹${variant.price.toFixed(2)}</span>
                <span class="fs-3 fw-bold text-primary">₹${variant.sale_price.toFixed(2)}</span>
                <span class="badge bg-danger ms-2">${variant.discount_percentage}% OFF</span>
            `;
        } else {
            priceHTML = `<span class="fs-3 fw-bold text-primary">₹${variant.price.toFixed(2)}</span>`;
        }
        priceDisplay.innerHTML = priceHTML;
    }

    // Update the quantity input maximum based on the selected variant
    function updateQuantityInput(variant) {
        const quantityInput = document.querySelector('.quantity-input');
        if (!quantityInput) return;

        quantityInput.max = variant.quantity;
        if (parseInt(quantityInput.value) > variant.quantity) {
            quantityInput.value = Math.max(1, variant.quantity);
        }
    }

    // Handle quantity buttons
    const quantityInput = document.querySelector('.quantity-input');
    const minusBtn = document.getElementById('quantity-minus');
    const plusBtn = document.getElementById('quantity-plus');

    if (quantityInput && minusBtn && plusBtn) {
        minusBtn.addEventListener('click', function() {
            const currentVal = parseInt(quantityInput.value);
            if (currentVal > 1) {
                quantityInput.value = currentVal - 1;
            }
        });

        plusBtn.addEventListener('click', function() {
            const currentVal = parseInt(quantityInput.value);
            const max = parseInt(quantityInput.max) || 99;
            if (currentVal < max) {
                quantityInput.value = currentVal + 1;
            }
        });
    }

    // Image gallery functionality
    const thumbnails = document.querySelectorAll('.thumbnail-image');
    const mainImage = document.getElementById('main-product-image');
    if (thumbnails.length > 0 && mainImage) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                mainImage.src = this.src;
            });
        });
    }

    // Initialize variant selection
    updateSelectedVariant();

    // Add to cart form submission
    const addToCartForm = document.getElementById('add-to-cart-form');
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const variantIdElement = document.getElementById('selected-variant-id');
            const quantity = parseInt(document.querySelector('.quantity-input').value);

            if (variantIdElement) {
                const variantId = variantIdElement.value;
                if(variantId){
                    fetch(`/check-variant-quantity/${variantId}/`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.quantity >= quantity) {
                                this.submit();
                            } else {
                                alert(`Only ${data.quantity} items left in stock.`);
                                updateAvailabilityText({ quantity: data.quantity, is_in_stock: data.quantity > 0 });
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            this.submit(); // Fallback to server-side validation
                        });
                    }
            } else {
                this.submit(); // No variant selected, proceed normally
            }
        });
    }

    // Image zoom functionality
    const container = document.getElementById('img-container');
    const mainImg = document.getElementById('main-product-image');
    const zoomModal = document.getElementById('zoom-modal');
    const zoomedImg = document.getElementById('zoomed-image');
    const closeBtn = document.getElementById('zoom-close');

    if (container && mainImg && zoomModal && zoomedImg) {
        // Variables for pan/zoom functionality
        let scale = 1;
        let currentTranslate = { x: 0, y: 0 };
        let isDragging = false;
        let dragStart = { x: 0, y: 0 };
        let lastTap = 0; // For double-tap detection on mobile

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
    const thumbnailImages = document.querySelectorAll('.product-thumbnail-image');

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
            const thumbnailWidth = thumbnailImages[0].offsetWidth + 10; // 10px is the gap
            scrollContainer.scrollBy({ left: -thumbnailWidth * 2, behavior: 'smooth' });
        });

        rightBtn.addEventListener('click', () => {
            const thumbnailWidth = thumbnailImages[0].offsetWidth + 10; // 10px is the gap
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
    if (thumbnailImages.length > 0 && mainImg) {
        thumbnailImages.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                // Update main image
                const fullImg = this.getAttribute('data-full-img');
                mainImg.src = fullImg;

                // Update active thumbnail
                thumbnailImages.forEach(t => t.classList.remove('active'));
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