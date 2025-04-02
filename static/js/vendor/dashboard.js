/**
 * Vendor Dashboard JavaScript
 */

/**
 * Initialize the sales chart on the vendor dashboard
 * @param {string} chartId - The ID of the canvas element
 * @param {Array} dates - Array of date labels
 * @param {Array} revenues - Array of revenue values
 * @param {Array} orderCounts - Array of order count values
 */
function initializeSalesChart(chartId, dates, revenues, orderCounts) {
    const ctx = document.getElementById(chartId).getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Revenue',
                    data: revenues,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    yAxisID: 'y',
                    tension: 0.1
                },
                {
                    label: 'Orders',
                    data: orderCounts,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    yAxisID: 'y1',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Revenue (₹)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    },
                    title: {
                        display: true,
                        text: 'Order Count'
                    }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Dashboard charts
    const salesChartCanvas = document.getElementById('sales-chart');
    const ordersChartCanvas = document.getElementById('orders-chart');
    
    if (salesChartCanvas && window.Chart) {
        // Get sales data from data attribute
        const salesData = JSON.parse(salesChartCanvas.getAttribute('data-sales') || '[]');
        const salesLabels = salesData.map(item => item.date);
        const salesValues = salesData.map(item => item.amount);
        
        // Create sales chart
        const salesChart = new Chart(salesChartCanvas, {
            type: 'line',
            data: {
                labels: salesLabels,
                datasets: [{
                    label: 'Sales',
                    data: salesValues,
                    backgroundColor: 'rgba(var(--primary-color-rgb), 0.1)',
                    borderColor: 'var(--primary-color)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: 'var(--primary-color)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `Sales: ₹${context.raw.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '₹' + value;
                            }
                        }
                    }
                }
            }
        });
    }
    
    if (ordersChartCanvas && window.Chart) {
        // Get orders data from data attribute
        const ordersData = JSON.parse(ordersChartCanvas.getAttribute('data-orders') || '[]');
        const ordersLabels = ordersData.map(item => item.date);
        const ordersValues = ordersData.map(item => item.count);
        
        // Create orders chart
        const ordersChart = new Chart(ordersChartCanvas, {
            type: 'bar',
            data: {
                labels: ordersLabels,
                datasets: [{
                    label: 'Orders',
                    data: ordersValues,
                    backgroundColor: 'rgba(var(--primary-color-rgb), 0.7)',
                    borderColor: 'var(--primary-color)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            stepSize: 1,
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    // Date range picker
    const dateRangePicker = document.getElementById('date-range-picker');
    
    if (dateRangePicker && window.daterangepicker) {
        new daterangepicker(dateRangePicker, {
            ranges: {
                'Today': [moment(), moment()],
                'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            startDate: moment().subtract(29, 'days'),
            endDate: moment(),
            alwaysShowCalendars: true,
            opens: 'left'
        }, function(start, end, label) {
            // Update hidden inputs
            document.getElementById('start-date').value = start.format('YYYY-MM-DD');
            document.getElementById('end-date').value = end.format('YYYY-MM-DD');
            
            // Submit form
            document.getElementById('date-range-form').submit();
        });
    }
    
    // Recent orders table
    const viewOrderBtns = document.querySelectorAll('.view-order-btn');
    const orderDetailModal = document.getElementById('order-detail-modal');
    
    if (viewOrderBtns.length > 0 && orderDetailModal) {
        viewOrderBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const orderId = this.getAttribute('data-order-id');
                
                if (orderId) {
                    // Show loading state
                    const modalBody = orderDetailModal.querySelector('.modal-body');
                    modalBody.innerHTML = `
                        <div class="text-center py-5">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-3">Loading order details...</p>
                        </div>
                    `;
                    
                    // Fetch order details
                    fetch(`/vendor/orders/${orderId}/detail/`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Update modal content
                                modalBody.innerHTML = data.html;
                            } else {
                                modalBody.innerHTML = `
                                    <div class="alert alert-danger">
                                        ${data.error || 'Failed to load order details'}
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
    }
    
    // Update order status
    const updateStatusForm = document.getElementById('update-status-form');
    
    if (updateStatusForm) {
        updateStatusForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(this);
            const orderId = formData.get('order_id');
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...';
            }
            
            // Send request
            fetch(`/vendor/orders/${orderId}/update-status/`, {
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
                    window.marketplaceUtils.showToast('Order status updated successfully', 'success');
                    
                    // Close modal
                    const modalInstance = bootstrap.Modal.getInstance(orderDetailModal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    
                    // Reload page after a short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // Show error message
                    window.marketplaceUtils.showToast(data.error || 'Failed to update order status', 'error');
                    
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
    }
    
    // Low stock alerts
    const dismissAlertBtns = document.querySelectorAll('.dismiss-alert-btn');
    
    if (dismissAlertBtns.length > 0) {
        dismissAlertBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const alertId = this.getAttribute('data-alert-id');
                const alertCard = this.closest('.alert-card');
                
                if (alertId && alertCard) {
                    // Show loading state
                    this.disabled = true;
                    const originalText = this.innerHTML;
                    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                    
                    // Send request to dismiss alert
                    fetch(`/vendor/alerts/${alertId}/dismiss/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': window.marketplaceUtils.getCsrfToken()
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Remove alert card with animation
                            alertCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                            alertCard.style.opacity = '0';
                            alertCard.style.transform = 'translateY(-10px)';
                            
                            setTimeout(() => {
                                alertCard.remove();
                                
                                // Update alert count
                                const alertCount = document.getElementById('alert-count');
                                if (alertCount) {
                                    const count = parseInt(alertCount.textContent) - 1;
                                    alertCount.textContent = count;
                                    
                                    if (count === 0) {
                                        // Show no alerts message
                                        const alertsContainer = document.getElementById('alerts-container');
                                        if (alertsContainer) {
                                            alertsContainer.innerHTML = `
                                                <div class="alert alert-success">
                                                    No active alerts at the moment.
                                                </div>
                                            `;
                                        }
                                    }
                                }
                            }, 300);
                        } else {
                            // Show error message
                            window.marketplaceUtils.showToast(data.error || 'Failed to dismiss alert', 'error');
                            
                            // Reset button
                            this.innerHTML = originalText;
                            this.disabled = false;
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        window.marketplaceUtils.showToast('An error occurred. Please try again.', 'error');
                        
                        // Reset button
                        this.innerHTML = originalText;
                        this.disabled = false;
                    });
                }
            });
        });
    }
});