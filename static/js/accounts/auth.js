/**
 * Authentication Pages JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Login Form
    const loginForm = document.getElementById('login-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // Clear previous error messages
            const errorAlert = document.getElementById('login-error');
            if (errorAlert) {
                errorAlert.classList.add('d-none');
                errorAlert.textContent = '';
            }
            
            // Get form inputs
            const emailInput = document.getElementById('id_login');
            const passwordInput = document.getElementById('id_password');
            
            // Basic validation
            let hasError = false;
            
            if (!emailInput.value.trim()) {
                emailInput.classList.add('is-invalid');
                hasError = true;
            } else {
                emailInput.classList.remove('is-invalid');
            }
            
            if (!passwordInput.value.trim()) {
                passwordInput.classList.add('is-invalid');
                hasError = true;
            } else {
                passwordInput.classList.remove('is-invalid');
            }
            
            if (hasError) {
                e.preventDefault();
                if (errorAlert) {
                    errorAlert.textContent = 'Please fill in all required fields.';
                    errorAlert.classList.remove('d-none');
                }
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Signing in...';
            }
        });
        
        // Clear validation errors when input changes
        const inputs = loginForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
                
                // Hide error alert if all fields are valid
                const invalidInputs = loginForm.querySelectorAll('.is-invalid');
                if (invalidInputs.length === 0) {
                    const errorAlert = document.getElementById('login-error');
                    if (errorAlert) {
                        errorAlert.classList.add('d-none');
                    }
                }
            });
        });
    }
    
    // Registration Form
    const registerForm = document.getElementById('register-form');
    
    if (registerForm) {
        // Password strength meter
        const passwordInput = document.getElementById('id_password1');
        const strengthMeter = document.getElementById('password-strength-meter');
        const strengthText = document.getElementById('password-strength-text');
        
        if (passwordInput && strengthMeter && strengthText) {
            passwordInput.addEventListener('input', function() {
                const password = this.value;
                let strength = 0;
                
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
        
        // Password confirmation match check
        const password1Input = document.getElementById('id_password1');
        const password2Input = document.getElementById('id_password2');
        const passwordMatchText = document.getElementById('password-match-text');
        
        if (password1Input && password2Input && passwordMatchText) {
            function checkPasswordMatch() {
                if (password2Input.value) {
                    if (password1Input.value === password2Input.value) {
                        passwordMatchText.textContent = 'Passwords match';
                        passwordMatchText.className = 'text-success';
                        password2Input.classList.remove('is-invalid');
                        password2Input.classList.add('is-valid');
                    } else {
                        passwordMatchText.textContent = 'Passwords do not match';
                        passwordMatchText.className = 'text-danger';
                        password2Input.classList.remove('is-valid');
                        password2Input.classList.add('is-invalid');
                    }
                } else {
                    passwordMatchText.textContent = '';
                    password2Input.classList.remove('is-valid', 'is-invalid');
                }
            }
            
            password1Input.addEventListener('input', checkPasswordMatch);
            password2Input.addEventListener('input', checkPasswordMatch);
        }
        
        // Form submission
        registerForm.addEventListener('submit', function(e) {
            // Clear previous error messages
            const errorAlert = document.getElementById('register-error');
            if (errorAlert) {
                errorAlert.classList.add('d-none');
                errorAlert.textContent = '';
            }
            
            // Get form inputs
            const emailInput = document.getElementById('id_email');
            const password1Input = document.getElementById('id_password1');
            const password2Input = document.getElementById('id_password2');
            
            // Basic validation
            let hasError = false;
            let errorMessage = '';
            
            if (!emailInput.value.trim()) {
                emailInput.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Please fill in all required fields.';
            } else if (!window.marketplaceUtils.isValidEmail(emailInput.value.trim())) {
                emailInput.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Please enter a valid email address.';
            } else {
                emailInput.classList.remove('is-invalid');
            }
            
            if (!password1Input.value.trim()) {
                password1Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Please fill in all required fields.';
            } else if (password1Input.value.length < 8) {
                password1Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Password must be at least 8 characters long.';
            } else {
                password1Input.classList.remove('is-invalid');
            }
            
            if (!password2Input.value.trim()) {
                password2Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Please fill in all required fields.';
            } else if (password1Input.value !== password2Input.value) {
                password2Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Passwords do not match.';
            } else {
                password2Input.classList.remove('is-invalid');
            }
            
            if (hasError) {
                e.preventDefault();
                if (errorAlert) {
                    errorAlert.textContent = errorMessage;
                    errorAlert.classList.remove('d-none');
                }
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating account...';
            }
        });
        
        // Clear validation errors when input changes
        const inputs = registerForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                if (this.id !== 'id_password2') { // Password2 is handled separately
                    this.classList.remove('is-invalid');
                }
                
                // Hide error alert if all fields are valid
                const invalidInputs = registerForm.querySelectorAll('.is-invalid');
                if (invalidInputs.length === 0) {
                    const errorAlert = document.getElementById('register-error');
                    if (errorAlert) {
                        errorAlert.classList.add('d-none');
                    }
                }
            });
        });
    }
    
    // Password Reset Form
    const resetForm = document.getElementById('password-reset-form');
    
    if (resetForm) {
        resetForm.addEventListener('submit', function(e) {
            // Clear previous error messages
            const errorAlert = document.getElementById('reset-error');
            if (errorAlert) {
                errorAlert.classList.add('d-none');
                errorAlert.textContent = '';
            }
            
            // Get form inputs
            const emailInput = document.getElementById('id_email');
            
            // Basic validation
            let hasError = false;
            
            if (!emailInput.value.trim()) {
                emailInput.classList.add('is-invalid');
                hasError = true;
            } else if (!window.marketplaceUtils.isValidEmail(emailInput.value.trim())) {
                emailInput.classList.add('is-invalid');
                hasError = true;
            } else {
                emailInput.classList.remove('is-invalid');
            }
            
            if (hasError) {
                e.preventDefault();
                if (errorAlert) {
                    errorAlert.textContent = 'Please enter a valid email address.';
                    errorAlert.classList.remove('d-none');
                }
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending reset link...';
            }
        });
        
        // Clear validation errors when input changes
        const inputs = resetForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
                
                // Hide error alert
                const errorAlert = document.getElementById('reset-error');
                if (errorAlert) {
                    errorAlert.classList.add('d-none');
                }
            });
        });
    }
    
    // Password Reset Confirm Form
    const resetConfirmForm = document.getElementById('password-reset-confirm-form');
    
    if (resetConfirmForm) {
        // Password strength meter
        const passwordInput = document.getElementById('id_password1');
        const strengthMeter = document.getElementById('password-strength-meter');
        const strengthText = document.getElementById('password-strength-text');
        
        if (passwordInput && strengthMeter && strengthText) {
            passwordInput.addEventListener('input', function() {
                const password = this.value;
                let strength = 0;
                
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
        
        // Password confirmation match check
        const password1Input = document.getElementById('id_password1');
        const password2Input = document.getElementById('id_password2');
        const passwordMatchText = document.getElementById('password-match-text');
        
        if (password1Input && password2Input && passwordMatchText) {
            function checkPasswordMatch() {
                if (password2Input.value) {
                    if (password1Input.value === password2Input.value) {
                        passwordMatchText.textContent = 'Passwords match';
                        passwordMatchText.className = 'text-success';
                        password2Input.classList.remove('is-invalid');
                        password2Input.classList.add('is-valid');
                    } else {
                        passwordMatchText.textContent = 'Passwords do not match';
                        passwordMatchText.className = 'text-danger';
                        password2Input.classList.remove('is-valid');
                        password2Input.classList.add('is-invalid');
                    }
                } else {
                    passwordMatchText.textContent = '';
                    password2Input.classList.remove('is-valid', 'is-invalid');
                }
            }
            
            password1Input.addEventListener('input', checkPasswordMatch);
            password2Input.addEventListener('input', checkPasswordMatch);
        }
        
        // Form submission
        resetConfirmForm.addEventListener('submit', function(e) {
            // Clear previous error messages
            const errorAlert = document.getElementById('reset-confirm-error');
            if (errorAlert) {
                errorAlert.classList.add('d-none');
                errorAlert.textContent = '';
            }
            
            // Get form inputs
            const password1Input = document.getElementById('id_password1');
            const password2Input = document.getElementById('id_password2');
            
            // Basic validation
            let hasError = false;
            let errorMessage = '';
            
            if (!password1Input.value.trim()) {
                password1Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Please fill in all required fields.';
            } else if (password1Input.value.length < 8) {
                password1Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Password must be at least 8 characters long.';
            } else {
                password1Input.classList.remove('is-invalid');
            }
            
            if (!password2Input.value.trim()) {
                password2Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Please fill in all required fields.';
            } else if (password1Input.value !== password2Input.value) {
                password2Input.classList.add('is-invalid');
                hasError = true;
                errorMessage = 'Passwords do not match.';
            } else {
                password2Input.classList.remove('is-invalid');
            }
            
            if (hasError) {
                e.preventDefault();
                if (errorAlert) {
                    errorAlert.textContent = errorMessage;
                    errorAlert.classList.remove('d-none');
                }
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Resetting password...';
            }
        });
        
        // Clear validation errors when input changes
        const inputs = resetConfirmForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                if (this.id !== 'id_password2') { // Password2 is handled separately
                    this.classList.remove('is-invalid');
                }
                
                // Hide error alert if all fields are valid
                const invalidInputs = resetConfirmForm.querySelectorAll('.is-invalid');
                if (invalidInputs.length === 0) {
                    const errorAlert = document.getElementById('reset-confirm-error');
                    if (errorAlert) {
                        errorAlert.classList.add('d-none');
                    }
                }
            });
        });
    }
    
    // Social Login Buttons
    const socialLoginButtons = document.querySelectorAll('.social-login-btn');
    
    socialLoginButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Show loading state
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Connecting...';
            
            // Redirect to social login URL
            window.location.href = this.getAttribute('data-url');
        });
    });
});