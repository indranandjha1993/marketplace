//Django Toast Notifications - Just add this to your footer template -->
(function() {
    // Toast Configuration - Change these options as needed
    const toastConfig = {
        position: 'bottom-right',   // top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
        autoDismiss: true,          // automatically hide toast after timeout
        dismissDelay: 5000,         // time in ms before toast auto-hides
        animation: 'slide',         // slide, fade, bounce
        maxToasts: 4                // maximum number of toasts to show at once
    };
    
    // Create toast container if it doesn't exist
    function createToastContainer() {
        let container = document.getElementById('django-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'django-toast-container';
            document.body.appendChild(container);
            
            // Apply position based on config
            const posClasses = {
                'top-left': 'top-0 start-0',
                'top-center': 'top-0 start-50 translate-middle-x',
                'top-right': 'top-0 end-0',
                'bottom-left': 'bottom-0 start-0',
                'bottom-center': 'bottom-0 start-50 translate-middle-x',
                'bottom-right': 'bottom-0 end-0'
            };
            
            const position = posClasses[toastConfig.position] || posClasses['bottom-right'];
            container.className = `toast-container position-fixed p-3 ${position}`;
            container.style.zIndex = '9999';
        }
        return container;
    }
    
    // Get icon for message type
    function getIcon(type) {
        switch (type) {
            case 'success': return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M8 12l2 2 4-4"></path></svg>';
            case 'error': case 'danger': return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
            case 'warning': return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
            case 'info': return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
            default: return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>';
        }
    }
    
    // Get title for message type
    function getTitle(type) {
        switch (type) {
            case 'success': return 'Success';
            case 'error': case 'danger': return 'Error';
            case 'warning': return 'Warning';
            case 'info': return 'Information';
            default: return 'Notification';
        }
    }
    
    // Create and show a toast
    function createToast(message, type) {
        const container = createToastContainer();
        const toast = document.createElement('div');
        
        // Set toast styling
        toast.className = 'toast-notification';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Set toast content
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon ${type}-icon">${getIcon(type)}</div>
                <div class="toast-message">
                    <div class="toast-title">${getTitle(type)}</div>
                    <div class="toast-text">${message}</div>
                </div>
                <button class="toast-close" aria-label="Close">&times;</button>
            </div>
            <div class="toast-progress"><div class="toast-progress-bar"></div></div>
        `;
        
        // Limit number of toasts
        const existingToasts = container.querySelectorAll('.toast-notification');
        if (existingToasts.length >= toastConfig.maxToasts) {
            container.removeChild(existingToasts[0]);
        }
        
        // Add to container
        container.appendChild(toast);
        
        // Show animation based on config
        if (toastConfig.animation === 'fade') {
            toast.style.animation = 'toast-fade-in 0.3s forwards';
        } else if (toastConfig.animation === 'bounce') {
            toast.style.animation = 'toast-bounce-in 0.5s forwards';
        } else {
            toast.style.animation = 'toast-slide-in 0.3s forwards';
        }
        
        // Set progress bar animation
        const progressBar = toast.querySelector('.toast-progress-bar');
        if (progressBar && toastConfig.autoDismiss) {
            progressBar.style.animation = `toast-progress ${toastConfig.dismissDelay}ms linear forwards`;
        }
        
        // Handle close button
        const closeButton = toast.querySelector('.toast-close');
        closeButton.addEventListener('click', () => {
            dismissToast(toast);
        });
        
        // Auto dismiss
        if (toastConfig.autoDismiss) {
            toast.timeout = setTimeout(() => {
                dismissToast(toast);
            }, toastConfig.dismissDelay);
            
            // Pause on hover
            toast.addEventListener('mouseenter', () => {
                clearTimeout(toast.timeout);
                if (progressBar) {
                    progressBar.style.animationPlayState = 'paused';
                }
            });
            
            toast.addEventListener('mouseleave', () => {
                toast.timeout = setTimeout(() => {
                    dismissToast(toast);
                }, toastConfig.dismissDelay * (1 - (parseFloat(getComputedStyle(progressBar).width) / parseFloat(getComputedStyle(progressBar.parentNode).width))));
                
                if (progressBar) {
                    progressBar.style.animationPlayState = 'running';
                }
            });
        }
        
        return toast;
    }
    
    // Dismiss a toast
    function dismissToast(toast) {
        clearTimeout(toast.timeout);
        
        // Hide animation based on config
        if (toastConfig.animation === 'fade') {
            toast.style.animation = 'toast-fade-out 0.3s forwards';
        } else if (toastConfig.animation === 'bounce') {
            toast.style.animation = 'toast-slide-out 0.3s forwards';
        } else {
            toast.style.animation = 'toast-slide-out 0.3s forwards';
        }
        
        // Remove after animation
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
    
    // Add styles
    function addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            #django-toast-container {
                position: fixed;
                z-index: 9999;
                pointer-events: none;
                max-width: 320px;
            }
            
            .toast-notification {
                background: white;
                border-radius: 8px;
                margin: 0.5rem 0;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                overflow: hidden;
                transition: transform 0.3s ease;
                pointer-events: auto;
                position: relative;
                transform: translateX(100%);
            }
            
            .toast-content {
                display: flex;
                align-items: flex-start;
                padding: 12px 12px 10px;
            }
            
            .toast-icon {
                flex-shrink: 0;
                padding: 3px;
                border-radius: 50%;
                margin-right: 10px;
                height: 24px;
                width: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .toast-icon svg {
                width: 18px;
                height: 18px;
            }
            
            .success-icon {
                background-color: rgba(40, 167, 69, 0.15);
                color: #28a745;
            }
            
            .error-icon, .danger-icon {
                background-color: rgba(220, 53, 69, 0.15);
                color: #dc3545;
            }
            
            .warning-icon {
                background-color: rgba(255, 193, 7, 0.15);
                color: #ffc107;
            }
            
            .info-icon {
                background-color: rgba(23, 162, 184, 0.15);
                color: #17a2b8;
            }
            
            .toast-message {
                flex-grow: 1;
                padding-right: 10px;
            }
            
            .toast-title {
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 2px;
                color: #333;
            }
            
            .toast-text {
                font-size: 14px;
                color: #666;
                word-break: break-word;
            }
            
            .toast-close {
                background: transparent;
                border: none;
                color: #999;
                font-size: 18px;
                cursor: pointer;
                font-weight: bold;
                margin-left: auto;
                padding: 0 5px;
                flex-shrink: 0;
                align-self: flex-start;
                line-height: 1;
                transition: color 0.2s;
            }
            
            .toast-close:hover {
                color: #333;
            }
            
            .toast-progress {
                height: 3px;
                width: 100%;
                background-color: rgba(0, 0, 0, 0.05);
                position: relative;
                overflow: hidden;
            }
            
            .toast-progress-bar {
                height: 100%;
                width: 100%;
                transform-origin: left;
                background: linear-gradient(90deg, #28a745, #17a2b8);
                transform: scaleX(0);
            }
            
            /* Success Toast */
            .toast-notification.success .toast-progress-bar {
                background: linear-gradient(90deg, #28a745, #20c997);
            }
            
            /* Error Toast */
            .toast-notification.error .toast-progress-bar,
            .toast-notification.danger .toast-progress-bar {
                background: linear-gradient(90deg, #dc3545, #e83e8c);
            }
            
            /* Warning Toast */
            .toast-notification.warning .toast-progress-bar {
                background: linear-gradient(90deg, #ffc107, #fd7e14);
            }
            
            /* Info Toast */
            .toast-notification.info .toast-progress-bar {
                background: linear-gradient(90deg, #17a2b8, #007bff);
            }
            
            /* Animations */
            @keyframes toast-slide-in {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes toast-slide-out {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            
            @keyframes toast-fade-in {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes toast-fade-out {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            
            @keyframes toast-bounce-in {
                0% { transform: translateX(100%); opacity: 0; }
                60% { transform: translateX(-5%); opacity: 1; }
                80% { transform: translateX(2%); }
                100% { transform: translateX(0); }
            }
            
            @keyframes toast-progress {
                from { transform: scaleX(1); }
                to { transform: scaleX(0); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Process Django messages
    function processDjangoMessages() {
        // Find Django messages
        const djangoMessages = document.querySelectorAll('.messages .alert, [data-toast-message]');
        if (!djangoMessages.length) return;
        
        // Add styles to document
        addStyles();
        
        // Process each message
        djangoMessages.forEach((message, index) => {
            // Extract message text and type
            let text = '';
            let type = 'info';
            
            if (message.hasAttribute('data-toast-message')) {
                // Custom data-attribute messages
                text = message.getAttribute('data-toast-message');
                type = message.getAttribute('data-toast-type') || 'info';
            } else {
                // Standard Django messages
                text = message.textContent.trim();
                
                if (message.classList.contains('alert-success')) {
                    type = 'success';
                } else if (message.classList.contains('alert-danger') || message.classList.contains('alert-error')) {
                    type = 'error';
                } else if (message.classList.contains('alert-warning')) {
                    type = 'warning';
                } else if (message.classList.contains('alert-info')) {
                    type = 'info';
                }
            }
            
            // Hide original message
            message.style.display = 'none';
            
            // Create toast with delay for sequential appearance
            setTimeout(() => {
                createToast(text, type);
            }, index * 300);
        });
    }
    
    // JavaScript API
    window.djangoToast = {
        show: (message, type = 'info') => createToast(message, type),
        success: (message) => createToast(message, 'success'),
        error: (message) => createToast(message, 'error'),
        warning: (message) => createToast(message, 'warning'),
        info: (message) => createToast(message, 'info'),
        configure: (options) => {
            Object.assign(toastConfig, options);
            
            // Update container position if it exists
            const container = document.getElementById('django-toast-container');
            if (container && options.position) {
                const posClasses = {
                    'top-left': 'top-0 start-0',
                    'top-center': 'top-0 start-50 translate-middle-x',
                    'top-right': 'top-0 end-0',
                    'bottom-left': 'bottom-0 start-0',
                    'bottom-center': 'bottom-0 start-50 translate-middle-x',
                    'bottom-right': 'bottom-0 end-0'
                };
                
                container.className = `toast-container position-fixed p-3 ${posClasses[options.position] || posClasses['bottom-right']}`;
            }
        }
    };
    
    // Process messages when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', processDjangoMessages);
    } else {
        processDjangoMessages();
    }
})();

//Example of how to use the JavaScript API: -->

//    // Display a toast programmatically
//    djangoToast.success('Operation completed successfully!');
//
//    // Configure toast options
//    djangoToast.configure({
//        position: 'top-right',
//        dismissDelay: 8000,
//        animation: 'bounce'
//    });
//
//    // Show different types of toasts
//    djangoToast.error('An error occurred while processing your request.');
//    djangoToast.warning('Your session will expire in 5 minutes.');
//    djangoToast.info('New features are available.');
