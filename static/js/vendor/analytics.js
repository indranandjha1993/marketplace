/**
 * Vendor Analytics JavaScript
 * Handles charts and analytics functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers with restrictions
    const startPicker = flatpickr("#startDate", {
        dateFormat: "Y-m-d",
        maxDate: new Date(), // Prevent future dates
        onChange: function(selectedDates, dateStr, instance) {
            // Update end date's minDate to start date
            const endPicker = document.querySelector("#endDate")._flatpickr;
            if (selectedDates.length) {
                endPicker.set('minDate', selectedDates[0]);
                // If end date is now invalid, clear it
                const endDateValue = document.querySelector("#endDate").value;
                if (endDateValue && new Date(endDateValue) < selectedDates[0]) {
                    endPicker.clear();
                }
            }
        }
    });

    const endPicker = flatpickr("#endDate", {
        dateFormat: "Y-m-d",
        maxDate: new Date(), // Prevent future dates
        onChange: function(selectedDates, dateStr, instance) {
            // Update start date's maxDate to end date
            const startPicker = document.querySelector("#startDate")._flatpickr;
            if (selectedDates.length) {
                startPicker.set('maxDate', selectedDates[0]);
                // If start date is now invalid, clear it
                const startDateValue = document.querySelector("#startDate").value;
                if (startDateValue && new Date(startDateValue) > selectedDates[0]) {
                    startPicker.clear();
                }
            }
        }
    });

    // Show/hide date pickers based on range selection
    const rangeSelect = document.querySelector('#rangeSelect');
    const datePickers = document.querySelectorAll('.date-picker');
    const dateRangeForm = document.querySelector('#dateRangeForm');

    if (rangeSelect && datePickers.length && dateRangeForm) {
        rangeSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                datePickers.forEach(picker => picker.style.display = 'block');
            } else {
                datePickers.forEach(picker => picker.style.display = 'none');
                dateRangeForm.submit(); // Submit immediately for predefined ranges
            }
        });

        // Ensure form submission only when both dates are selected for custom range
        dateRangeForm.addEventListener('submit', function(event) {
            const range = rangeSelect.value;
            const startDate = document.querySelector('#startDate').value;
            const endDate = document.querySelector('#endDate').value;

            if (range === 'custom') {
                if (!startDate || !endDate) {
                    event.preventDefault();
                    alert('Please select both start and end dates for a custom range.');
                } else if (new Date(startDate) > new Date(endDate)) {
                    event.preventDefault();
                    alert('Start date must be less than or equal to end date.');
                }
            }
        });
    }
});

/**
 * Initialize charts for the analytics page
 * @param {Array} salesLabels - Array of date labels for sales chart
 * @param {Array} salesValues - Array of sales values
 * @param {Array} ordersValues - Array of order count values
 * @param {Array} categoryLabels - Array of category labels for category chart
 * @param {Array} categoryValues - Array of category revenue values
 */
function initializeCharts(salesLabels, salesValues, ordersValues, categoryLabels, categoryValues) {
    // Sales Chart
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: salesLabels.length ? salesLabels : ['No Data'],
            datasets: [
                {
                    label: 'Total Sales ($)',
                    data: salesValues.length ? salesValues : [0],
                    borderColor: '#007aff',
                    backgroundColor: 'rgba(0, 122, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Total Orders',
                    data: ordersValues.length ? ordersValues : [0],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            }
        }
    });

    // Category Chart
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    new Chart(categoryCtx, {
        type: 'pie',
        data: {
            labels: categoryLabels.length ? categoryLabels : ['No Data'],
            datasets: [{
                data: categoryValues.length ? categoryValues : [0],
                backgroundColor: [
                    '#007aff', '#28a745', '#dc3545', '#ffca28', '#6f42c1',
                    '#17a2b8', '#fd7e14', '#6610f2', '#e83e8c', '#20c997'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: $${value.toFixed(2)}`;
                        }
                    }
                }
            }
        }
    });
}