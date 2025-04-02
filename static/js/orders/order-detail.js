/**
 * Order Detail Page JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Order tracking timeline
    const trackingTimeline = document.querySelector('.tracking-timeline');
    
    if (trackingTimeline) {
        // Highlight current status
        const currentStatus = trackingTimeline.getAttribute('data-current-status');
        if (currentStatus) {
            const statusItems = trackingTimeline.querySelectorAll('.tracking-item');
            
            let currentFound = false;
            statusItems.forEach(item => {
                const itemStatus = item.getAttribute('data-status');
                
                if (currentStatus === itemStatus) {
                    item.classList.add('active');
                    currentFound = true;
                } else if (!currentFound) {
                    item.classList.add('completed');
                }
            });
        }
    }
    
    // Order cancellation
    const cancelOrderBtn = document.getElementById('cancel-order-btn');
    const cancelOrderModal = document.getElementById('cancel-order-modal');
    
    if (cancelOrderBtn && cancelOrderModal) {
        const cancelOrderForm = cancelOrderModal.querySelector('form');
        const cancelReasonSelect = document.getElementById('cancel-reason');
        const cancelSubmitBtn = document.getElementById('cancel-submit-btn');
        
        if (cancelOrderForm && cancelReasonSelect && cancelSubmitBtn) {
            // Validate reason selection
            cancelReasonSelect.addEventListener('change', function() {
                if (this.value) {
                    cancelSubmitBtn.disabled = false;
                } else {
                    cancelSubmitBtn.disabled = true;
                }
            });
            
            // Handle form submission
            cancelOrderForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                if (!cancelReasonSelect.value) {
                    return;
                }
                
                // Show loading state
                cancelSubmitBtn.disabled = true;
                const originalText = cancelSubmitBtn.innerHTML;
                cancelSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                // Get form data
                const formData = new FormData(this);
                const orderId = formData.get('order_id');
                
                // Send cancellation request
                fetch(`/orders/${orderId}/cancel/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.marketplaceUtils.getCsrfToken()
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        window.marketplaceUtils.showToast('Order cancelled successfully', 'success');
                        
                        // Hide modal
                        const modalInstance = bootstrap.Modal.getInstance(cancelOrderModal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                        
                        // Reload page after a short delay
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        // Show error message
                        window.marketplaceUtils.showToast(data.error || 'Failed to cancel order', 'error');
                        
                        // Reset button
                        cancelSubmitBtn.innerHTML = originalText;
                        cancelSubmitBtn.disabled = false;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                    
                    // Reset button
                    cancelSubmitBtn.innerHTML = originalText;
                    cancelSubmitBtn.disabled = false;
                });
            });
        }
    }
    
    // Return request
    const returnItemBtns = document.querySelectorAll('.return-item-btn');
    const returnItemModal = document.getElementById('return-item-modal');
    
    if (returnItemBtns.length > 0 && returnItemModal) {
        const returnItemForm = returnItemModal.querySelector('form');
        const returnReasonSelect = document.getElementById('return-reason');
        const returnDescriptionInput = document.getElementById('return-description');
        const returnSubmitBtn = document.getElementById('return-submit-btn');
        const returnItemIdInput = document.getElementById('return-item-id');
        
        if (returnItemForm && returnReasonSelect && returnSubmitBtn && returnItemIdInput) {
            // Handle return button click
            returnItemBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    const itemId = this.getAttribute('data-item-id');
                    if (itemId) {
                        returnItemIdInput.value = itemId;
                        
                        // Reset form
                        returnReasonSelect.value = '';
                        if (returnDescriptionInput) {
                            returnDescriptionInput.value = '';
                        }
                        returnSubmitBtn.disabled = true;
                    }
                });
            });
            
            // Validate reason selection
            returnReasonSelect.addEventListener('change', function() {
                if (this.value) {
                    returnSubmitBtn.disabled = false;
                } else {
                    returnSubmitBtn.disabled = true;
                }
            });
            
            // Handle form submission
            returnItemForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                if (!returnReasonSelect.value) {
                    return;
                }
                
                // Show loading state
                returnSubmitBtn.disabled = true;
                const originalText = returnSubmitBtn.innerHTML;
                returnSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                // Get form data
                const formData = new FormData(this);
                const orderId = formData.get('order_id');
                const itemId = formData.get('item_id');
                
                // Send return request
                fetch(`/orders/${orderId}/return-item/${itemId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.marketplaceUtils.getCsrfToken()
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        window.marketplaceUtils.showToast('Return request submitted successfully', 'success');
                        
                        // Hide modal
                        const modalInstance = bootstrap.Modal.getInstance(returnItemModal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                        
                        // Reload page after a short delay
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        // Show error message
                        window.marketplaceUtils.showToast(data.error || 'Failed to submit return request', 'error');
                        
                        // Reset button
                        returnSubmitBtn.innerHTML = originalText;
                        returnSubmitBtn.disabled = false;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                    
                    // Reset button
                    returnSubmitBtn.innerHTML = originalText;
                    returnSubmitBtn.disabled = false;
                });
            });
        }
    }
    
    // Write review
    const reviewItemBtns = document.querySelectorAll('.review-item-btn');
    const reviewItemModal = document.getElementById('review-item-modal');
    
    if (reviewItemBtns.length > 0 && reviewItemModal) {
        const reviewItemForm = reviewItemModal.querySelector('form');
        const reviewRatingInputs = reviewItemModal.querySelectorAll('input[name="rating"]');
        const reviewTitleInput = document.getElementById('review-title');
        const reviewContentInput = document.getElementById('review-content');
        const reviewSubmitBtn = document.getElementById('review-submit-btn');
        const reviewItemIdInput = document.getElementById('review-item-id');
        const reviewProductIdInput = document.getElementById('review-product-id');
        
        if (reviewItemForm && reviewRatingInputs.length > 0 && reviewSubmitBtn && reviewItemIdInput && reviewProductIdInput) {
            // Handle review button click
            reviewItemBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    const itemId = this.getAttribute('data-item-id');
                    const productId = this.getAttribute('data-product-id');
                    
                    if (itemId && productId) {
                        reviewItemIdInput.value = itemId;
                        reviewProductIdInput.value = productId;
                        
                        // Reset form
                        reviewRatingInputs.forEach(input => {
                            input.checked = false;
                        });
                        if (reviewTitleInput) {
                            reviewTitleInput.value = '';
                        }
                        if (reviewContentInput) {
                            reviewContentInput.value = '';
                        }
                        reviewSubmitBtn.disabled = true;
                    }
                });
            });
            
            // Validate rating selection
            reviewRatingInputs.forEach(input => {
                input.addEventListener('change', function() {
                    reviewSubmitBtn.disabled = false;
                });
            });
            
            // Handle form submission
            reviewItemForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Check if rating is selected
                const selectedRating = reviewItemModal.querySelector('input[name="rating"]:checked');
                if (!selectedRating) {
                    window.marketplaceUtils.showToast('Please select a rating', 'error');
                    return;
                }
                
                // Show loading state
                reviewSubmitBtn.disabled = true;
                const originalText = reviewSubmitBtn.innerHTML;
                reviewSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';
                
                // Get form data
                const formData = new FormData(this);
                const productId = formData.get('product_id');
                
                // Send review
                fetch(`/products/${productId}/review/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.marketplaceUtils.getCsrfToken()
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        window.marketplaceUtils.showToast('Review submitted successfully', 'success');
                        
                        // Hide modal
                        const modalInstance = bootstrap.Modal.getInstance(reviewItemModal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                        
                        // Update review button
                        const reviewBtn = document.querySelector(`.review-item-btn[data-item-id="${formData.get('item_id')}"]`);
                        if (reviewBtn) {
                            reviewBtn.textContent = 'View Review';
                            reviewBtn.classList.remove('btn-primary');
                            reviewBtn.classList.add('btn-outline-primary');
                            reviewBtn.setAttribute('data-bs-toggle', '');
                            reviewBtn.setAttribute('data-bs-target', '');
                            
                            // Change click behavior to redirect to product page
                            reviewBtn.addEventListener('click', function(e) {
                                e.preventDefault();
                                window.location.href = `/products/${productId}/#reviews`;
                            }, { once: true });
                        }
                    } else {
                        // Show error message
                        window.marketplaceUtils.showToast(data.error || 'Failed to submit review', 'error');
                        
                        // Reset button
                        reviewSubmitBtn.innerHTML = originalText;
                        reviewSubmitBtn.disabled = false;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                    
                    // Reset button
                    reviewSubmitBtn.innerHTML = originalText;
                    reviewSubmitBtn.disabled = false;
                });
            });
        }
    }
    
    // Invoice download
    const downloadInvoiceBtn = document.getElementById('download-invoice-btn');
    
    if (downloadInvoiceBtn) {
        downloadInvoiceBtn.addEventListener('click', function() {
            // Show loading state
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
            
            const orderId = this.getAttribute('data-order-id');
            
            // Request invoice
            fetch(`/orders/${orderId}/invoice/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to generate invoice');
                    }
                    return response.blob();
                })
                .then(blob => {
                    // Create download link
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = `invoice-${orderId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    // Show success message
                    window.marketplaceUtils.showToast('Invoice downloaded successfully', 'success');
                })
                .catch(error => {
                    console.error('Error:', error);
                    window.marketplaceUtils.showToast('Failed to generate invoice. Please try again.', 'error');
                })
                .finally(() => {
                    // Reset button
                    this.innerHTML = originalText;
                    this.disabled = false;
                });
        });
    }
});