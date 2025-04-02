// Checkout Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Address selection
    const addressRadios = document.querySelectorAll('input[name="address"]');
    const newAddressForm = document.getElementById('new-address-form');
    const newAddressToggle = document.getElementById('new-address-toggle');
    
    if (addressRadios.length > 0 && newAddressForm) {
        // Handle address selection change
        addressRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'new') {
                    newAddressForm.classList.remove('d-none');
                    
                    // Make form fields required
                    const formInputs = newAddressForm.querySelectorAll('input, select');
                    formInputs.forEach(input => {
                        if (input.getAttribute('data-required') === 'true') {
                            input.required = true;
                        }
                    });
                } else {
                    newAddressForm.classList.add('d-none');
                    
                    // Remove required attribute from form fields
                    const formInputs = newAddressForm.querySelectorAll('input, select');
                    formInputs.forEach(input => {
                        input.required = false;
                    });
                }
            });
        });
        
        // Handle new address toggle
        if (newAddressToggle) {
            newAddressToggle.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Find the "new" radio button and check it
                const newAddressRadio = document.querySelector('input[name="address"][value="new"]');
                if (newAddressRadio) {
                    newAddressRadio.checked = true;
                    
                    // Trigger change event
                    const event = new Event('change');
                    newAddressRadio.dispatchEvent(event);
                    
                    // Scroll to form
                    newAddressForm.scrollIntoView({ behavior: 'smooth' });
                }
            });
        }
    }
    
    // Payment method selection
    const paymentMethodRadios = document.querySelectorAll('input[name="payment_method"]');
    const paymentForms = document.querySelectorAll('.payment-method-form');
    
    if (paymentMethodRadios.length > 0 && paymentForms.length > 0) {
        // Handle payment method selection change
        paymentMethodRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                const selectedMethod = this.value;
                
                // Hide all payment forms
                paymentForms.forEach(form => {
                    form.classList.add('d-none');
                    
                    // Remove required attribute from form fields
                    const formInputs = form.querySelectorAll('input, select');
                    formInputs.forEach(input => {
                        input.required = false;
                    });
                });
                
                // Show selected payment form
                const selectedForm = document.getElementById(`${selectedMethod}-form`);
                if (selectedForm) {
                    selectedForm.classList.remove('d-none');
                    
                    // Make form fields required
                    const formInputs = selectedForm.querySelectorAll('input, select');
                    formInputs.forEach(input => {
                        if (input.getAttribute('data-required') === 'true') {
                            input.required = true;
                        }
                    });
                }
            });
        });
        
        // Initialize with the checked payment method
        const checkedPaymentMethod = document.querySelector('input[name="payment_method"]:checked');
        if (checkedPaymentMethod) {
            const event = new Event('change');
            checkedPaymentMethod.dispatchEvent(event);
        }
    }
    
    // Coupon code application
    const couponForm = document.getElementById('coupon-form');
    const couponInput = document.getElementById('coupon-code');
    const couponBtn = document.getElementById('apply-coupon-btn');
    const couponError = document.getElementById('coupon-error');
    const couponSuccess = document.getElementById('coupon-success');
    const orderSummary = document.getElementById('order-summary');
    
    if (couponForm && couponInput && couponBtn) {
        couponForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const couponCode = couponInput.value.trim();
            
            if (!couponCode) {
                if (couponError) {
                    couponError.textContent = 'Please enter a coupon code';
                    couponError.classList.remove('d-none');
                }
                return;
            }
            
            // Show loading state
            couponBtn.disabled = true;
            const originalBtnText = couponBtn.innerHTML;
            couponBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Applying...';
            
            // Hide any previous messages
            if (couponError) couponError.classList.add('d-none');
            if (couponSuccess) couponSuccess.classList.add('d-none');
            
            // Apply coupon via AJAX
            fetch('/checkout/apply-coupon/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    coupon_code: couponCode
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    if (couponSuccess) {
                        couponSuccess.textContent = data.message || 'Coupon applied successfully';
                        couponSuccess.classList.remove('d-none');
                    }
                    
                    // Update order summary
                    if (orderSummary && data.order_summary_html) {
                        orderSummary.innerHTML = data.order_summary_html;
                    }
                    
                    // Disable coupon input and button
                    couponInput.disabled = true;
                    couponBtn.innerHTML = 'Applied';
                    couponBtn.disabled = true;
                    
                    // Add remove coupon button
                    const removeCouponBtn = document.createElement('button');
                    removeCouponBtn.type = 'button';
                    removeCouponBtn.className = 'btn btn-sm btn-outline-danger ms-2';
                    removeCouponBtn.textContent = 'Remove';
                    removeCouponBtn.addEventListener('click', removeCoupon);
                    
                    couponForm.appendChild(removeCouponBtn);
                } else {
                    // Show error message
                    if (couponError) {
                        couponError.textContent = data.message || 'Invalid coupon code';
                        couponError.classList.remove('d-none');
                    }
                    
                    // Reset button
                    couponBtn.innerHTML = originalBtnText;
                    couponBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Show error message
                if (couponError) {
                    couponError.textContent = 'An error occurred. Please try again.';
                    couponError.classList.remove('d-none');
                }
                
                // Reset button
                couponBtn.innerHTML = originalBtnText;
                couponBtn.disabled = false;
            });
        });
        
        // Function to remove coupon
        function removeCoupon() {
            // Show loading state
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
            
            // Hide any previous messages
            if (couponError) couponError.classList.add('d-none');
            if (couponSuccess) couponSuccess.classList.add('d-none');
            
            // Remove coupon via AJAX
            fetch('/checkout/remove-coupon/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update order summary
                    if (orderSummary && data.order_summary_html) {
                        orderSummary.innerHTML = data.order_summary_html;
                    }
                    
                    // Reset coupon input and button
                    couponInput.value = '';
                    couponInput.disabled = false;
                    couponBtn.innerHTML = 'Apply';
                    couponBtn.disabled = false;
                    
                    // Remove this button
                    this.remove();
                    
                    // Show success message
                    if (couponSuccess) {
                        couponSuccess.textContent = 'Coupon removed successfully';
                        couponSuccess.classList.remove('d-none');
                    }
                } else {
                    // Show error message
                    if (couponError) {
                        couponError.textContent = data.message || 'Failed to remove coupon';
                        couponError.classList.remove('d-none');
                    }
                    
                    // Reset this button
                    this.innerHTML = 'Remove';
                    this.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Show error message
                if (couponError) {
                    couponError.textContent = 'An error occurred. Please try again.';
                    couponError.classList.remove('d-none');
                }
                
                // Reset this button
                this.innerHTML = 'Remove';
                this.disabled = false;
            });
        }
    }
    
    // Form validation
    const checkoutForm = document.getElementById('checkout-form');
    
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            // Custom validation logic here if needed
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            }
        });
    }
    
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