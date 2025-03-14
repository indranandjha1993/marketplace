// Cart functionality with AJAX support
document.addEventListener('DOMContentLoaded', function() {
    // Add to cart with AJAX
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');

    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const url = this.action;
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;

            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';

            // Send AJAX request
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
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;

                // Update cart count in header
                updateCartCount(data.cart_count);

                // Show notification
                showNotification(data.message, data.success ? 'success' : 'error');

                // If the product requires variant selection and none was selected
                if (data.requires_variant) {
                    // Scroll to variant selection area and highlight it
                    const variantSection = document.querySelector('.product-variants');
                    if (variantSection) {
                        variantSection.scrollIntoView({ behavior: 'smooth' });
                        variantSection.classList.add('highlight-section');
                        setTimeout(() => {
                            variantSection.classList.remove('highlight-section');
                        }, 2000);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                showNotification('An error occurred. Please try again.', 'error');
            });
        });
    });

    // Update cart item quantity
    const quantityControls = document.querySelectorAll('.cart-quantity-control');

    quantityControls.forEach(control => {
        control.addEventListener('change', function() {
            const form = this.closest('form');
            const formData = new FormData(form);
            const url = form.action;
            const itemId = this.dataset.itemId;

            // Show loading overlay for this item
            const cartItem = this.closest('.cart-item');
            cartItem.classList.add('updating');

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
                // Remove loading state
                cartItem.classList.remove('updating');

                if (data.success) {
                    // Update cart count in header
                    updateCartCount(data.cart_count);

                    // Update cart totals
                    updateCartTotals(data.cart_total);

                    // Update individual item details
                    if (data.item_removed) {
                        // Item was removed (quantity set to 0)
                        cartItem.classList.add('fade-out');
                        setTimeout(() => {
                            cartItem.remove();

                            // If no items left, refresh the page to show empty cart state
                            if (data.cart_count === 0) {
                                location.reload();
                            }
                        }, 300);
                    } else {
                        // Update item total
                        const itemTotalEl = cartItem.querySelector('.item-total');
                        if (itemTotalEl) {
                            itemTotalEl.textContent = '₹' + data.item_total.toFixed(2);
                        }

                        // Update item subtotal display if present
                        const itemSubtotalEl = cartItem.querySelector('.item-subtotal');
                        if (itemSubtotalEl) {
                            itemSubtotalEl.textContent = '₹' + data.item_subtotal.toFixed(2);
                        }
                    }

                    // Show notification
                    showNotification(data.message, 'success');
                } else {
                    // If there's an available quantity limit
                    if (data.available_quantity) {
                        // Reset input to available quantity
                        this.value = data.available_quantity;
                    }

                    showNotification(data.message, 'warning');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                cartItem.classList.remove('updating');
                showNotification('An error occurred. Please try again.', 'error');
            });
        });
    });

    // Remove item from cart
    const removeItemButtons = document.querySelectorAll('.remove-cart-item');

    removeItemButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const form = this.closest('form');
            const formData = new FormData(form);
            const url = form.action;
            const cartItem = this.closest('.cart-item');

            // Confirm removal
            if (confirm('Are you sure you want to remove this item from your cart?')) {
                // Show loading state
                cartItem.classList.add('updating');

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
                    if (data.success) {
                        // Update cart count and totals
                        updateCartCount(data.cart_count);
                        updateCartTotals(data.cart_total);

                        // Fade out and remove the item
                        cartItem.classList.add('fade-out');
                        setTimeout(() => {
                            cartItem.remove();

                            // If no items left, refresh to show empty cart state
                            if (data.cart_count === 0) {
                                location.reload();
                            }
                        }, 300);

                        showNotification(data.message, 'success');
                    } else {
                        cartItem.classList.remove('updating');
                        showNotification(data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    cartItem.classList.remove('updating');
                    showNotification('An error occurred. Please try again.', 'error');
                });
            }
        });
    });

    // Save item for later
    const saveForLaterButtons = document.querySelectorAll('.save-for-later');

    saveForLaterButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const form = this.closest('form');
            const formData = new FormData(form);
            const url = form.action;
            const cartItem = this.closest('.cart-item');

            // Show loading state
            cartItem.classList.add('updating');

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
                if (data.success) {
                    // Update cart count and totals
                    updateCartCount(data.cart_count);
                    updateCartTotals(data.cart_total);

                    // Fade out and remove from cart items
                    cartItem.classList.add('fade-out');
                    setTimeout(() => {
                        cartItem.remove();

                        // Refresh to show in saved items section
                        // This is a bit of a hack, but simplest way to update the saved items section
                        location.reload();
                    }, 300);

                    showNotification(data.message, 'success');
                } else {
                    cartItem.classList.remove('updating');
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                cartItem.classList.remove('updating');
                showNotification('An error occurred. Please try again.', 'error');
            });
        });
    });

    // Move to cart (from saved for later)
    const moveToCartButtons = document.querySelectorAll('.move-to-cart');

    moveToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const form = this.closest('form');
            const formData = new FormData(form);
            const url = form.action;
            const savedItem = this.closest('.saved-item');

            // Show loading state
            savedItem.classList.add('updating');

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
                if (data.success) {
                    // Update cart count
                    updateCartCount(data.cart_count);

                    // Fade out and remove from saved items
                    savedItem.classList.add('fade-out');
                    setTimeout(() => {
                        savedItem.remove();

                        // Refresh to show in cart items section
                        location.reload();
                    }, 300);

                    showNotification(data.message, 'success');
                } else {
                    savedItem.classList.remove('updating');
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                savedItem.classList.remove('updating');
                showNotification('An error occurred. Please try again.', 'error');
            });
        });
    });

    // Clear cart
    const clearCartButton = document.querySelector('.clear-cart-button');

    if (clearCartButton) {
        clearCartButton.addEventListener('click', function(e) {
            e.preventDefault();

            if (confirm('Are you sure you want to remove all items from your cart?')) {
                const form = this.closest('form');
                const formData = new FormData(form);
                const url = form.action;

                // Show loading overlay
                document.body.classList.add('loading');

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
                    if (data.success) {
                        // Reload page to show empty cart state
                        location.reload();
                    } else {
                        document.body.classList.remove('loading');
                        showNotification(data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.body.classList.remove('loading');
                    showNotification('An error occurred. Please try again.', 'error');
                });
            }
        });
    }

    // Helper functions
    function updateCartCount(count) {
        const cartCountBadges = document.querySelectorAll('.cart-count-badge');
        cartCountBadges.forEach(badge => {
            badge.textContent = count;

            // Add animation effect
            badge.classList.add('pulse');
            setTimeout(() => {
                badge.classList.remove('pulse');
            }, 500);
        });
    }

    function updateCartTotals(total) {
        // Update cart subtotal, tax, and final total
        // This may need customization based on your actual cart layout
        const cartTotalElements = document.querySelectorAll('.cart-total');
        const formattedTotal = '₹' + (parseFloat(total)).toFixed(2);

        cartTotalElements.forEach(element => {
            element.textContent = formattedTotal;

            // Add highlight effect
            element.classList.add('highlight-change');
            setTimeout(() => {
                element.classList.remove('highlight-change');
            }, 700);
        });
    }

    function showNotification(message, type = 'success') {
        // Create notification element if it doesn't exist
        let notification = document.querySelector('.toast-notification');

        if (!notification) {
            notification = document.createElement('div');
            notification.className = 'toast-notification';
            document.body.appendChild(notification);
        }

        // Set message and type
        notification.textContent = message;
        notification.className = `toast-notification toast-${type}`;

        // Show notification
        notification.classList.add('show');

        // Remove after animation completes
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Initialize quantity buttons
    initializeQuantityButtons();
});

function initializeQuantityButtons() {
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
}

function triggerChangeEvent(element) {
    const event = new Event('change', { bubbles: true });
    element.dispatchEvent(event);
}
