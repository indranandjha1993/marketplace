document.addEventListener('DOMContentLoaded', function() {
  // Elements
  const filterForm = document.getElementById('filter-form');
  const filterToggle = document.getElementById('filter-toggle');
  const filterContainer = document.getElementById('filter-container');
  const clearFiltersBtn = document.getElementById('clear-filters');
  const loadingSpinner = document.getElementById('loading-spinner');
  const sortSelect = document.getElementById('sort-select');
  const sortInput = document.getElementById('sort-input');
  const priceInputs = document.querySelectorAll('input[name="min_price"], input[name="max_price"]');
  const searchInput = document.querySelector('input[name="q"]');

  // Show currently active filters count on filter button for mobile
  function updateFilterCount() {
    if (!filterToggle) return;

    const activeFilters = document.querySelectorAll('.filter-pill').length;
    const filterBadge = filterToggle.querySelector('.filter-count');

    if (activeFilters > 0) {
      if (filterBadge) {
        filterBadge.textContent = activeFilters;
      } else {
        const badge = document.createElement('span');
        badge.className = 'badge bg-primary rounded-pill filter-count';
        badge.textContent = activeFilters;
        badge.style.marginLeft = '5px';
        filterToggle.appendChild(badge);
      }
    } else if (filterBadge) {
      filterBadge.remove();
    }
  }

  // Mobile filter toggle
  if (filterToggle && filterContainer) {
    // Initialize container state
    if (window.innerWidth < 992) {
      filterContainer.classList.add('collapsed');
    }

    filterToggle.addEventListener('click', function() {
      filterContainer.classList.toggle('collapsed');

      // Update button text and icon
      const buttonText = filterContainer.classList.contains('collapsed') ? 'Show Filters' : 'Hide Filters';
      filterToggle.querySelector('span').textContent = buttonText;

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

  // Debounce function to limit how often a function can fire
  function debounce(func, wait) {
    let timeout;
    return function() {
      const context = this;
      const args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), wait);
    };
  }

  // Price input validation and auto-submission
  if (priceInputs.length) {
    priceInputs.forEach(input => {
      // Validate numeric input
      input.addEventListener('input', function() {
        this.value = this.value.replace(/[^0-9]/g, '');
      });

      // Auto-submit after delay when user stops typing
      input.addEventListener('input', debounce(function() {
        if (this.value !== '') {
          filterForm.submit();
          loadingSpinner.classList.add('active');
        }
      }, 1000));
    });
  }

  // Search input auto-submit
  if (searchInput) {
    const originalValue = searchInput.value;

    searchInput.addEventListener('input', debounce(function() {
      // Only submit if value has changed and is not empty
      if (this.value !== originalValue && this.value.trim() !== '') {
        filterForm.submit();
        loadingSpinner.classList.add('active');
      }
    }, 500));

    // Clear search with X button
    const clearSearchBtn = document.createElement('button');
    clearSearchBtn.type = 'button';
    clearSearchBtn.className = 'clear-search-btn';
    clearSearchBtn.innerHTML = '&times;';
    clearSearchBtn.style.display = searchInput.value ? 'block' : 'none';
    clearSearchBtn.addEventListener('click', function() {
      searchInput.value = '';
      this.style.display = 'none';
      filterForm.submit();
      loadingSpinner.classList.add('active');
    });

    // Position the clear button
    searchInput.parentNode.style.position = 'relative';
    clearSearchBtn.style.position = 'absolute';
    clearSearchBtn.style.right = '50px';
    clearSearchBtn.style.top = '50%';
    clearSearchBtn.style.transform = 'translateY(-50%)';
    clearSearchBtn.style.border = 'none';
    clearSearchBtn.style.background = 'transparent';
    clearSearchBtn.style.fontSize = '18px';
    clearSearchBtn.style.color = '#aaa';
    clearSearchBtn.style.cursor = 'pointer';
    clearSearchBtn.style.zIndex = '5';

    searchInput.parentNode.appendChild(clearSearchBtn);

    // Show/hide clear button based on input
    searchInput.addEventListener('input', function() {
      clearSearchBtn.style.display = this.value ? 'block' : 'none';
    });
  }

  // Show loading spinner when form is submitted
  if (filterForm) {
    filterForm.addEventListener('submit', function() {
      loadingSpinner.classList.add('active');
    });

    // Radio button auto-submit
    const radioInputs = filterForm.querySelectorAll('input[type="radio"]');
    radioInputs.forEach(input => {
      input.addEventListener('change', function() {
        filterForm.submit();
        loadingSpinner.classList.add('active');
      });
    });
  }

  // Clear filters button
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', function(e) {
      e.preventDefault();
      loadingSpinner.classList.add('active');
      window.location.href = window.location.pathname;
    });
  }

  // Sort order handling
  if (sortSelect && sortInput) {
    sortSelect.addEventListener('change', function() {
      sortInput.value = this.value;
      filterForm.submit();
      loadingSpinner.classList.add('active');
    });
  }

  // Highlight active category/brand in sidebar
  function highlightActiveFilters() {
    const activeCategory = document.querySelector('input[name="category"]:checked');
    const activeBrand = document.querySelector('input[name="brand"]:checked');
    const activeRating = document.querySelector('input[name="rating"]:checked');

    if (activeCategory) {
      const categoryItem = activeCategory.closest('.form-check');
      categoryItem.scrollIntoView({ block: 'center', behavior: 'smooth' });
      setTimeout(() => {
        categoryItem.classList.add('highlight-item');
        setTimeout(() => categoryItem.classList.remove('highlight-item'), 1000);
      }, 500);
    }

    if (activeBrand) {
      const brandItem = activeBrand.closest('.form-check');
      brandItem.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }

    if (activeRating) {
      const ratingItem = activeRating.closest('.form-check');
      ratingItem.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  // Show spinner when pagination links are clicked
  const paginationLinks = document.querySelectorAll('.pagination .page-link');
  paginationLinks.forEach(link => {
    link.addEventListener('click', function() {
      loadingSpinner.classList.add('active');
    });
  });

  // Add animation for product cards
  const productCards = document.querySelectorAll('.product-card');
  productCards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';

    setTimeout(() => {
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 100 + (index * 50)); // Stagger the animations
  });

  // Add hover effect for filter pills
  const filterPills = document.querySelectorAll('.filter-pill');
  filterPills.forEach(pill => {
    pill.addEventListener('mouseover', function() {
      this.style.transform = 'translateY(-3px)';
    });

    pill.addEventListener('mouseout', function() {
      this.style.transform = 'translateY(0)';
    });
  });

  // Execute initial setup
  updateFilterCount();
  highlightActiveFilters();

  // Add scroll to top button
  const scrollTopBtn = document.createElement('button');
  scrollTopBtn.className = 'scroll-top-btn';
  scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
  scrollTopBtn.title = 'Scroll to top';
  document.body.appendChild(scrollTopBtn);

  scrollTopBtn.addEventListener('click', function() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });

  // Show/hide scroll to top button
  window.addEventListener('scroll', function() {
    if (window.pageYOffset > 300) {
      scrollTopBtn.classList.add('show');
    } else {
      scrollTopBtn.classList.remove('show');
    }
  });

  // Style for scroll to top button
  scrollTopBtn.style.position = 'fixed';
  scrollTopBtn.style.bottom = '20px';
  scrollTopBtn.style.right = '20px';
  scrollTopBtn.style.width = '40px';
  scrollTopBtn.style.height = '40px';
  scrollTopBtn.style.borderRadius = '50%';
  scrollTopBtn.style.backgroundColor = 'var(--primary-color)';
  scrollTopBtn.style.color = 'white';
  scrollTopBtn.style.border = 'none';
  scrollTopBtn.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
  scrollTopBtn.style.cursor = 'pointer';
  scrollTopBtn.style.display = 'flex';
  scrollTopBtn.style.alignItems = 'center';
  scrollTopBtn.style.justifyContent = 'center';
  scrollTopBtn.style.fontSize = '16px';
  scrollTopBtn.style.opacity = '0';
  scrollTopBtn.style.transform = 'scale(0.8)';
  scrollTopBtn.style.transition = 'all 0.3s ease';
  scrollTopBtn.style.zIndex = '1000';

  // Active style
  const style = document.createElement('style');
  style.textContent = `
    .scroll-top-btn.show {
      opacity: 1;
      transform: scale(1);
    }
    .scroll-top-btn:hover {
      background-color: var(--secondary-color);
      transform: scale(1.1);
    }
    .highlight-item {
      animation: highlight-pulse 1s ease;
    }
    @keyframes highlight-pulse {
      0% { background-color: transparent; }
      50% { background-color: rgba(var(--primary-color-rgb), 0.15); }
      100% { background-color: transparent; }
    }
  `;
  document.head.appendChild(style);
});

// Global function to update sort and submit form
function updateSortAndSubmit(sortValue) {
  const sortInput = document.getElementById('sort-input');
  const loadingSpinner = document.getElementById('loading-spinner');

  if (sortInput) {
    sortInput.value = sortValue;
    document.getElementById('filter-form').submit();
    loadingSpinner.classList.add('active');
  }
}
