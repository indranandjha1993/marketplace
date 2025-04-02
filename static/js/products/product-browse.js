/**
 * Product Browse Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('filter-form');
    const filterToggle = document.getElementById('filter-toggle');
    const filterContainer = document.getElementById('filter-container');
    const clearFiltersBtn = document.getElementById('clear-filters');
    const sortSelect = document.getElementById('sort-select');
    const sortInput = document.getElementById('sort-input');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Mobile filter toggle
    if (filterToggle && filterContainer) {
        // Initialize container state
        if (window.innerWidth < 992) {
            filterContainer.classList.add('collapsed');
        }

        filterToggle.addEventListener('click', function() {
            filterContainer.classList.toggle('collapsed');

            // Update button text
            const buttonText = filterContainer.classList.contains('collapsed') ? 'Show Filters' : 'Hide Filters';
            filterToggle.querySelector('span').textContent = buttonText;

            // Update icon
            const icon = filterToggle.querySelector('i');
            if (filterContainer.classList.contains('collapsed')) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-filter');
            } else {
                icon.classList.remove('fa-filter');
                icon.classList.add('fa-times');
            }
        });
    }

    // Show spinner when form is submitted
    if (form) {
        form.addEventListener('submit', function() {
            loadingSpinner.classList.add('active');
        });
    }

    // Clear filters button
    if (clearFiltersBtn && form) {
        clearFiltersBtn.addEventListener('click', function(e) {
            e.preventDefault();
            loadingSpinner.classList.add('active');
            window.location.href = window.location.pathname;
        });
    }

    // Add active class to filter-pills for hover effect
    const filterPills = document.querySelectorAll('.filter-pill');
    filterPills.forEach(pill => {
        pill.addEventListener('mouseenter', function() {
            this.classList.add('active');
        });
        pill.addEventListener('mouseleave', function() {
            this.classList.remove('active');
        });
    });
});

/**
 * Function to update sort and submit the form
 * @param {string} sortValue - The sort value to set
 */
function updateSortAndSubmit(sortValue) {
    const sortInput = document.getElementById('sort-input');
    if (sortInput) {
        sortInput.value = sortValue;
        document.getElementById('filter-form').submit();
    }
}