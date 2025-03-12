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
});
