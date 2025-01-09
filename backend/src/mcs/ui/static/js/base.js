// Base utilities for MicroColdSpray UI

// Service status colors
const STATUS_COLORS = {
    running: {
        bg: 'bg-green-100',
        border: 'border-green-500',
        text: 'text-green-800'
    },
    starting: {
        bg: 'bg-yellow-100',
        border: 'border-yellow-500',
        text: 'text-yellow-800'
    },
    error: {
        bg: 'bg-red-100',
        border: 'border-red-500',
        text: 'text-red-800'
    },
    stopped: {
        bg: 'bg-red-100',
        border: 'border-red-500',
        text: 'text-red-800'
    }
};

// Format utilities
const formatUtils = {
    /**
     * Format uptime duration
     * @param {number} seconds - Duration in seconds
     * @returns {string} Formatted duration string
     */
    formatUptime(seconds) {
        if (!seconds || seconds < 0) return 'Not available';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    },

    /**
     * Format service name for display
     * @param {string} name - Service name
     * @returns {string} Formatted service name
     */
    formatServiceName(name) {
        return name.split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
};

// API utilities
const apiUtils = {
    /**
     * Fetch with timeout and error handling
     * @param {string} url - API endpoint URL
     * @param {Object} options - Fetch options
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise} Fetch promise
     */
    async fetchWithTimeout(url, options = {}, timeout = 5000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timed out');
            }
            throw error;
        }
    },

    /**
     * Handle API errors
     * @param {Error} error - Error object
     * @param {string} context - Error context
     * @returns {Object} Error details
     */
    handleError(error, context = '') {
        console.error(`API Error (${context}):`, error);
        return {
            status: 'error',
            message: error.message || 'An unexpected error occurred',
            context
        };
    }
};

// DOM utilities
const domUtils = {
    /**
     * Create loading spinner element
     * @returns {HTMLElement} Spinner element
     */
    createSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        return spinner;
    },

    /**
     * Create error message element
     * @param {string} message - Error message
     * @returns {HTMLElement} Error element
     */
    createErrorMessage(message) {
        const error = document.createElement('div');
        error.className = 'error-message p-4 bg-red-100 border-2 border-red-500 rounded text-red-800';
        error.textContent = message;
        return error;
    }
};

// Service monitoring utilities
const monitoringUtils = {
    // Service update interval in milliseconds
    UPDATE_INTERVAL: 5000,
    updateTimer: null,

    /**
     * Create service card element
     * @param {string} name - Service name
     * @param {Object} service - Service data
     * @returns {HTMLElement} Card element
     */
    createServiceCard(name, service) {
        const card = document.createElement('div');
        
        // Map status to display colors
        let statusColor;
        switch (service.status.toLowerCase()) {
            case 'ok':
            case 'running':
                statusColor = 'success';
                break;
            case 'starting':
                statusColor = 'warning';
                break;
            case 'error':
            case 'stopped':
                statusColor = 'error';
                break;
            default:
                statusColor = 'error';
        }
        
        card.className = `service-card p-6 rounded-lg border-2 border-${statusColor} bg-${statusColor}/10`;
        card.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold">${formatUtils.formatServiceName(name)}</h3>
                <span class="px-2 py-1 rounded text-sm text-white bg-${statusColor}">
                    ${service.is_running ? 'RUNNING' : service.status.toUpperCase()}
                </span>
            </div>
            <div class="space-y-2">
                <p class="text-sm">
                    <span class="font-medium">Version:</span> ${service.version || 'Not available'}
                </p>
                ${service.port ? `
                    <p class="text-sm">
                        <span class="font-medium">Port:</span> ${service.port}
                    </p>
                ` : ''}
                <p class="text-sm">
                    <span class="font-medium">Uptime:</span> ${formatUtils.formatUptime(service.uptime)}
                </p>
                ${service.mode ? `
                    <p class="text-sm">
                        <span class="font-medium">Mode:</span> ${service.mode}
                    </p>
                ` : ''}
                ${service.error ? `
                    <div class="error-message mt-2 text-sm text-red-600">
                        <span class="font-medium">Error:</span> ${service.error}
                    </div>
                ` : ''}
                ${service.components ? `
                    <div class="mt-4 border-t pt-2">
                        <p class="text-sm font-medium mb-2">Components:</p>
                        ${Object.entries(service.components).map(([name, health]) => {
                            let componentColor;
                            switch (health.status.toLowerCase()) {
                                case 'ok':
                                    componentColor = 'success';
                                    break;
                                case 'warning':
                                    componentColor = 'warning';
                                    break;
                                case 'error':
                                    componentColor = 'error';
                                    break;
                                default:
                                    componentColor = 'error';
                            }
                            return `
                                <div class="component-status flex items-center justify-between mt-2 text-sm">
                                    <span class="font-medium">${formatUtils.formatServiceName(name)}:</span>
                                    <span class="px-2 py-0.5 rounded text-xs text-white bg-${componentColor}">
                                        ${health.status.toUpperCase()}
                                    </span>
                                </div>
                                ${health.error ? `<p class="text-xs text-red-600 mt-1">${health.error}</p>` : ''}
                            `;
                        }).join('')}
                    </div>
                ` : ''}
            </div>
        `;
        return card;
    },

    /**
     * Update services display
     * @param {boolean} showLoading - Whether to show loading state
     */
    async updateServices(showLoading = false) {
        const grid = document.getElementById('services-grid');
        if (!grid) return;
        
        try {
            if (showLoading) {
                grid.innerHTML = '';
                grid.appendChild(domUtils.createSpinner());
            }
            
            const services = await apiUtils.fetchWithTimeout('/monitoring/services/status');
            
            const newGrid = document.createElement('div');
            Object.entries(services).forEach(([name, service]) => {
                newGrid.appendChild(this.createServiceCard(name, service));
            });
            
            if (grid.innerHTML !== newGrid.innerHTML) {
                grid.innerHTML = newGrid.innerHTML;
            }
        } catch (error) {
            const errorDetails = apiUtils.handleError(error, 'services-update');
            grid.innerHTML = '';
            grid.appendChild(domUtils.createErrorMessage(
                'Failed to fetch services status. Please try refreshing the page.'
            ));
        }
    },

    /**
     * Initialize service monitoring
     */
    initialize() {
        // Setup refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (this.updateTimer) {
                    clearInterval(this.updateTimer);
                }
                this.updateServices(true);
                this.updateTimer = setInterval(() => this.updateServices(false), this.UPDATE_INTERVAL);
            });
        }

        // Initial update with loading indicator
        this.updateServices(true);

        // Start update timer
        this.updateTimer = setInterval(() => this.updateServices(false), this.UPDATE_INTERVAL);

        // Cleanup on page unload
        window.addEventListener('unload', () => {
            if (this.updateTimer) {
                clearInterval(this.updateTimer);
            }
        });
    }
};

// Export utilities
window.mcsprayUI = {
    STATUS_COLORS,
    formatUtils,
    apiUtils,
    domUtils,
    monitoringUtils
};

// Initialize monitoring when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mcsprayUI.monitoringUtils.initialize();
}); 