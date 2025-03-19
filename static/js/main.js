document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    function triggerChangeEvent(element) {
        const event = new Event('change', { bubbles: true });
        element.dispatchEvent(event);
    }
});


document.addEventListener('DOMContentLoaded', function() {
    // Function to handle search submission
    function setupSearchForm(formId, inputId) {
        const form = document.getElementById(formId);
        const input = document.getElementById(inputId);

        if (form && input) {
            // Enable enter key submission
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    form.submit();
                }
            });

            // Ensure the search button works
            const button = form.querySelector('.search-button');
            if (button) {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    form.submit();
                });
            }
        }
    }

    // Setup both desktop and mobile search forms
    setupSearchForm('desktopSearchForm', 'desktopSearchInput');
    setupSearchForm('mobileSearchForm', 'mobileSearchInput');
});
