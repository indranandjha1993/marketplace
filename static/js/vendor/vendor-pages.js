/**
 * Vendor Pages JavaScript
 * Handles functionality for vendor list, detail, and become vendor pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Vendor List Page
    initVendorListPage();
    
    // Vendor Detail Page
    initVendorDetailPage();
    
    // Become Vendor Page
    initBecomeVendorPage();
});

/**
 * Initialize vendor list page functionality
 */
function initVendorListPage() {
    // Add any specific functionality for the vendor list page
    const vendorCards = document.querySelectorAll('.vendor-card');
    
    if (vendorCards.length) {
        // Add hover effects or other interactions if needed
        vendorCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                // Additional hover effects beyond CSS if needed
            });
        });
    }
}

/**
 * Initialize vendor detail page functionality
 */
function initVendorDetailPage() {
    // Add any specific functionality for the vendor detail page
    const sortSelect = document.querySelector('.vendor-sort-select');
    
    if (sortSelect) {
        // Handle sort selection change
        sortSelect.addEventListener('change', function() {
            window.location.href = this.value;
        });
    }
}

/**
 * Initialize become vendor page functionality
 */
function initBecomeVendorPage() {
    // Form validation for become vendor page
    const becomeVendorForm = document.querySelector('.become-vendor-form');
    
    if (becomeVendorForm) {
        becomeVendorForm.addEventListener('submit', function(e) {
            // Validate form fields
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    // Add validation styling
                    field.classList.add('is-invalid');
                    
                    // Create error message if it doesn't exist
                    let errorDiv = field.nextElementSibling;
                    if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        field.parentNode.insertBefore(errorDiv, field.nextSibling);
                    }
                    
                    errorDiv.textContent = 'This field is required';
                }
            });
            
            // Validate file inputs
            const fileInputs = this.querySelectorAll('input[type="file"][required]');
            fileInputs.forEach(input => {
                if (input.files.length === 0) {
                    isValid = false;
                    // Add validation styling
                    input.classList.add('is-invalid');
                    
                    // Create error message if it doesn't exist
                    let errorDiv = input.nextElementSibling;
                    if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        input.parentNode.insertBefore(errorDiv, input.nextSibling);
                    }
                    
                    errorDiv.textContent = 'Please upload a file';
                }
            });
            
            // Validate terms checkbox
            const termsCheckbox = this.querySelector('#terms');
            if (termsCheckbox && !termsCheckbox.checked) {
                isValid = false;
                // Add validation styling
                termsCheckbox.classList.add('is-invalid');
                
                // Create error message if it doesn't exist
                let errorDiv = termsCheckbox.nextElementSibling.nextElementSibling;
                if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    termsCheckbox.parentNode.appendChild(errorDiv);
                }
                
                errorDiv.textContent = 'You must agree to the terms and conditions';
            }
            
            if (!isValid) {
                e.preventDefault();
                
                // Scroll to first error
                const firstError = document.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
        
        // Clear validation errors when input changes
        const inputs = becomeVendorForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
                const errorFeedback = this.nextElementSibling;
                if (errorFeedback && errorFeedback.classList.contains('invalid-feedback')) {
                    errorFeedback.textContent = '';
                }
            });
        });
    }
}