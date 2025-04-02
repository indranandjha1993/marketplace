/**
 * Vendor Product Management JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Product form validation
    const productForm = document.getElementById('product-form');
    
    if (productForm) {
        // Handle form submission
        productForm.addEventListener('submit', function(e) {
            // Prevent default submission
            e.preventDefault();
            
            // Validate form
            if (!validateProductForm()) {
                // Scroll to first error
                const firstError = document.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return;
            }
            
            // Show loading state
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            }
            
            // Submit form
            this.submit();
        });
        
        // Clear validation errors when input changes
        const inputs = productForm.querySelectorAll('input, select, textarea');
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
    
    // Validate product form
    function validateProductForm() {
        let isValid = true;
        
        // Get form elements
        const title = document.getElementById('id_title');
        const description = document.getElementById('id_description');
        const price = document.getElementById('id_price');
        const quantity = document.getElementById('id_quantity');
        const category = document.getElementById('id_category');
        
        // Validate required fields
        if (title && !title.value.trim()) {
            showError(title, 'Product title is required');
            isValid = false;
        }
        
        if (description && !description.value.trim()) {
            showError(description, 'Product description is required');
            isValid = false;
        }
        
        if (price) {
            if (!price.value.trim()) {
                showError(price, 'Price is required');
                isValid = false;
            } else if (isNaN(parseFloat(price.value)) || parseFloat(price.value) <= 0) {
                showError(price, 'Please enter a valid price');
                isValid = false;
            }
        }
        
        if (quantity) {
            if (!quantity.value.trim()) {
                showError(quantity, 'Quantity is required');
                isValid = false;
            } else if (isNaN(parseInt(quantity.value)) || parseInt(quantity.value) < 0) {
                showError(quantity, 'Please enter a valid quantity');
                isValid = false;
            }
        }
        
        if (category && !category.value) {
            showError(category, 'Category is required');
            isValid = false;
        }
        
        return isValid;
    }
    
    // Show error message for an input
    function showError(input, message) {
        input.classList.add('is-invalid');
        
        // Add or update error message
        let errorDiv = input.nextElementSibling;
        if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            input.parentNode.insertBefore(errorDiv, input.nextSibling);
        }
        
        errorDiv.textContent = message;
    }
    
    // Product image upload
    const imageUploadContainer = document.getElementById('product-images-container');
    const imageUploadInput = document.getElementById('product-image-upload');
    const imagePreviewContainer = document.getElementById('product-image-previews');
    
    if (imageUploadContainer && imageUploadInput && imagePreviewContainer) {
        // Handle click on upload button
        imageUploadContainer.addEventListener('click', function() {
            imageUploadInput.click();
        });
        
        // Handle file selection
        imageUploadInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                // Check if we've reached the maximum number of images
                const existingImages = imagePreviewContainer.querySelectorAll('.product-image-preview').length;
                const maxImages = parseInt(imageUploadContainer.getAttribute('data-max-images') || 5);
                
                if (existingImages + this.files.length > maxImages) {
                    window.marketplaceUtils.showToast(`You can upload a maximum of ${maxImages} images`, 'error');
                    return;
                }
                
                // Process each selected file
                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];
                    
                    // Check file type
                    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
                    if (!validTypes.includes(file.type)) {
                        window.marketplaceUtils.showToast('Please select a valid image file (JPEG, PNG, GIF)', 'error');
                        continue;
                    }
                    
                    // Check file size (max 5MB)
                    if (file.size > 5 * 1024 * 1024) {
                        window.marketplaceUtils.showToast('Image size should be less than 5MB', 'error');
                        continue;
                    }
                    
                    // Create preview
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const previewDiv = document.createElement('div');
                        previewDiv.className = 'product-image-preview';
                        
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'product-image-preview-img';
                        
                        const actions = document.createElement('div');
                        actions.className = 'product-image-preview-actions';
                        
                        const primaryBtn = document.createElement('button');
                        primaryBtn.type = 'button';
                        primaryBtn.className = 'btn btn-sm btn-outline-primary set-primary-btn';
                        primaryBtn.innerHTML = '<i class="fas fa-star"></i>';
                        primaryBtn.title = 'Set as primary image';
                        primaryBtn.addEventListener('click', setPrimaryImage);
                        
                        const removeBtn = document.createElement('button');
                        removeBtn.type = 'button';
                        removeBtn.className = 'btn btn-sm btn-outline-danger remove-image-btn';
                        removeBtn.innerHTML = '<i class="fas fa-trash"></i>';
                        removeBtn.title = 'Remove image';
                        removeBtn.addEventListener('click', removeImage);
                        
                        actions.appendChild(primaryBtn);
                        actions.appendChild(removeBtn);
                        
                        previewDiv.appendChild(img);
                        previewDiv.appendChild(actions);
                        
                        // Create hidden input for the file
                        const hiddenInput = document.createElement('input');
                        hiddenInput.type = 'file';
                        hiddenInput.name = 'product_images';
                        hiddenInput.className = 'd-none';
                        hiddenInput.required = false;
                        
                        // Create a new FileList containing only this file
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(file);
                        hiddenInput.files = dataTransfer.files;
                        
                        previewDiv.appendChild(hiddenInput);
                        
                        // Add to preview container
                        imagePreviewContainer.appendChild(previewDiv);
                        
                        // Update upload container state
                        updateImageUploadState();
                    };
                    reader.readAsDataURL(file);
                }
                
                // Reset file input
                this.value = '';
            }
        });
        
        // Set primary image
        function setPrimaryImage() {
            const previewDiv = this.closest('.product-image-preview');
            
            // Remove primary class from all previews
            const allPreviews = imagePreviewContainer.querySelectorAll('.product-image-preview');
            allPreviews.forEach(preview => {
                preview.classList.remove('primary');
                
                // Update primary button
                const primaryBtn = preview.querySelector('.set-primary-btn');
                if (primaryBtn) {
                    primaryBtn.innerHTML = '<i class="fas fa-star"></i>';
                    primaryBtn.title = 'Set as primary image';
                }
            });
            
            // Add primary class to this preview
            previewDiv.classList.add('primary');
            
            // Update primary button
            this.innerHTML = '<i class="fas fa-check"></i>';
            this.title = 'Primary image';
            
            // Update hidden input for primary image
            let primaryImageInput = document.getElementById('primary-image-input');
            if (!primaryImageInput) {
                primaryImageInput = document.createElement('input');
                primaryImageInput.type = 'hidden';
                primaryImageInput.id = 'primary-image-input';
                primaryImageInput.name = 'primary_image';
                productForm.appendChild(primaryImageInput);
            }
            
            // Set value to the index of this preview
            const index = Array.from(allPreviews).indexOf(previewDiv);
            primaryImageInput.value = index;
        }
        
        // Remove image
        function removeImage() {
            const previewDiv = this.closest('.product-image-preview');
            
            // Check if this is the primary image
            if (previewDiv.classList.contains('primary')) {
                // Clear primary image input
                const primaryImageInput = document.getElementById('primary-image-input');
                if (primaryImageInput) {
                    primaryImageInput.value = '';
                }
            }
            
            // Remove preview
            previewDiv.remove();
            
            // Update upload container state
            updateImageUploadState();
        }
        
        // Update image upload container state
        function updateImageUploadState() {
            const existingImages = imagePreviewContainer.querySelectorAll('.product-image-preview').length;
            const maxImages = parseInt(imageUploadContainer.getAttribute('data-max-images') || 5);
            
            if (existingImages >= maxImages) {
                imageUploadContainer.classList.add('disabled');
                imageUploadContainer.querySelector('.upload-text').textContent = 'Maximum images reached';
            } else {
                imageUploadContainer.classList.remove('disabled');
                imageUploadContainer.querySelector('.upload-text').textContent = 'Click to upload images';
            }
        }
        
        // Initialize existing images
        const existingImages = imagePreviewContainer.querySelectorAll('.product-image-preview');
        existingImages.forEach(preview => {
            // Add event listeners to buttons
            const primaryBtn = preview.querySelector('.set-primary-btn');
            if (primaryBtn) {
                primaryBtn.addEventListener('click', setPrimaryImage);
            }
            
            const removeBtn = preview.querySelector('.remove-image-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', removeImage);
            }
        });
        
        // Initialize upload container state
        updateImageUploadState();
    }
    
    // Product variants
    const variantsContainer = document.getElementById('variants-container');
    const addVariantBtn = document.getElementById('add-variant-btn');
    const variantTemplate = document.getElementById('variant-template');
    
    if (variantsContainer && addVariantBtn && variantTemplate) {
        // Add new variant
        addVariantBtn.addEventListener('click', function() {
            // Clone template
            const newVariant = variantTemplate.content.cloneNode(true);
            
            // Set unique IDs and names
            const variantIndex = variantsContainer.querySelectorAll('.variant-item').length;
            
            // Update IDs and names
            const inputs = newVariant.querySelectorAll('input, select');
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                if (name) {
                    input.setAttribute('name', name.replace('__index__', variantIndex));
                }
                
                const id = input.getAttribute('id');
                if (id) {
                    input.setAttribute('id', id.replace('__index__', variantIndex));
                }
            });
            
            // Add event listener to remove button
            const removeBtn = newVariant.querySelector('.remove-variant-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', removeVariant);
            }
            
            // Add to container
            variantsContainer.appendChild(newVariant);
            
            // Initialize price inputs
            const priceInputs = variantsContainer.querySelectorAll('.variant-price');
            priceInputs.forEach(input => {
                input.addEventListener('input', function() {
                    // Format as currency
                    const value = this.value.replace(/[^\d.]/g, '');
                    this.value = value;
                });
            });
            
            // Initialize stock inputs
            const stockInputs = variantsContainer.querySelectorAll('.variant-stock');
            stockInputs.forEach(input => {
                input.addEventListener('input', function() {
                    // Allow only numbers
                    const value = this.value.replace(/[^\d]/g, '');
                    this.value = value;
                });
            });
        });
        
        // Remove variant
        function removeVariant() {
            const variantItem = this.closest('.variant-item');
            
            // Remove with animation
            variantItem.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            variantItem.style.opacity = '0';
            variantItem.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                variantItem.remove();
            }, 300);
        }
        
        // Initialize existing variants
        const existingVariants = variantsContainer.querySelectorAll('.variant-item');
        existingVariants.forEach(variant => {
            // Add event listener to remove button
            const removeBtn = variant.querySelector('.remove-variant-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', removeVariant);
            }
        });
        
        // Initialize price inputs
        const priceInputs = variantsContainer.querySelectorAll('.variant-price');
        priceInputs.forEach(input => {
            input.addEventListener('input', function() {
                // Format as currency
                const value = this.value.replace(/[^\d.]/g, '');
                this.value = value;
            });
        });
        
        // Initialize stock inputs
        const stockInputs = variantsContainer.querySelectorAll('.variant-stock');
        stockInputs.forEach(input => {
            input.addEventListener('input', function() {
                // Allow only numbers
                const value = this.value.replace(/[^\d]/g, '');
                this.value = value;
            });
        });
    }
    
    // Rich text editor for description
    const descriptionTextarea = document.getElementById('id_description');
    
    if (descriptionTextarea && window.ClassicEditor) {
        ClassicEditor
            .create(descriptionTextarea, {
                toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', '|', 'undo', 'redo'],
                placeholder: 'Enter product description...'
            })
            .catch(error => {
                console.error('Error initializing editor:', error);
            });
    }
    
    // Product bulk actions
    const bulkActionForm = document.getElementById('bulk-action-form');
    const bulkActionSelect = document.getElementById('bulk-action');
    const bulkActionBtn = document.getElementById('apply-bulk-action');
    const selectAllCheckbox = document.getElementById('select-all');
    const productCheckboxes = document.querySelectorAll('.product-checkbox');
    
    if (bulkActionForm && bulkActionSelect && bulkActionBtn && selectAllCheckbox && productCheckboxes.length > 0) {
        // Handle select all checkbox
        selectAllCheckbox.addEventListener('change', function() {
            productCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            
            // Update bulk action button state
            updateBulkActionState();
        });
        
        // Handle individual checkboxes
        productCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // Update select all checkbox
                selectAllCheckbox.checked = Array.from(productCheckboxes).every(cb => cb.checked);
                
                // Update bulk action button state
                updateBulkActionState();
            });
        });
        
        // Handle bulk action selection
        bulkActionSelect.addEventListener('change', function() {
            // Update bulk action button state
            updateBulkActionState();
        });
        
        // Handle bulk action form submission
        bulkActionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get selected action
            const action = bulkActionSelect.value;
            
            // Get selected products
            const selectedProducts = Array.from(productCheckboxes)
                .filter(checkbox => checkbox.checked)
                .map(checkbox => checkbox.value);
            
            if (!action || selectedProducts.length === 0) {
                return;
            }
            
            // Confirm action
            let confirmMessage = '';
            
            switch (action) {
                case 'delete':
                    confirmMessage = `Are you sure you want to delete ${selectedProducts.length} product(s)?`;
                    break;
                case 'activate':
                    confirmMessage = `Are you sure you want to activate ${selectedProducts.length} product(s)?`;
                    break;
                case 'deactivate':
                    confirmMessage = `Are you sure you want to deactivate ${selectedProducts.length} product(s)?`;
                    break;
                default:
                    confirmMessage = `Are you sure you want to ${action} ${selectedProducts.length} product(s)?`;
            }
            
            if (!confirm(confirmMessage)) {
                return;
            }
            
            // Show loading state
            bulkActionBtn.disabled = true;
            const originalText = bulkActionBtn.innerHTML;
            bulkActionBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            
            // Create form data
            const formData = new FormData();
            formData.append('action', action);
            selectedProducts.forEach(productId => {
                formData.append('products', productId);
            });
            
            // Send request
            fetch('/vendor/products/bulk-action/', {
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
                    window.marketplaceUtils.showToast(data.message || 'Bulk action completed successfully', 'success');
                    
                    // Reload page after a short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // Show error message
                    window.marketplaceUtils.showToast(data.error || 'Failed to perform bulk action', 'error');
                    
                    // Reset button
                    bulkActionBtn.innerHTML = originalText;
                    bulkActionBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                
                // Reset button
                bulkActionBtn.innerHTML = originalText;
                bulkActionBtn.disabled = false;
            });
        });
        
        // Update bulk action button state
        function updateBulkActionState() {
            const selectedProducts = Array.from(productCheckboxes).filter(checkbox => checkbox.checked);
            const action = bulkActionSelect.value;
            
            bulkActionBtn.disabled = selectedProducts.length === 0 || !action;
        }
        
        // Initialize bulk action button state
        updateBulkActionState();
    }
    
    // Product search and filter
    const productSearchForm = document.getElementById('product-search-form');
    const productSearchInput = document.getElementById('product-search');
    const productFilterSelect = document.getElementById('product-filter');
    const productSortSelect = document.getElementById('product-sort');
    
    if (productSearchForm && productSearchInput) {
        // Handle search input
        productSearchInput.addEventListener('input', function() {
            // Add debounce to prevent too many requests
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                productSearchForm.submit();
            }, 500);
        });
        
        // Handle filter and sort changes
        if (productFilterSelect) {
            productFilterSelect.addEventListener('change', function() {
                productSearchForm.submit();
            });
        }
        
        if (productSortSelect) {
            productSortSelect.addEventListener('change', function() {
                productSearchForm.submit();
            });
        }
    }
    
    // Product quick edit
    const quickEditBtns = document.querySelectorAll('.quick-edit-btn');
    const quickEditModal = document.getElementById('quick-edit-modal');
    
    if (quickEditBtns.length > 0 && quickEditModal) {
        quickEditBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const productId = this.getAttribute('data-product-id');
                
                if (productId) {
                    // Show loading state
                    const modalBody = quickEditModal.querySelector('.modal-body');
                    modalBody.innerHTML = `
                        <div class="text-center py-5">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-3">Loading product details...</p>
                        </div>
                    `;
                    
                    // Fetch product details
                    fetch(`/vendor/products/${productId}/quick-edit/`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Update modal content
                                modalBody.innerHTML = data.html;
                                
                                // Initialize form elements
                                initQuickEditForm();
                            } else {
                                modalBody.innerHTML = `
                                    <div class="alert alert-danger">
                                        ${data.error || 'Failed to load product details'}
                                    </div>
                                `;
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            modalBody.innerHTML = `
                                <div class="alert alert-danger">
                                    An error occurred. Please try again.
                                </div>
                            `;
                        });
                }
            });
        });
        
        // Initialize quick edit form
        function initQuickEditForm() {
            const quickEditForm = quickEditModal.querySelector('form');
            
            if (quickEditForm) {
                // Handle form submission
                quickEditForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    // Show loading state
                    const submitBtn = this.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        const originalText = submitBtn.innerHTML;
                        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
                    }
                    
                    // Get form data
                    const formData = new FormData(this);
                    
                    // Send request
                    fetch(this.action, {
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
                            window.marketplaceUtils.showToast(data.message || 'Product updated successfully', 'success');
                            
                            // Close modal
                            const modalInstance = bootstrap.Modal.getInstance(quickEditModal);
                            if (modalInstance) {
                                modalInstance.hide();
                            }
                            
                            // Reload page after a short delay
                            setTimeout(() => {
                                window.location.reload();
                            }, 1000);
                        } else {
                            // Show error message
                            window.marketplaceUtils.showToast(data.error || 'Failed to update product', 'error');
                            
                            // Display field errors if any
                            if (data.field_errors) {
                                for (const field in data.field_errors) {
                                    const input = quickEditForm.querySelector(`[name="${field}"]`);
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
                            
                            // Reset button
                            if (submitBtn) {
                                submitBtn.innerHTML = originalText;
                                submitBtn.disabled = false;
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                        
                        // Reset button
                        if (submitBtn) {
                            submitBtn.innerHTML = originalText;
                            submitBtn.disabled = false;
                        }
                    });
                });
                
                // Initialize price inputs
                const priceInputs = quickEditForm.querySelectorAll('.price-input');
                priceInputs.forEach(input => {
                    input.addEventListener('input', function() {
                        // Format as currency
                        const value = this.value.replace(/[^\d.]/g, '');
                        this.value = value;
                    });
                });
                
                // Initialize stock inputs
                const stockInputs = quickEditForm.querySelectorAll('.stock-input');
                stockInputs.forEach(input => {
                    input.addEventListener('input', function() {
                        // Allow only numbers
                        const value = this.value.replace(/[^\d]/g, '');
                        this.value = value;
                    });
                });
            }
        }
    }
});