/**
 * Cost Builder UI module
 */
const CostBuilder = {
    currentData: null,
    filters: {
        region: '',
        tag_key: '',
        tag_value: '',
        include_oos: false
    },
    initialized: false,
    
    /**
     * Initialize cost builder
     */
    async init() {
        if (this.initialized) return;
        
        this.setupEventListeners();
        this.updateFilterUI();
        
        // Auto-load costs when tab is initialized
        await this.loadCurrentCosts();
        
        this.initialized = true;
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Fetch button (optional refresh, auto-loads on init)
        const fetchBtn = document.getElementById('fetch-cost-btn');
        if (fetchBtn) {
            fetchBtn.addEventListener('click', () => this.loadCurrentCosts());
        }
        
        // Export buttons
        const exportCsvBtn = document.getElementById('export-cost-csv-btn');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportCosts('csv'));
        }
        
        const exportJsonBtn = document.getElementById('export-cost-json-btn');
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportCosts('json'));
        }
        
        // Filter inputs
        const regionSelect = document.getElementById('cost-region');
        if (regionSelect) {
            regionSelect.addEventListener('change', () => this.updateFiltersFromUI());
        }
        
        const tagKeyInput = document.getElementById('cost-tag-key');
        if (tagKeyInput) {
            tagKeyInput.addEventListener('input', () => this.updateFiltersFromUI());
        }
        
        const tagValueInput = document.getElementById('cost-tag-value');
        if (tagValueInput) {
            tagValueInput.addEventListener('input', () => this.updateFiltersFromUI());
        }
        
        const includeOosCheckbox = document.getElementById('cost-include-oos');
        if (includeOosCheckbox) {
            includeOosCheckbox.addEventListener('change', () => this.updateFiltersFromUI());
        }
    },
    
    /**
     * Update filters from UI inputs
     */
    updateFiltersFromUI() {
        const regionSelect = document.getElementById('cost-region');
        const tagKeyInput = document.getElementById('cost-tag-key');
        const tagValueInput = document.getElementById('cost-tag-value');
        const includeOosCheckbox = document.getElementById('cost-include-oos');
        
        if (regionSelect) this.filters.region = regionSelect.value;
        if (tagKeyInput) this.filters.tag_key = tagKeyInput.value;
        if (tagValueInput) this.filters.tag_value = tagValueInput.value;
        if (includeOosCheckbox) this.filters.include_oos = includeOosCheckbox.checked;
    },
    
    /**
     * Update filter UI with current filter values
     */
    updateFilterUI() {
        const regionSelect = document.getElementById('cost-region');
        const tagKeyInput = document.getElementById('cost-tag-key');
        const tagValueInput = document.getElementById('cost-tag-value');
        const includeOosCheckbox = document.getElementById('cost-include-oos');
        
        if (regionSelect) regionSelect.value = this.filters.region;
        if (tagKeyInput) tagKeyInput.value = this.filters.tag_key;
        if (tagValueInput) tagValueInput.value = this.filters.tag_value;
        if (includeOosCheckbox) includeOosCheckbox.checked = this.filters.include_oos;
    },
    
    /**
     * Load current costs
     */
    async loadCurrentCosts() {
        this.showLoading();
        this.hideError();
        
        try {
            this.updateFiltersFromUI();
            
            // Build query parameters
            // Note: region is optional - API will use session region if not provided
            const params = {};
            if (this.filters.region) params.region = this.filters.region;
            if (this.filters.tag_key) params.tag_key = this.filters.tag_key;
            if (this.filters.tag_value) params.tag_value = this.filters.tag_value;
            if (this.filters.include_oos) params.include_oos = true;
            
            // Fetch data
            const response = await CostService.getCurrentCosts(params);
            
            // Store full response including metadata
            this.currentData = {
                ...response.data,
                metadata: response.metadata || {}
            };
            
            // Update UI
            this.updateCostTable();
            this.updateSummaryCards();
            this.updateBreakdown();
            
            this.hideLoading();
        } catch (error) {
            console.error('Failed to load current costs:', error);
            this.hideLoading();
            this.showError(error.message || 'Failed to load current cost data');
        }
    },
    
    /**
     * Update cost table
     */
    updateCostTable() {
        const tableBody = document.getElementById('cost-table-body');
        if (!tableBody) return;
        
        const resources = this.currentData?.resources || [];
        
        if (resources.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" class="empty-message">${typeof i18n !== 'undefined' ? i18n.t('cost.noResources') : 'No resources found.'}</td></tr>`;
            return;
        }
        
        const currency = this.currentData?.currency || this.currentData?.metadata?.currency || 'USD';
        
        let html = '';
        resources.forEach(resource => {
            html += `
                <tr>
                    <td>${resource.resource_id || 'N/A'}</td>
                    <td>${resource.resource_type || '-'}</td>
                    <td>${resource.region || '-'}</td>
                    <td>${resource.zone || '-'}</td>
                    <td>${this.formatCurrency(resource.cost_per_hour || 0, currency)}</td>
                    <td>${this.formatCurrency(resource.cost_per_month || 0, currency)}</td>
                    <td>${this.formatCurrency(resource.cost_per_year || 0, currency)}</td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    },
    
    /**
     * Update summary cards
     */
    updateSummaryCards() {
        const totals = this.currentData?.totals || {};
        const currency = this.currentData?.currency || this.currentData?.metadata?.currency || 'USD';
        
        const costPerHourCard = document.getElementById('cost-per-hour');
        const costPerMonthCard = document.getElementById('cost-per-month');
        const costPerYearCard = document.getElementById('cost-per-year');
        const resourceCountCard = document.getElementById('cost-resource-count');
        
        if (costPerHourCard) {
            costPerHourCard.textContent = this.formatCurrency(totals.cost_per_hour || 0, currency);
        }
        if (costPerMonthCard) {
            costPerMonthCard.textContent = this.formatCurrency(totals.cost_per_month || 0, currency);
        }
        if (costPerYearCard) {
            costPerYearCard.textContent = this.formatCurrency(totals.cost_per_year || 0, currency);
        }
        if (resourceCountCard) {
            resourceCountCard.textContent = (totals.resource_count || 0).toString();
        }
    },
    
    /**
     * Update breakdown sections
     */
    updateBreakdown() {
        const breakdown = this.currentData?.breakdown || {};
        const currency = this.currentData?.currency || this.currentData?.metadata?.currency || 'USD';
        
        // Breakdown by resource type
        const breakdownByTypeList = document.getElementById('breakdown-by-type-list');
        if (breakdownByTypeList) {
            const byType = breakdown.by_resource_type || {};
            let html = '';
            
            if (Object.keys(byType).length === 0) {
                html = `<li class="empty-message">${typeof i18n !== 'undefined' ? i18n.t('cost.noBreakdown') : 'No breakdown data available.'}</li>`;
            } else {
                for (const [resourceType, values] of Object.entries(byType)) {
                    html += `
                        <li>
                            <span>${resourceType} (${values.count || 0})</span>
                            <span>${this.formatCurrency(values.cost_per_month || 0, currency)}</span>
                        </li>
                    `;
                }
            }
            
            breakdownByTypeList.innerHTML = html;
        }
        
        // Breakdown by category
        const breakdownByCategoryList = document.getElementById('breakdown-by-category-list');
        if (breakdownByCategoryList) {
            const byCategory = breakdown.by_category || {};
            let html = '';
            
            if (Object.keys(byCategory).length === 0) {
                html = `<li class="empty-message">${typeof i18n !== 'undefined' ? i18n.t('cost.noBreakdown') : 'No breakdown data available.'}</li>`;
            } else {
                for (const [category, values] of Object.entries(byCategory)) {
                    html += `
                        <li>
                            <span>${category} (${values.count || 0})</span>
                            <span>${this.formatCurrency(values.cost_per_month || 0, currency)}</span>
                        </li>
                    `;
                }
            }
            
            breakdownByCategoryList.innerHTML = html;
        }
    },
    
    /**
     * Export costs
     */
    async exportCosts(format) {
        try {
            this.updateFiltersFromUI();
            
            const params = {};
            if (this.filters.region) params.region = this.filters.region;
            if (this.filters.tag_key) params.tag_key = this.filters.tag_key;
            if (this.filters.tag_value) params.tag_value = this.filters.tag_value;
            if (this.filters.include_oos) params.include_oos = true;
            
            await CostService.exportCosts(params, format);
            this.showSuccess(`Cost data exported as ${format.toUpperCase()}`);
        } catch (error) {
            console.error('Failed to export costs:', error);
            this.showError(error.message || 'Failed to export cost data');
        }
    },
    
    /**
     * Format currency
     */
    formatCurrency(value, currency = 'USD') {
        if (typeof value !== 'number') return `$0.00`;
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    },
    
    /**
     * Show loading message
     */
    showLoading() {
        const loadingEl = document.getElementById('cost-loading');
        if (loadingEl) loadingEl.style.display = 'block';
    },
    
    /**
     * Hide loading message
     */
    hideLoading() {
        const loadingEl = document.getElementById('cost-loading');
        if (loadingEl) loadingEl.style.display = 'none';
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const errorEl = document.getElementById('cost-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
    },
    
    /**
     * Hide error message
     */
    hideError() {
        const errorEl = document.getElementById('cost-error');
        if (errorEl) errorEl.style.display = 'none';
    },
    
    /**
     * Show success message
     */
    showSuccess(message) {
        // Simple alert for now, can be enhanced with toast notifications
        alert(message);
    }
};

