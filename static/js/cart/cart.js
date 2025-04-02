// Cart functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle quantity buttons in cart
    const quantityControls = document.querySelectorAll('.quantity-control');
    
    quantityControls.forEach(control => {
        const minusBtn = control.querySelector('.quantity-minus');
        const plusBtn = control.querySelector('.quantity-plus');
        const input = control.querySelector('.quantity-input');
        const updateBtn = control.closest('tr').querySelector('.update-cart-item');
        const itemId = control.getAttribute('data-item-id');
        
        if (minusBtn && plusBtn && input) {
            // Minus button click
            minusBtn.addEventListener('click', function() {
                const currentVal = parseInt(input.value);
                if (currentVal > 1) {
                    input.value = currentVal - 1;
                    if (updateBtn) {
                        updateBtn.classList.remove('d-none');
                    }
                }
            });
            
            // Plus button click
            plusBtn.addEventListener('click', function() {
                const currentVal = parseInt(input.value);
                const max = parseInt(input.getAttribute('max')) || 99;
                if (currentVal < max) {
                    input.value = currentVal + 1;
                    if (updateBtn) {
                        updateBtn.classList.remove('d-none');
                    }
                }
            });
            
            // Input change
            input.addEventListener('change', function() {
                let val = parseInt(this.value);
                const max = parseInt(this.getAttribute('max')) || 99;
                
                // Ensure value is a number and within range
                if (isNaN(val) || val < 1) {
                    val = 1;
                } else if (val > max) {
                    val = max;
                }
                
                this.value = val;
                
                if (updateBtn) {
                    updateBtn.classList.remove('d-none');
                }
            });
        }
    });
    
    // Handle update cart item
    const updateButtons = document.querySelectorAll('.update-cart-item');
    
    updateButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const row = this.closest('tr');
            const itemId = this.getAttribute('data-item-id');
            const quantityInput = row.querySelector('.quantity-input');
            const quantity = parseInt(quantityInput.value);
            
            if (itemId && quantity) {
                // Show loading spinner
                const spinner = this.querySelector('.spinner-border');
                const btnText = this.querySelector('.btn-text');
                
                if (spinner && btnText) {
                    spinner.classList.remove('d-none');
                    btnText.classList.add('d-none');
                }
                
                // Update cart via AJAX
                fetch('/cart/update/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        item_id: itemId,
                        quantity: quantity
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update subtotal
                        const subtotalElement = row.querySelector('.item-subtotal');
                        if (subtotalElement) {
                            subtotalElement.textContent = data.item_subtotal;
                        }
                        
                        // Update cart total
                        const cartTotalElement = document.getElementById('cart-total');
                        if (cartTotalElement) {
                            cartTotalElement.textContent = data.cart_total;
                        }
                        
                        // Hide update button
                        this.classList.add('d-none');
                        
                        // Show success message
                        if (window.djangoToast) {
                            window.djangoToast.success('Cart updated successfully');
                        }
                    } else {
                        // Show error message
                        if (window.djangoToast) {
                            window.djangoToast.error(data.error || 'Failed to update cart');
                        }
                        
                        // Reset quantity if needed
                        if (data.available_quantity) {
                            quantityInput.value = data.available_quantity;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (window.djangoToast) {
                        window.djangoToast.error('An error occurred. Please try again.');
                    }
                })
                .finally(() => {
                    // Hide loading spinner
                    if (spinner && btnText) {
                        spinner.classList.add('d-none');
                        btnText.classList.remove('d-none');
                    }
                });
            }
        });
    });
    
    // Handle remove cart item
    const removeButtons = document.querySelectorAll('.remove-cart-item');
    
    removeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const row = this.closest('tr');
            const itemId = this.getAttribute('data-item-id');
            
            if (itemId && confirm('Are you sure you want to remove this item from your cart?')) {
                // Show loading spinner
                const spinner = this.querySelector('.spinner-border');
                const icon = this.querySelector('.fa-trash');
                
                if (spinner && icon) {
                    spinner.classList.remove('d-none');
                    icon.classList.add('d-none');
                }
                
                // Remove item via AJAX
                fetch('/cart/remove/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        item_id: itemId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Remove row with animation
                        row.style.transition = 'opacity 0.3s ease';
                        row.style.opacity = '0';
                        
                        setTimeout(() => {
                            row.remove();
                            
                            // Update cart total
                            const cartTotalElement = document.getElementById('cart-total');
                            if (cartTotalElement) {
                                cartTotalElement.textContent = data.cart_total;
                            }
                            
                            // Update cart count in header
                            const cartCountElement = document.querySelector('.cart-count');
                            if (cartCountElement && data.cart_count !== undefined) {
                                cartCountElement.textContent = data.cart_count;
                                
                                // Hide badge if count is 0
                                if (data.cart_count === 0) {
                                    cartCountElement.classList.add('d-none');
                                    
                                    // Show empty cart message
                                    const cartTable = document.querySelector('.cart-table');
                                    const emptyCartMessage = document.querySelector('.empty-cart-message');
                                    
                                    if (cartTable) {
                                        cartTable.classList.add('d-none');
                                    }
                                    
                                    if (emptyCartMessage) {
                                        emptyCartMessage.classList.remove('d-none');
                                    }
                                }
                            }
                            
                            // Show success message
                            if (window.djangoToast) {
                                window.djangoToast.success('Item removed from cart');
                            }
                        }, 300);
                    } else {
                        // Show error message
                        if (window.djangoToast) {
                            window.djangoToast.error(data.error || 'Failed to remove item');
                        }
                        
                        // Hide loading spinner
                        if (spinner && icon) {
                            spinner.classList.add('d-none');
                            icon.classList.remove('d-none');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (window.djangoToast) {
                        window.djangoToast.error('An error occurred. Please try again.');
                    }
                    
                    // Hide loading spinner
                    if (spinner && icon) {
                        spinner.classList.add('d-none');
                        icon.classList.remove('d-none');
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