// CG Global Entertainment - Expense System JavaScript

(function() {
    'use strict';

    // Initialize application when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeApp();
    });

    function initializeApp() {
        initializeFormValidation();
        initializeFileUpload();
        initializeDataTables();
        initializeCharts();
        initializeNotifications();
        initializeTooltips();
        initializeModals();
        initializeDatePickers();
        initializeCurrencyHandling();
    }

    // Form Validation
    function initializeFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });

        // Real-time validation
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(input);
            });
        });
    }

    function validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        
        let isValid = true;
        let message = '';

        // Required field validation
        if (required && !value) {
            isValid = false;
            message = 'This field is required';
        }

        // Email validation
        if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Please enter a valid email address';
            }
        }

        // Amount validation
        if (field.classList.contains('amount-field') && value) {
            const amount = parseFloat(value);
            if (isNaN(amount) || amount <= 0) {
                isValid = false;
                message = 'Please enter a valid amount';
            }
        }

        // Display validation result
        showFieldValidation(field, isValid, message);
        return isValid;
    }

    function showFieldValidation(field, isValid, message) {
        const feedbackElement = field.parentNode.querySelector('.invalid-feedback');
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            if (feedbackElement) {
                feedbackElement.textContent = message;
            }
        }
    }

    // File Upload with Drag & Drop
    function initializeFileUpload() {
        const uploadAreas = document.querySelectorAll('.file-upload-area');
        
        uploadAreas.forEach(function(area) {
            const fileInput = area.querySelector('input[type="file"]');
            
            area.addEventListener('click', function() {
                fileInput.click();
            });

            area.addEventListener('dragover', function(e) {
                e.preventDefault();
                area.classList.add('dragover');
            });

            area.addEventListener('dragleave', function(e) {
                e.preventDefault();
                area.classList.remove('dragover');
            });

            area.addEventListener('drop', function(e) {
                e.preventDefault();
                area.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    handleFileSelection(files, area);
                }
            });

            fileInput.addEventListener('change', function(e) {
                handleFileSelection(e.target.files, area);
            });
        });
    }

    function handleFileSelection(files, uploadArea) {
        const maxSize = 5 * 1024 * 1024; // 5MB
        const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        
        Array.from(files).forEach(function(file) {
            // Validate file size
            if (file.size > maxSize) {
                showNotification('File size must be less than 5MB', 'danger');
                return;
            }

            // Validate file type
            if (!allowedTypes.includes(file.type)) {
                showNotification('Only JPEG, PNG and PDF files are allowed', 'danger');
                return;
            }

            // Show file preview
            showFilePreview(file, uploadArea);
        });
    }

    function showFilePreview(file, container) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.createElement('div');
            preview.className = 'file-preview d-flex align-items-center p-2 border rounded mb-2';
            
            if (file.type.startsWith('image/')) {
                preview.innerHTML = `
                    <img src="${e.target.result}" class="preview-image me-2" style="width: 50px; height: 50px; object-fit: cover;">
                    <span>${file.name}</span>
                    <button type="button" class="btn btn-sm btn-danger ms-auto remove-file">
                        <i class="fas fa-times"></i>
                    </button>
                `;
            } else {
                preview.innerHTML = `
                    <i class="fas fa-file-pdf fa-2x me-2 text-danger"></i>
                    <span>${file.name}</span>
                    <button type="button" class="btn btn-sm btn-danger ms-auto remove-file">
                        <i class="fas fa-times"></i>
                    </button>
                `;
            }

            const previewContainer = container.querySelector('.file-previews') || 
                                   container.appendChild(document.createElement('div'));
            previewContainer.className = 'file-previews mt-3';
            previewContainer.appendChild(preview);

            // Remove file functionality
            preview.querySelector('.remove-file').addEventListener('click', function() {
                preview.remove();
            });
        };
        reader.readAsDataURL(file);
    }

    // DataTables Enhancement
    function initializeDataTables() {
        const tables = document.querySelectorAll('.data-table');
        
        if (window.$ && $.fn.DataTable) {
            tables.forEach(function(table) {
                $(table).DataTable({
                    responsive: true,
                    pageLength: 25,
                    language: {
                        search: "Search claims:",
                        lengthMenu: "Show _MENU_ claims",
                        info: "Showing _START_ to _END_ of _TOTAL_ claims",
                        emptyTable: "No claims found"
                    },
                    columnDefs: [
                        { targets: 'no-sort', orderable: false }
                    ]
                });
            });
        }
    }

    // Charts initialization
    function initializeCharts() {
        initializeExpenseChart();
        initializeCategoryChart();
        initializeMonthlyTrendChart();
    }

    function initializeExpenseChart() {
        const ctx = document.getElementById('expenseChart');
        if (!ctx || !window.Chart) return;

        fetch('/api/expense-data/')
            .then(response => response.json())
            .then(data => {
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.values,
                            backgroundColor: [
                                '#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error loading expense chart data:', error);
            });
    }

    function initializeCategoryChart() {
        const ctx = document.getElementById('categoryChart');
        if (!ctx || !window.Chart) return;

        fetch('/api/category-data/')
            .then(response => response.json())
            .then(data => {
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Amount',
                            data: data.values,
                            backgroundColor: 'rgba(54, 162, 235, 0.8)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error loading category chart data:', error);
            });
    }

    function initializeMonthlyTrendChart() {
        const ctx = document.getElementById('monthlyTrendChart');
        if (!ctx || !window.Chart) return;

        fetch('/api/monthly-trend-data/')
            .then(response => response.json())
            .then(data => {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Monthly Expenses',
                            data: data.values,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error loading monthly trend data:', error);
            });
    }

    // Notifications
    function initializeNotifications() {
        // Auto-hide alerts after 5 seconds
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.classList.add('fade');
                    setTimeout(() => alert.remove(), 500);
                }
            }, 5000);
        });
    }

    function showNotification(message, type = 'info', duration = 5000) {
        const alertContainer = document.getElementById('alert-container') || 
                              document.body.insertAdjacentHTML('afterbegin', 
                                  '<div id="alert-container" class="position-fixed" style="top: 20px; right: 20px; z-index: 9999;"></div>') &&
                              document.getElementById('alert-container');

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        alertContainer.appendChild(alert);

        // Auto remove after duration
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 500);
            }
        }, duration);
    }

    // Bootstrap tooltips
    function initializeTooltips() {
        if (window.bootstrap) {
            const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltips.forEach(function(tooltip) {
                new bootstrap.Tooltip(tooltip);
            });
        }
    }

    // Bootstrap modals
    function initializeModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(function(modal) {
            modal.addEventListener('hidden.bs.modal', function() {
                // Clear form data when modal closes
                const forms = modal.querySelectorAll('form');
                forms.forEach(form => form.reset());
            });
        });
    }

    // Date pickers
    function initializeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(function(input) {
            // Set max date to today for past dates
            if (input.classList.contains('past-date-only')) {
                input.max = new Date().toISOString().split('T')[0];
            }
            
            // Set min date to today for future dates
            if (input.classList.contains('future-date-only')) {
                input.min = new Date().toISOString().split('T')[0];
            }
        });
    }

    // Currency handling
    function initializeCurrencyHandling() {
        const currencySelects = document.querySelectorAll('.currency-select');
        const amountFields = document.querySelectorAll('.amount-field');

        currencySelects.forEach(function(select) {
            select.addEventListener('change', function() {
                updateExchangeRate(this);
            });
        });

        amountFields.forEach(function(field) {
            // FIXED: Don't format on input to avoid cursor jumping
            // field.addEventListener('input', function() {
            //     formatCurrency(this);
            // });
            
            // Only format when user finishes typing (on blur)
            field.addEventListener('blur', function() {
                formatCurrency(this);
            });
        });
    }

    function updateExchangeRate(currencySelect) {
        const selectedCurrency = currencySelect.value;
        const rateDisplay = currencySelect.closest('.form-group')?.querySelector('.exchange-rate');
        
        if (selectedCurrency && selectedCurrency !== 'HKD' && rateDisplay) {
            fetch(`/api/exchange-rate/${selectedCurrency}/`)
                .then(response => response.json())
                .then(data => {
                    rateDisplay.textContent = `1 ${selectedCurrency} = ${data.rate} HKD`;
                    rateDisplay.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error fetching exchange rate:', error);
                    rateDisplay.style.display = 'none';
                });
        } else if (rateDisplay) {
            rateDisplay.style.display = 'none';
        }
    }

    function formatCurrency(amountField) {
        // DISABLED: This function was causing cursor jumping
        // Never modify input values during user typing
        // let value = amountField.value.replace(/[^\d.-]/g, '');
        // const numValue = parseFloat(value);
        // 
        // if (!isNaN(numValue) && numValue >= 0) {
        //     // Format with 2 decimal places
        //     amountField.value = numValue.toFixed(2);
        // }
        
        console.log('formatCurrency called but disabled to prevent cursor jumping');
    }

    // Utility functions
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function formatMoney(amount, currency = 'HKD') {
        return new Intl.NumberFormat('en-HK', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    function formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-HK');
    }

    // Export utility functions for global use
    window.ExpenseSystem = {
        showNotification,
        formatMoney,
        formatDate,
        validateField,
        debounce
    };

    // Service Worker registration for PWA capabilities
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/sw.js')
                .then(function(registration) {
                    console.log('SW registered: ', registration);
                })
                .catch(function(registrationError) {
                    console.log('SW registration failed: ', registrationError);
                });
        });
    }

})();
