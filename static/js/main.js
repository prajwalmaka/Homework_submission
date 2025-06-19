/**
 * LearnTrack - Main JavaScript functionality
 * Handles form enhancements, file uploads, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeFormValidation();
    initializeFileUpload();
    initializeTooltips();
    initializeConfirmDialogs();
    initializeLoadingStates();
    initializeDateTimeInputs();
    initializeTableEnhancements();
});

/**
 * Form validation enhancements
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });

        // Real-time validation for specific fields
        const emailInputs = form.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', validateEmail);
        });

        const passwordInputs = form.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            input.addEventListener('input', validatePassword);
        });
    });
}

/**
 * Email validation
 */
function validateEmail(e) {
    const input = e.target;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (input.value && !emailRegex.test(input.value)) {
        input.setCustomValidity('Please enter a valid email address');
    } else {
        input.setCustomValidity('');
    }
}

/**
 * Password validation
 */
function validatePassword(e) {
    const input = e.target;
    const minLength = 6;
    
    if (input.value.length < minLength && input.value.length > 0) {
        input.setCustomValidity(`Password must be at least ${minLength} characters long`);
    } else {
        input.setCustomValidity('');
    }

    // Check for confirm password field
    const confirmPassword = document.querySelector('input[name="password2"]');
    if (confirmPassword && input.name === 'password') {
        validatePasswordConfirmation(confirmPassword);
    }
}

/**
 * Password confirmation validation
 */
function validatePasswordConfirmation(confirmInput) {
    const passwordInput = document.querySelector('input[name="password"]');
    
    if (confirmInput.value !== passwordInput.value) {
        confirmInput.setCustomValidity('Passwords do not match');
    } else {
        confirmInput.setCustomValidity('');
    }
}

/**
 * File upload enhancements with drag and drop
 */
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const wrapper = createFileUploadWrapper(input);
        setupDragAndDrop(wrapper, input);
        setupFilePreview(input);
    });
}

/**
 * Create drag and drop wrapper for file inputs
 */
function createFileUploadWrapper(input) {
    if (input.closest('.file-upload-wrapper')) {
        return input.closest('.file-upload-wrapper');
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'file-upload-wrapper';
    
    const dropArea = document.createElement('div');
    dropArea.className = 'file-upload-area border-2 border-dashed rounded p-4 text-center';
    dropArea.innerHTML = `
        <i class="fas fa-cloud-upload-alt fa-2x text-muted mb-2"></i>
        <p class="mb-2">Drag and drop files here or click to browse</p>
        <small class="text-muted">Supported formats: PDF, DOC, DOCX, JPG, PNG (Max: 16MB)</small>
    `;
    
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(dropArea);
    wrapper.appendChild(input);
    
    // Hide the original input
    input.style.display = 'none';
    
    // Make drop area clickable
    dropArea.addEventListener('click', () => input.click());
    
    return wrapper;
}

/**
 * Setup drag and drop functionality
 */
function setupDragAndDrop(wrapper, input) {
    const dropArea = wrapper.querySelector('.file-upload-area');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('dragover'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('dragover'), false);
    });
    
    dropArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            updateFileDisplay(dropArea, files[0]);
            triggerChangeEvent(input);
        }
    });
}

/**
 * Prevent default drag behaviors
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Setup file preview functionality
 */
function setupFilePreview(input) {
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        const wrapper = input.closest('.file-upload-wrapper');
        const dropArea = wrapper.querySelector('.file-upload-area');
        
        if (file) {
            updateFileDisplay(dropArea, file);
        }
    });
}

/**
 * Update file display in drop area
 */
function updateFileDisplay(dropArea, file) {
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    const maxSize = 16;
    
    let iconClass = 'fas fa-file';
    if (file.type.includes('image')) {
        iconClass = 'fas fa-file-image';
    } else if (file.type.includes('pdf')) {
        iconClass = 'fas fa-file-pdf';
    } else if (file.type.includes('word') || file.name.endsWith('.doc') || file.name.endsWith('.docx')) {
        iconClass = 'fas fa-file-word';
    }
    
    const statusClass = fileSize > maxSize ? 'text-danger' : 'text-success';
    const statusText = fileSize > maxSize ? `File too large (${fileSize}MB > ${maxSize}MB)` : `Ready to upload (${fileSize}MB)`;
    
    dropArea.innerHTML = `
        <i class="${iconClass} fa-2x ${statusClass} mb-2"></i>
        <p class="mb-1 fw-bold">${file.name}</p>
        <p class="mb-2 ${statusClass}">${statusText}</p>
        <small class="text-muted">Click to choose a different file</small>
    `;
}

/**
 * Trigger change event programmatically
 */
