/**
 * User Profile Management JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Profile tabs functionality
    const profileTabs = document.querySelectorAll('.profile-tab');
    const profileTabContents = document.querySelectorAll('.profile-tab-content');
    
    if (profileTabs.length > 0 && profileTabContents.length > 0) {
        // Get active tab from URL hash or default to first tab
        let activeTabId = window.location.hash.substring(1) || profileTabs[0].getAttribute('data-tab');
        
        // Function to activate a tab
        function activateTab(tabId) {
            // Update active tab
            profileTabs.forEach(tab => {
                if (tab.getAttribute('data-tab') === tabId) {
                    tab.classList.add('active');
                } else {
                    tab.classList.remove('active');
                }
            });
            
            // Update active content
            profileTabContents.forEach(content => {
                if (content.id === tabId) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
            
            // Update URL hash
            window.history.replaceState(null, null, `#${tabId}`);
            
            // Store active tab in localStorage
            localStorage.setItem('activeProfileTab', tabId);
        }
        
        // Check localStorage for previously active tab
        const storedActiveTab = localStorage.getItem('activeProfileTab');
        if (storedActiveTab) {
            // Verify the tab exists
            const tabExists = Array.from(profileTabContents).some(content => content.id === storedActiveTab);
            if (tabExists) {
                activeTabId = storedActiveTab;
            }
        }
        
        // Activate initial tab
        activateTab(activeTabId);
        
        // Add click event listeners to tabs
        profileTabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                const tabId = this.getAttribute('data-tab');
                activateTab(tabId);
            });
        });
    }
    
    // Profile image upload
    const profileImageUpload = document.getElementById('profile-image-upload');
    const profileImageInput = document.getElementById('profile-image-input');
    const profileImagePreview = document.getElementById('profile-image-preview');
    const removeProfileImageBtn = document.getElementById('remove-profile-image');
    
    if (profileImageUpload && profileImageInput && profileImagePreview) {
        // Handle click on profile image to trigger file input
        profileImageUpload.addEventListener('click', function() {
            profileImageInput.click();
        });
        
        // Handle file selection
        profileImageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                
                // Check file type
                const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
                if (!validTypes.includes(file.type)) {
                    window.marketplaceUtils.showToast('Please select a valid image file (JPEG, PNG, GIF)', 'error');
                    return;
                }
                
                // Check file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    window.marketplaceUtils.showToast('Image size should be less than 5MB', 'error');
                    return;
                }
                
                // Preview image
                const reader = new FileReader();
                reader.onload = function(e) {
                    profileImagePreview.src = e.target.result;
                    
                    // Show remove button if it exists
                    if (removeProfileImageBtn) {
                        removeProfileImageBtn.classList.remove('d-none');
                    }
                    
                    // Show save button
                    const saveImageBtn = document.getElementById('save-profile-image');
                    if (saveImageBtn) {
                        saveImageBtn.classList.remove('d-none');
                    }
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Handle remove profile image
        if (removeProfileImageBtn) {
            removeProfileImageBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Reset file input
                profileImageInput.value = '';
                
                // Reset preview to default image
                profileImagePreview.src = profileImagePreview.getAttribute('data-default-image') || '/static/img/default-profile.png';
                
                // Hide remove button
                this.classList.add('d-none');
                
                // Show save button with remove flag
                const saveImageBtn = document.getElementById('save-profile-image');
                if (saveImageBtn) {
                    saveImageBtn.classList.remove('d-none');
                    saveImageBtn.setAttribute('data-remove', 'true');
                }
            });
        }
        
        // Handle save profile image
        const saveImageBtn = document.getElementById('save-profile-image');
        if (saveImageBtn) {
            saveImageBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Show loading state
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
                
                // Create form data
                const formData = new FormData();
                
                // Check if removing image
                const isRemoving = this.getAttribute('data-remove') === 'true';
                
                if (isRemoving) {
                    formData.append('remove_image', 'true');
                } else if (profileImageInput.files && profileImageInput.files[0]) {
                    formData.append('profile_image', profileImageInput.files[0]);
                } else {
                    // No changes
                    this.innerHTML = originalText;
                    this.disabled = false;
                    this.classList.add('d-none');
                    return;
                }
                
                // Send request to update profile image
                fetch('/accounts/update-profile-image/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.marketplaceUtils.getCsrfToken()
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.marketplaceUtils.showToast('Profile image updated successfully', 'success');
                        
                        // Update all profile images on the page
                        const profileImages = document.querySelectorAll('.user-profile-image');
                        profileImages.forEach(img => {
                            // Add timestamp to prevent caching
                            img.src = data.image_url + '?t=' + new Date().getTime();
                        });
                        
                        // Reset data-remove attribute
                        this.removeAttribute('data-remove');
                        
                        // Hide save button
                        this.classList.add('d-none');
                        
                        // Show/hide remove button based on whether there's a custom image
                        if (removeProfileImageBtn) {
                            if (data.has_image) {
                                removeProfileImageBtn.classList.remove('d-none');
                            } else {
                                removeProfileImageBtn.classList.add('d-none');
                            }
                        }
                    } else {
                        window.marketplaceUtils.showToast(data.error || 'Failed to update profile image', 'error');
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
            });
        }
    }
    
    // Address management
    const addAddressBtn = document.getElementById('add-address-btn');
    const addressForm = document.getElementById('address-form');
    const addressList = document.getElementById('address-list');
    const cancelAddressBtn = document.getElementById('cancel-address-btn');
    
    if (addAddressBtn && addressForm) {
        // Show address form when add button is clicked
        addAddressBtn.addEventListener('click', function() {
            // Reset form
            addressForm.reset();
            
            // Clear hidden ID field
            const addressIdInput = addressForm.querySelector('input[name="address_id"]');
            if (addressIdInput) {
                addressIdInput.value = '';
            }
            
            // Update form title and button text
            const formTitle = addressForm.querySelector('.address-form-title');
            if (formTitle) {
                formTitle.textContent = 'Add New Address';
            }
            
            const submitBtn = addressForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = 'Add Address';
            }
            
            // Show form
            addressForm.classList.remove('d-none');
            
            // Hide add button
            this.classList.add('d-none');
            
            // Scroll to form
            addressForm.scrollIntoView({ behavior: 'smooth' });
        });
        
        // Hide address form when cancel button is clicked
        if (cancelAddressBtn) {
            cancelAddressBtn.addEventListener('click', function() {
                // Hide form
                addressForm.classList.add('d-none');
                
                // Show add button
                if (addAddressBtn) {
                    addAddressBtn.classList.remove('d-none');
                }
            });
        }
        
        // Handle edit address
        if (addressList) {
            addressList.addEventListener('click', function(e) {
                // Check if edit button was clicked
                if (e.target.classList.contains('edit-address-btn') || e.target.closest('.edit-address-btn')) {
                    e.preventDefault();
                    
                    // Get address card
                    const addressBtn = e.target.closest('.edit-address-btn');
                    const addressCard = addressBtn.closest('.address-card');
                    const addressId = addressBtn.getAttribute('data-address-id');
                    
                    if (addressId) {
                        // Show loading state
                        addressBtn.disabled = true;
                        const originalText = addressBtn.innerHTML;
                        addressBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                        
                        // Fetch address details
                        fetch(`/accounts/address/${addressId}/`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    // Populate form with address details
                                    const address = data.address;
                                    
                                    // Set form fields
                                    for (const key in address) {
                                        const input = addressForm.querySelector(`[name="${key}"]`);
                                        if (input) {
                                            input.value = address[key];
                                        }
                                    }
                                    
                                    // Update form title and button text
                                    const formTitle = addressForm.querySelector('.address-form-title');
                                    if (formTitle) {
                                        formTitle.textContent = 'Edit Address';
                                    }
                                    
                                    const submitBtn = addressForm.querySelector('button[type="submit"]');
                                    if (submitBtn) {
                                        submitBtn.textContent = 'Update Address';
                                    }
                                    
                                    // Show form
                                    addressForm.classList.remove('d-none');
                                    
                                    // Hide add button
                                    if (addAddressBtn) {
                                        addAddressBtn.classList.add('d-none');
                                    }
                                    
                                    // Scroll to form
                                    addressForm.scrollIntoView({ behavior: 'smooth' });
                                } else {
                                    window.marketplaceUtils.showToast(data.error || 'Failed to load address details', 'error');
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                            })
                            .finally(() => {
                                // Reset button
                                addressBtn.innerHTML = originalText;
                                addressBtn.disabled = false;
                            });
                    }
                }
                
                // Check if delete button was clicked
                if (e.target.classList.contains('delete-address-btn') || e.target.closest('.delete-address-btn')) {
                    e.preventDefault();
                    
                    // Get address card
                    const addressBtn = e.target.closest('.delete-address-btn');
                    const addressCard = addressBtn.closest('.address-card');
                    const addressId = addressBtn.getAttribute('data-address-id');
                    
                    if (addressId && confirm('Are you sure you want to delete this address?')) {
                        // Show loading state
                        addressBtn.disabled = true;
                        const originalText = addressBtn.innerHTML;
                        addressBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                        
                        // Delete address
                        fetch(`/accounts/address/${addressId}/delete/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': window.marketplaceUtils.getCsrfToken()
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Remove address card with animation
                                addressCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                                addressCard.style.opacity = '0';
                                addressCard.style.transform = 'translateY(-10px)';
                                
                                setTimeout(() => {
                                    addressCard.remove();
                                    
                                    // Show message if no addresses left
                                    if (addressList.querySelectorAll('.address-card').length === 0) {
                                        const noAddressMsg = document.createElement('div');
                                        noAddressMsg.className = 'alert alert-info';
                                        noAddressMsg.textContent = 'You have no saved addresses.';
                                        addressList.appendChild(noAddressMsg);
                                    }
                                }, 300);
                                
                                window.marketplaceUtils.showToast('Address deleted successfully', 'success');
                            } else {
                                window.marketplaceUtils.showToast(data.error || 'Failed to delete address', 'error');
                                
                                // Reset button
                                addressBtn.innerHTML = originalText;
                                addressBtn.disabled = false;
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                            
                            // Reset button
                            addressBtn.innerHTML = originalText;
                            addressBtn.disabled = false;
                        });
                    }
                }
                
                // Check if set default button was clicked
                if (e.target.classList.contains('set-default-address-btn') || e.target.closest('.set-default-address-btn')) {
                    e.preventDefault();
                    
                    // Get address card
                    const addressBtn = e.target.closest('.set-default-address-btn');
                    const addressCard = addressBtn.closest('.address-card');
                    const addressId = addressBtn.getAttribute('data-address-id');
                    
                    if (addressId) {
                        // Show loading state
                        addressBtn.disabled = true;
                        const originalText = addressBtn.innerHTML;
                        addressBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                        
                        // Set as default
                        fetch(`/accounts/address/${addressId}/set-default/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': window.marketplaceUtils.getCsrfToken()
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Remove default badge from all addresses
                                const defaultBadges = addressList.querySelectorAll('.default-badge');
                                defaultBadges.forEach(badge => badge.remove());
                                
                                // Remove set default button from all addresses
                                const setDefaultBtns = addressList.querySelectorAll('.set-default-address-btn');
                                setDefaultBtns.forEach(btn => {
                                    btn.closest('.address-card-actions').appendChild(btn);
                                });
                                
                                // Add default badge to this address
                                const addressHeader = addressCard.querySelector('.address-card-header');
                                if (addressHeader) {
                                    const defaultBadge = document.createElement('span');
                                    defaultBadge.className = 'badge bg-primary ms-2 default-badge';
                                    defaultBadge.textContent = 'Default';
                                    addressHeader.appendChild(defaultBadge);
                                }
                                
                                // Remove set default button from this address
                                addressBtn.remove();
                                
                                window.marketplaceUtils.showToast('Default address updated successfully', 'success');
                            } else {
                                window.marketplaceUtils.showToast(data.error || 'Failed to update default address', 'error');
                                
                                // Reset button
                                addressBtn.innerHTML = originalText;
                                addressBtn.disabled = false;
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                            
                            // Reset button
                            addressBtn.innerHTML = originalText;
                            addressBtn.disabled = false;
                        });
                    }
                }
            });
        }
        
        // Handle address form submission
        addressForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(this);
            const addressId = formData.get('address_id');
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            }
            
            // Determine URL based on whether we're adding or editing
            const url = addressId ? `/accounts/address/${addressId}/update/` : '/accounts/address/add/';
            
            // Send request
            fetch(url, {
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
                    window.marketplaceUtils.showToast(addressId ? 'Address updated successfully' : 'Address added successfully', 'success');
                    
                    // Reload the page to show updated address list
                    window.location.reload();
                } else {
                    // Show error message
                    window.marketplaceUtils.showToast(data.error || 'Failed to save address', 'error');
                    
                    // Display field errors if any
                    if (data.field_errors) {
                        for (const field in data.field_errors) {
                            const input = this.querySelector(`[name="${field}"]`);
                            if (input) {
                                input.classList.add('is-invalid');
                                
                                // Add or update error message
                                let errorDiv = input.nextElementSibling;
                                if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                                    errorDiv = document.createElement('div');
                                    errorDiv.className = 'invalid-feedback';
                                    input.parentNode.insertBefore(errorDiv, input.nextSibling);
                                }
                                errorDiv.textContent = data.field_errors[field];
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
            })
            .finally(() => {
                // Reset button
                if (submitBtn) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            });
        });
        
        // Clear validation errors when input changes
        addressForm.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
                const errorDiv = this.nextElementSibling;
                if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv.textContent = '';
                }
            });
        });
    }
    
    // Password change form
    const passwordForm = document.getElementById('password-change-form');
    
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(this);
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            }
            
            // Send request
            fetch('/accounts/change-password/', {
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
                    window.marketplaceUtils.showToast('Password changed successfully', 'success');
                    
                    // Reset form
                    this.reset();
                    
                    // Remove any validation errors
                    this.querySelectorAll('.is-invalid').forEach(input => {
                        input.classList.remove('is-invalid');
                    });
                    
                    this.querySelectorAll('.invalid-feedback').forEach(div => {
                        div.textContent = '';
                    });
                } else {
                    // Show error message
                    window.marketplaceUtils.showToast(data.error || 'Failed to change password', 'error');
                    
                    // Display field errors if any
                    if (data.field_errors) {
                        for (const field in data.field_errors) {
                            const input = this.querySelector(`[name="${field}"]`);
                            if (input) {
                                input.classList.add('is-invalid');
                                
                                // Add or update error message
                                let errorDiv = input.nextElementSibling;
                                if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                                    errorDiv = document.createElement('div');
                                    errorDiv.className = 'invalid-feedback';
                                    input.parentNode.insertBefore(errorDiv, input.nextSibling);
                                }
                                errorDiv.textContent = data.field_errors[field];
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
            })
            .finally(() => {
                // Reset button
                if (submitBtn) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            });
        });
        
        // Clear validation errors when input changes
        passwordForm.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
                const errorDiv = this.nextElementSibling;
                if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv.textContent = '';
                }
            });
        });
        
        // Password strength meter
        const newPasswordInput = passwordForm.querySelector('input[name="new_password1"]');
        const strengthMeter = document.getElementById('password-strength-meter');
        const strengthText = document.getElementById('password-strength-text');
        
        if (newPasswordInput && strengthMeter && strengthText) {
            newPasswordInput.addEventListener('input', function() {
                const password = this.value;
                let strength = 0;
                let feedback = '';
                
                if (password.length >= 8) {
                    strength += 1;
                }
                
                if (password.match(/[A-Z]/)) {
                    strength += 1;
                }
                
                if (password.match(/[a-z]/)) {
                    strength += 1;
                }
                
                if (password.match(/[0-9]/)) {
                    strength += 1;
                }
                
                if (password.match(/[^A-Za-z0-9]/)) {
                    strength += 1;
                }
                
                // Update meter and text
                strengthMeter.value = strength;
                
                switch (strength) {
                    case 0:
                        strengthText.textContent = 'Very Weak';
                        strengthText.className = 'text-danger';
                        break;
                    case 1:
                        strengthText.textContent = 'Weak';
                        strengthText.className = 'text-danger';
                        break;
                    case 2:
                        strengthText.textContent = 'Fair';
                        strengthText.className = 'text-warning';
                        break;
                    case 3:
                        strengthText.textContent = 'Good';
                        strengthText.className = 'text-info';
                        break;
                    case 4:
                        strengthText.textContent = 'Strong';
                        strengthText.className = 'text-success';
                        break;
                    case 5:
                        strengthText.textContent = 'Very Strong';
                        strengthText.className = 'text-success';
                        break;
                }
            });
        }
    }
});