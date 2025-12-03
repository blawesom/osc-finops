/**
 * Consumption Builder UI module
 */
const ConsumptionBuilder = {
    currentData: null,
    filters: {
        from_date: '',
        to_date: '',
        granularity: 'day',
        region: '',
        service: '',
        resource_type: '',
        aggregate_by: ''
    },
    initialized: false,
    
    /**
     * Initialize consumption builder
     */
    async init() {
        // Prevent duplicate initialization
        if (this.initialized) {
            return;
        }
        
        // Set default date range (last 30 days)
        const today = new Date();
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(today.getDate() - 30);
        
        this.filters.from_date = this.formatDate(thirtyDaysAgo);
        this.filters.to_date = this.formatDate(today);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Update filter UI
        this.updateFilterUI();
        
        // Load initial data
        await this.loadConsumption();
        
        // Mark as initialized
        this.initialized = true;
    },
    
    /**
     * Format date to YYYY-MM-DD
     */
    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Apply filters button
        const applyBtn = document.getElementById('consumption-apply-filters');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyFilters());
        }
        
        // Clear filters button
        const clearBtn = document.getElementById('consumption-clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearFilters());
        }
        
        // Export buttons
        const exportCsvBtn = document.getElementById('consumption-export-csv');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportData('csv'));
        }
        
        const exportJsonBtn = document.getElementById('consumption-export-json');
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportData('json'));
        }
        
        // Filter inputs (debounced)
        let debounceTimer;
        const filterInputs = [
            'consumption-from-date',
            'consumption-to-date',
            'consumption-granularity',
            'consumption-region',
            'consumption-service',
            'consumption-resource-type',
            'consumption-aggregate-by'
        ];
        
        filterInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('change', () => {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => {
                        this.updateFiltersFromUI();
                    }, 300);
                });
            }
        });
    },
    
    /**
     * Update filters from UI inputs
     */
    updateFiltersFromUI() {
        const fromDateInput = document.getElementById('consumption-from-date');
        const toDateInput = document.getElementById('consumption-to-date');
        const granularitySelect = document.getElementById('consumption-granularity');
        const regionSelect = document.getElementById('consumption-region');
        const serviceSelect = document.getElementById('consumption-service');
        const resourceTypeSelect = document.getElementById('consumption-resource-type');
        const aggregateBySelect = document.getElementById('consumption-aggregate-by');
        
        if (fromDateInput) this.filters.from_date = fromDateInput.value;
        if (toDateInput) this.filters.to_date = toDateInput.value;
        if (granularitySelect) this.filters.granularity = granularitySelect.value;
        if (regionSelect) this.filters.region = regionSelect.value;
        if (serviceSelect) this.filters.service = serviceSelect.value;
        if (resourceTypeSelect) this.filters.resource_type = resourceTypeSelect.value;
        if (aggregateBySelect) this.filters.aggregate_by = aggregateBySelect.value;
    },
    
    /**
     * Update filter UI with current filter values
     */
    updateFilterUI() {
        const fromDateInput = document.getElementById('consumption-from-date');
        const toDateInput = document.getElementById('consumption-to-date');
        const granularitySelect = document.getElementById('consumption-granularity');
        const regionSelect = document.getElementById('consumption-region');
        const serviceSelect = document.getElementById('consumption-service');
        const resourceTypeSelect = document.getElementById('consumption-resource-type');
        const aggregateBySelect = document.getElementById('consumption-aggregate-by');
        
        if (fromDateInput) fromDateInput.value = this.filters.from_date;
        if (toDateInput) toDateInput.value = this.filters.to_date;
        if (granularitySelect) granularitySelect.value = this.filters.granularity;
        if (regionSelect) regionSelect.value = this.filters.region;
        if (serviceSelect) serviceSelect.value = this.filters.service;
        if (resourceTypeSelect) resourceTypeSelect.value = this.filters.resource_type;
        if (aggregateBySelect) aggregateBySelect.value = this.filters.aggregate_by;
    },
    
    /**
     * Apply filters and reload data
     */
    async applyFilters() {
        this.updateFiltersFromUI();
        await this.loadConsumption();
    },
    
    /**
     * Clear all filters
     */
    async clearFilters() {
        const today = new Date();
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(today.getDate() - 30);
        
        this.filters = {
            from_date: this.formatDate(thirtyDaysAgo),
            to_date: this.formatDate(today),
            granularity: 'day',
            region: '',
            service: '',
            resource_type: '',
            aggregate_by: ''
        };
        
        this.updateFilterUI();
        await this.loadConsumption();
    },
    
    /**
     * Load consumption data
     */
    async loadConsumption() {
        this.showLoading();
        this.hideError();
        
        try {
            // Validate date range
            if (!this.filters.from_date || !this.filters.to_date) {
                throw new Error('Please select a date range');
            }
            
            if (this.filters.from_date > this.filters.to_date) {
                throw new Error('Start date must be before end date');
            }
            
            // Build query parameters
            const params = {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date,
                granularity: this.filters.granularity
            };
            
            if (this.filters.region) params.region = this.filters.region;
            if (this.filters.service) params.service = this.filters.service;
            if (this.filters.resource_type) params.resource_type = this.filters.resource_type;
            if (this.filters.aggregate_by) params.aggregate_by = this.filters.aggregate_by;
            
            // Fetch data
            const response = await ConsumptionService.getConsumption(params);
            
            // Store full response including metadata and totals
            this.currentData = {
                ...response.data,
                metadata: response.metadata || {},
                totals: response.totals || {}
            };
            
            // Update UI
            this.updateConsumptionTable();
            this.updateSummaryCards();
            this.updateTopDrivers();
            this.updateFilterOptions();
            
            this.hideLoading();
        } catch (error) {
            console.error('Failed to load consumption:', error);
            this.hideLoading();
            this.showError(error.message || 'Failed to load consumption data');
        }
    },
    
    /**
     * Update consumption table
     */
    updateConsumptionTable() {
        const tableBody = document.getElementById('consumption-table-body');
        if (!tableBody) return;
        
        const entries = this.currentData?.entries || [];
        
        if (entries.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="empty-message">No consumption data found</td></tr>';
            return;
        }
        
        // Check if aggregated view
        const isAggregated = this.filters.aggregate_by || this.filters.granularity !== 'day';
        
        let html = '';
        entries.forEach(entry => {
            if (isAggregated) {
                // Aggregated view
                html += `
                    <tr>
                        <td>${entry.from_date || entry[this.filters.aggregate_by] || 'N/A'}</td>
                        <td>${entry.to_date || '-'}</td>
                        <td>${entry.service || entry.resource_type || entry.region || '-'}</td>
                        <td>${entry.resource_type || entry.type || '-'}</td>
                        <td>${entry.operation || '-'}</td>
                        <td>${this.formatNumber(entry.value || 0)}</td>
                        <td>${this.formatCurrency(entry.UnitPrice || entry.unit_price || 0, this.currentData?.metadata?.currency)}</td>
                        <td>${this.formatCurrency(entry.Price || entry.price || 0, this.currentData?.metadata?.currency)}</td>
                        <td>${entry.Region || entry.region || entry.Zone || entry.zone || '-'}</td>
                    </tr>
                `;
            } else {
                // Detailed view
                html += `
                    <tr>
                        <td>${entry.FromDate || entry.from_date || 'N/A'}</td>
                        <td>${entry.ToDate || entry.to_date || '-'}</td>
                        <td>${entry.Service || entry.service || '-'}</td>
                        <td>${entry.Type || entry.type || '-'}</td>
                        <td>${entry.Operation || entry.operation || '-'}</td>
                        <td>${this.formatNumber(entry.Value || entry.value || 0)}</td>
                        <td>${this.formatCurrency(entry.UnitPrice || entry.unit_price || 0, this.currentData?.metadata?.currency)}</td>
                        <td>${this.formatCurrency(entry.Price || entry.price || 0, this.currentData?.metadata?.currency)}</td>
                        <td>${entry.Region || entry.region || entry.Zone || entry.zone || '-'}</td>
                    </tr>
                `;
            }
        });
        
        tableBody.innerHTML = html;
    },
    
    /**
     * Update summary cards
     */
    updateSummaryCards() {
        const totals = this.currentData?.totals || {};
        const entries = this.currentData?.entries || [];
        const metadata = this.currentData?.metadata || {};
        
        // Get currency from metadata or default to USD
        const currency = metadata.currency || 'USD';
        
        // Calculate total cost from all entries (sum of Price field)
        let totalCost = 0;
        entries.forEach(entry => {
            const price = entry.Price || entry.price || 0;
            totalCost += parseFloat(price) || 0;
        });
        
        // Use calculated total or fallback to totals.total_price
        const finalTotalCost = totalCost > 0 ? totalCost : (totals.total_price || 0);
        
        // Calculate period count
        const periodCount = entries.length;
        
        // Calculate average daily cost
        const fromDate = new Date(this.filters.from_date);
        const toDate = new Date(this.filters.to_date);
        const daysDiff = Math.max(1, Math.ceil((toDate - fromDate) / (1000 * 60 * 60 * 24)));
        const avgDailyCost = finalTotalCost / daysDiff;
        
        // Update cards
        const totalCostCard = document.getElementById('consumption-total-cost');
        const periodCountCard = document.getElementById('consumption-period-count');
        const avgDailyCard = document.getElementById('consumption-avg-daily');
        
        if (totalCostCard) {
            totalCostCard.textContent = this.formatCurrency(finalTotalCost, currency);
        }
        if (periodCountCard) {
            periodCountCard.textContent = periodCount.toString();
        }
        if (avgDailyCard) {
            avgDailyCard.textContent = this.formatCurrency(avgDailyCost, currency);
        }
    },
    
    /**
     * Update top drivers
     */
    async updateTopDrivers() {
        const topDriversContainer = document.getElementById('consumption-top-drivers');
        if (!topDriversContainer) return;
        
        try {
            const params = {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date
            };
            
            if (this.filters.region) params.region = this.filters.region;
            if (this.filters.service) params.service = this.filters.service;
            if (this.filters.resource_type) params.resource_type = this.filters.resource_type;
            
            const response = await ConsumptionService.getTopDrivers(params, 10);
            const topDrivers = response.data?.top_drivers || [];
            
            if (topDrivers.length === 0) {
                topDriversContainer.innerHTML = '<p class="empty-message">No cost drivers found</p>';
                return;
            }
            
            let html = '<ul class="top-drivers-list">';
            topDrivers.forEach((driver, index) => {
                html += `
                    <li>
                        <span class="driver-rank">${index + 1}.</span>
                        <span class="driver-name">${driver.service}/${driver.resource_type}/${driver.operation}</span>
                        <span class="driver-cost">${this.formatCurrency(driver.total_price)}</span>
                    </li>
                `;
            });
            html += '</ul>';
            
            topDriversContainer.innerHTML = html;
        } catch (error) {
            console.error('Failed to load top drivers:', error);
            topDriversContainer.innerHTML = '<p class="error-message">Failed to load top drivers</p>';
        }
    },
    
    /**
     * Update filter options (service, resource_type) from current data
     */
    updateFilterOptions() {
        const entries = this.currentData?.entries || [];
        
        // Extract unique services and resource types
        const services = new Set();
        const resourceTypes = new Set();
        
        entries.forEach(entry => {
            const service = entry.Service || entry.service;
            const type = entry.Type || entry.type || entry.resource_type;
            
            if (service) services.add(service);
            if (type) resourceTypes.add(type);
        });
        
        // Update service dropdown
        const serviceSelect = document.getElementById('consumption-service');
        if (serviceSelect) {
            const currentValue = serviceSelect.value;
            let html = '<option value="">All Services</option>';
            Array.from(services).sort().forEach(service => {
                html += `<option value="${service}">${service}</option>`;
            });
            serviceSelect.innerHTML = html;
            if (currentValue) serviceSelect.value = currentValue;
        }
        
        // Update resource type dropdown
        const resourceTypeSelect = document.getElementById('consumption-resource-type');
        if (resourceTypeSelect) {
            const currentValue = resourceTypeSelect.value;
            let html = '<option value="">All Resource Types</option>';
            Array.from(resourceTypes).sort().forEach(type => {
                html += `<option value="${type}">${type}</option>`;
            });
            resourceTypeSelect.innerHTML = html;
            if (currentValue) resourceTypeSelect.value = currentValue;
        }
    },
    
    /**
     * Export consumption data
     */
    async exportData(format) {
        try {
            this.updateFiltersFromUI();
            
            const params = {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date,
                granularity: this.filters.granularity
            };
            
            if (this.filters.region) params.region = this.filters.region;
            if (this.filters.service) params.service = this.filters.service;
            if (this.filters.resource_type) params.resource_type = this.filters.resource_type;
            if (this.filters.aggregate_by) params.aggregate_by = this.filters.aggregate_by;
            
            if (format === 'csv') {
                const blob = await ConsumptionService.exportConsumption(params, 'csv');
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `consumption_${this.filters.from_date}_to_${this.filters.to_date}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const data = await ConsumptionService.exportConsumption(params, 'json');
                const jsonStr = JSON.stringify(data, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `consumption_${this.filters.from_date}_to_${this.filters.to_date}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
            
            this.showSuccess(`Exported consumption data as ${format.toUpperCase()}`);
        } catch (error) {
            console.error('Export error:', error);
            this.showError(error.message || 'Failed to export consumption data');
        }
    },
    
    /**
     * Format number
     */
    formatNumber(value) {
        if (typeof value !== 'number') return '0';
        return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    
    /**
     * Format currency
     */
    formatCurrency(value) {
        if (typeof value !== 'number') return '$0.00';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    },
    
    /**
     * Show loading indicator
     */
    showLoading() {
        const loadingEl = document.getElementById('consumption-loading');
        if (loadingEl) loadingEl.style.display = 'block';
        
        const tableBody = document.getElementById('consumption-table-body');
        if (tableBody) tableBody.innerHTML = '';
    },
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loadingEl = document.getElementById('consumption-loading');
        if (loadingEl) loadingEl.style.display = 'none';
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const errorEl = document.getElementById('consumption-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
    },
    
    /**
     * Hide error message
     */
    hideError() {
        const errorEl = document.getElementById('consumption-error');
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    },
    
    /**
     * Show success message
     */
    showSuccess(message) {
        // Simple success notification (could be enhanced with toast)
        console.log('Success:', message);
        // Could add a toast notification here
    }
};