function triggerChangeEvent(input) {
    const event = new Event('change', { bubbles: true });
    input.dispatchEvent(event);
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize confirmation dialogs for dangerous actions
 */
function initializeConfirmDialogs() {
    const dangerousActions = document.querySelectorAll('[data-confirm]');
    
    dangerousActions.forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Initialize loading states for forms and buttons
 */
function initializeLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (form.checkValidity()) {
                const submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn) {
                    showLoadingState(submitBtn);
                }
                
                // Disable form to prevent double submission
                setTimeout(() => {
                    const inputs = form.querySelectorAll('input, select, textarea, button');
                    inputs.forEach(input => input.disabled = true);
                }, 100);
            }
        });
    });
}

/**
 * Show loading state on button
 */
function showLoadingState(button) {
    const originalText = button.textContent;
    const loadingText = button.getAttribute('data-loading-text') || 'Processing...';
    
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        ${loadingText}
    `;
    
    button.disabled = true;
    
    // Store original text for potential restoration
    button.setAttribute('data-original-text', originalText);
}

/**
 * Initialize date/time input enhancements
 */
function initializeDateTimeInputs() {
    const dateTimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    
    dateTimeInputs.forEach(input => {
        // Set minimum date to current date and time if not already set
        if (!input.min) {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            input.min = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
        
        // Add validation
        input.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const now = new Date();
            
            if (selectedDate < now) {
                this.setCustomValidity('Due date cannot be in the past');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

/**
 * Initialize table enhancements
 */
function initializeTableEnhancements() {
    // Add sorting functionality to tables
    const sortableTables = document.querySelectorAll('.table[data-sortable]');
    
    sortableTables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sort]');
        
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';
            
            header.addEventListener('click', function() {
                sortTable(table, this.getAttribute('data-sort'), this);
            });
        });
    });
    
    // Add search functionality
    const searchableElements = document.querySelectorAll('[data-search-target]');
    
    searchableElements.forEach(searchInput => {
        const targetSelector = searchInput.getAttribute('data-search-target');
        const targetElements = document.querySelectorAll(targetSelector);
        
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            targetElements.forEach(element => {
                const text = element.textContent.toLowerCase();
                const shouldShow = text.includes(searchTerm);
                
                element.style.display = shouldShow ? '' : 'none';
                
                // Handle table rows
                if (element.tagName === 'TR') {
                    element.style.display = shouldShow ? 'table-row' : 'none';
                }
            });
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, column, headerElement) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(headerElement.parentNode.children).indexOf(headerElement);
    
    // Determine sort direction
    const currentSort = headerElement.getAttribute('data-sort-direction') || 'asc';
    const newSort = currentSort === 'asc' ? 'desc' : 'asc';
    
    // Update header icons
    table.querySelectorAll('th i').forEach(i => {
        i.className = 'fas fa-sort text-muted';
    });
    
    const icon = headerElement.querySelector('i');
    icon.className = `fas fa-sort-${newSort === 'asc' ? 'up' : 'down'} text-primary`;
    
    headerElement.setAttribute('data-sort-direction', newSort);
    
    // Sort rows
    rows.sort((a, b) => {
        const aText = a.children[columnIndex].textContent.trim();
        const bText = b.children[columnIndex].textContent.trim();
        
        // Try to parse as numbers first
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        let comparison = 0;
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            comparison = aNum - bNum;
        } else {
            comparison = aText.localeCompare(bText);
        }
        
        return newSort === 'asc' ? comparison : -comparison;
    });
    
    // Reorder DOM elements
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Utility function to show toast notifications
 */
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove element after hiding
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

/**
 * Get or create toast container
 */
function getOrCreateToastContainer() {
    let container = document.querySelector('.toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    return container;
}

/**
 * Utility function to format file sizes
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Utility function to format dates
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

/**
 * Auto-resize textareas
 */
function initializeAutoResizeTextareas() {
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Initial resize
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    });
}

/**
 * Initialize character counters for text inputs
 */
function initializeCharacterCounters() {
    const inputs = document.querySelectorAll('[data-max-length]');
    
    inputs.forEach(input => {
        const maxLength = parseInt(input.getAttribute('data-max-length'));
        
        // Create counter element
        const counter = document.createElement('div');
        counter.className = 'form-text text-end';
        counter.innerHTML = `<span class="current">0</span>/<span class="max">${maxLength}</span>`;
        
        input.parentNode.appendChild(counter);
        
        // Update counter on input
        input.addEventListener('input', function() {
            const currentLength = this.value.length;
            const currentSpan = counter.querySelector('.current');
            
            currentSpan.textContent = currentLength;
            
            if (currentLength > maxLength * 0.9) {
                counter.className = 'form-text text-end text-warning';
            } else if (currentLength >= maxLength) {
                counter.className = 'form-text text-end text-danger';
            } else {
                counter.className = 'form-text text-end';
            }
        });
    });
}

// Export functions for external use
window.LearnTrack = {
    showToast,
    formatFileSize,
    formatDate,
    showLoadingState
};
