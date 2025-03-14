document.addEventListener('DOMContentLoaded', function() {
  const filterForm = document.getElementById('filter-form');
  const filterToggle = document.getElementById('filter-toggle');
  const filterContainer = document.getElementById('filter-container');
  const clearFiltersBtn = document.getElementById('clear-filters');
  const sortSelect = document.getElementById('sort-select');
  const sortInput = document.getElementById('sort-input');
  // const activeFiltersContainer = document.querySelector('.active-filters');

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

  // Sort order handling
  if (sortSelect && sortInput) {
    // Copy the sort select from hidden area to visible area
    const sortControls = document.querySelector('.sort-controls');
    if (sortControls) {
      const sortControlsParent = document.querySelector('.sort-controls-container');
      if (sortControlsParent) {
        sortControls.classList.remove('d-none');
        sortControlsParent.appendChild(sortControls);
      }
    }

    // Update hidden input when sort select changes
    sortSelect.addEventListener('change', function() {
      sortInput.value = this.value;
      filterForm.submit();
    });
  }

  // Clear filters button
  if (clearFiltersBtn && filterForm) {
    clearFiltersBtn.addEventListener('click', function(e) {
      e.preventDefault();

      // Clear all inputs except search query
      const inputs = filterForm.querySelectorAll('input:not([name="q"]), select');
      inputs.forEach(input => {
        if (input.type === 'radio' || input.type === 'checkbox') {
          input.checked = false;
        } else {
          input.value = '';
        }
      });

      // Reset sort to default
      if (sortInput) {
        sortInput.value = 'newest';
      }

      // Submit form
      filterForm.submit();
    });
  }

  })