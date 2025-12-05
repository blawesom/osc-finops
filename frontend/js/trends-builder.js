/**
 * Trends Builder UI module
 */
const TrendsBuilder = {
    currentTrendData: null,
    currentDriftData: null,
    trendChart: null,
    filters: {
        from_date: '',
        to_date: '',
        granularity: 'day',
        region: '',
        resource_type: ''
    },
    driftThreshold: 10.0,
    initialized: false,
    
    /**
     * Initialize trends builder
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
        // Load trends button
        const loadTrendsBtn = document.getElementById('trends-load-btn');
        if (loadTrendsBtn) {
            loadTrendsBtn.addEventListener('click', () => this.loadTrends());
        }
        
        // Load drift button
        const loadDriftBtn = document.getElementById('trends-load-drift-btn');
        if (loadDriftBtn) {
            loadDriftBtn.addEventListener('click', () => this.loadDrift());
        }
        
        // Export buttons
        const exportCsvBtn = document.getElementById('trends-export-csv');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportTrends('csv'));
        }
        
        const exportJsonBtn = document.getElementById('trends-export-json');
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportTrends('json'));
        }
    },
    
    /**
     * Update filter UI with current filter values
     */
    updateFilterUI() {
        const fromDateInput = document.getElementById('trends-from-date');
        const toDateInput = document.getElementById('trends-to-date');
        const granularitySelect = document.getElementById('trends-granularity');
        const regionSelect = document.getElementById('trends-region');
        const resourceTypeInput = document.getElementById('trends-resource-type');
        const thresholdInput = document.getElementById('trends-threshold');
        
        if (fromDateInput) fromDateInput.value = this.filters.from_date;
        if (toDateInput) toDateInput.value = this.filters.to_date;
        if (granularitySelect) granularitySelect.value = this.filters.granularity;
        if (regionSelect) regionSelect.value = this.filters.region;
        if (resourceTypeInput) resourceTypeInput.value = this.filters.resource_type;
        if (thresholdInput) thresholdInput.value = this.driftThreshold;
    },
    
    /**
     * Get filters from UI
     */
    getFiltersFromUI() {
        const fromDateInput = document.getElementById('trends-from-date');
        const toDateInput = document.getElementById('trends-to-date');
        const granularitySelect = document.getElementById('trends-granularity');
        const regionSelect = document.getElementById('trends-region');
        const resourceTypeInput = document.getElementById('trends-resource-type');
        const thresholdInput = document.getElementById('trends-threshold');
        
        this.filters.from_date = fromDateInput?.value || '';
        this.filters.to_date = toDateInput?.value || '';
        this.filters.granularity = granularitySelect?.value || 'day';
        this.filters.region = regionSelect?.value || '';
        this.filters.resource_type = resourceTypeInput?.value || '';
        this.driftThreshold = parseFloat(thresholdInput?.value || '10.0');
    },
    
    /**
     * Show loading indicator
     */
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'block';
        }
    },
    
    /**
     * Hide loading indicator
     */
    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    },
    
    /**
     * Show error message
     */
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
        }
    },
    
    /**
     * Hide error message
     */
    hideError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    },
    
    /**
     * Load trend data using async job processing
     */
    async loadTrends() {
        try {
            this.getFiltersFromUI();
            
            // Validate dates
            if (!this.filters.from_date || !this.filters.to_date) {
                this.showError('trends-error', 'Please select both from and to dates');
                return;
            }
            
            // Show loading and progress
            this.showLoading('trends-loading');
            this.hideError('trends-error');
            this.showProgressBar();
            this.updateProgressBar(0);
            
            // Build params
            const params = {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date,
                granularity: this.filters.granularity
            };
            
            if (this.filters.region) {
                params.region = this.filters.region;
            }
            
            if (this.filters.resource_type) {
                params.resource_type = this.filters.resource_type;
            }
            
            // Submit async job
            const jobResponse = await TrendsService.submitTrendsJob(params);
            const jobId = jobResponse.job_id;
            
            // Poll job status with progress updates
            const onProgress = (progress, estimatedRemaining) => {
                this.updateProgressBar(progress, estimatedRemaining);
            };
            
            // Poll until complete
            const statusResponse = await TrendsService.pollJobStatus(jobId, onProgress, 2000);
            
            // Job completed, get result
            this.currentTrendData = statusResponse.result;
            
            // Render data
            this.renderTrends();
            
            // Hide loading and progress
            this.hideLoading('trends-loading');
            this.hideProgressBar();
        } catch (error) {
            console.error('Load trends error:', error);
            this.showError('trends-error', error.message || 'Failed to load trend data');
            this.hideLoading('trends-loading');
            this.hideProgressBar();
        }
    },
    
    /**
     * Show progress bar
     */
    showProgressBar() {
        const progressBar = document.getElementById('trends-progress-bar');
        const progressContainer = document.getElementById('trends-progress-container');
        if (progressBar) progressBar.style.display = 'block';
        if (progressContainer) progressContainer.style.display = 'block';
    },
    
    /**
     * Hide progress bar
     */
    hideProgressBar() {
        const progressBar = document.getElementById('trends-progress-bar');
        const progressContainer = document.getElementById('trends-progress-container');
        if (progressBar) progressBar.style.display = 'none';
        if (progressContainer) progressContainer.style.display = 'none';
    },
    
    /**
     * Update progress bar
     */
    updateProgressBar(progress, estimatedRemaining = null) {
        const progressBar = document.getElementById('trends-progress-bar');
        const progressText = document.getElementById('trends-progress-text');
        const progressTime = document.getElementById('trends-progress-time');
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        if (progressText) {
            progressText.textContent = `${progress}%`;
        }
        
        if (progressTime && estimatedRemaining !== null && estimatedRemaining > 0) {
            const minutes = Math.floor(estimatedRemaining / 60);
            const seconds = estimatedRemaining % 60;
            if (minutes > 0) {
                progressTime.textContent = `Estimated time remaining: ${minutes}m ${seconds}s`;
            } else {
                progressTime.textContent = `Estimated time remaining: ${seconds}s`;
            }
        } else if (progressTime) {
            progressTime.textContent = '';
        }
    },
    
    /**
     * Load drift data
     */
    async loadDrift() {
        try {
            this.getFiltersFromUI();
            
            // Validate dates
            if (!this.filters.from_date || !this.filters.to_date) {
                this.showError('trends-drift-error', 'Please select both from and to dates');
                return;
            }
            
            // Show loading
            this.showLoading('trends-drift-loading');
            this.hideError('trends-drift-error');
            
            // Build params
            const params = {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date,
                threshold: this.driftThreshold
            };
            
            if (this.filters.region) {
                params.region = this.filters.region;
            }
            
            // Fetch data
            const response = await TrendsService.getDrift(params);
            this.currentDriftData = response.data;
            
            // Render drift
            this.renderDrift();
            
            // Hide loading
            this.hideLoading('trends-drift-loading');
        } catch (error) {
            console.error('Load drift error:', error);
            this.showError('trends-drift-error', error.message || 'Failed to load drift data');
            this.hideLoading('trends-drift-loading');
        }
    },
    
    /**
     * Render trend data
     */
    renderTrends() {
        if (!this.currentTrendData) {
            return;
        }
        
        const data = this.currentTrendData;
        const currency = data.currency || 'EUR';
        
        // Update summary cards
        const growthRateEl = document.getElementById('trends-growth-rate');
        const avgCostEl = document.getElementById('trends-avg-cost');
        const totalCostEl = document.getElementById('trends-total-cost');
        const trendDirectionEl = document.getElementById('trends-direction');
        
        if (growthRateEl) {
            const sign = data.growth_rate >= 0 ? '+' : '';
            growthRateEl.textContent = `${sign}${data.growth_rate.toFixed(2)}%`;
            growthRateEl.className = data.growth_rate >= 0 ? 'positive' : 'negative';
        }
        
        if (avgCostEl) {
            avgCostEl.textContent = `${currency} ${data.historical_average.toFixed(2)}`;
        }
        
        if (totalCostEl) {
            totalCostEl.textContent = `${currency} ${data.total_cost.toFixed(2)}`;
        }
        
        if (trendDirectionEl) {
            trendDirectionEl.textContent = data.trend_direction.charAt(0).toUpperCase() + data.trend_direction.slice(1);
            trendDirectionEl.className = data.trend_direction;
        }
        
        // Render chart
        this.renderTrendChart();
    },
    
    /**
     * Render trend chart using Chart.js
     */
    renderTrendChart() {
        if (!this.currentTrendData || !window.Chart) {
            return;
        }
        
        const data = this.currentTrendData;
        const periods = data.periods || [];
        
        if (periods.length === 0) {
            return;
        }
        
        const ctx = document.getElementById('trends-chart');
        if (!ctx) {
            return;
        }
        
        // Destroy existing chart
        if (this.trendChart) {
            this.trendChart.destroy();
        }
        
        // Prepare chart data
        const labels = periods.map(p => p.period);
        const costs = periods.map(p => p.cost);
        
        // Create chart
        this.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `Cost (${data.currency})`,
                    data: costs,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Cost Trend Over Time'
                    },
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: `Cost (${data.currency})`
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Period'
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Render drift data
     */
    renderDrift() {
        if (!this.currentDriftData) {
            return;
        }
        
        const data = this.currentDriftData;
        const currency = data.currency || 'EUR';
        
        // Update drift summary
        const overallDriftEl = document.getElementById('drift-overall');
        const totalEstimatedEl = document.getElementById('drift-total-estimated');
        const totalActualEl = document.getElementById('drift-total-actual');
        const driftAmountEl = document.getElementById('drift-amount');
        
        if (overallDriftEl) {
            const sign = data.overall_drift >= 0 ? '+' : '';
            overallDriftEl.textContent = `${sign}${data.overall_drift.toFixed(2)}%`;
            overallDriftEl.className = data.overall_drift >= 0 ? 'positive' : 'negative';
        }
        
        if (totalEstimatedEl) {
            totalEstimatedEl.textContent = `${currency} ${data.total_estimated.toFixed(2)}`;
        }
        
        if (totalActualEl) {
            totalActualEl.textContent = `${currency} ${data.total_actual.toFixed(2)}`;
        }
        
        if (driftAmountEl) {
            const sign = data.overall_drift_amount >= 0 ? '+' : '';
            driftAmountEl.textContent = `${sign}${currency} ${Math.abs(data.overall_drift_amount).toFixed(2)}`;
            driftAmountEl.className = data.overall_drift_amount >= 0 ? 'positive' : 'negative';
        }
        
        // Render drift table
        this.renderDriftTable();
    },
    
    /**
     * Render drift table
     */
    renderDriftTable() {
        if (!this.currentDriftData) {
            return;
        }
        
        const data = this.currentDriftData;
        const currency = data.currency || 'EUR';
        const driftByCategory = data.drift_by_category || [];
        const tbody = document.getElementById('drift-table-body');
        
        if (!tbody) {
            return;
        }
        
        // Clear existing rows
        tbody.innerHTML = '';
        
        if (driftByCategory.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-message">No drift data available</td></tr>';
            return;
        }
        
        // Add rows
        driftByCategory.forEach(item => {
            const row = document.createElement('tr');
            const driftClass = Math.abs(item.drift_percent) >= data.threshold ? 'significant' : '';
            const driftSign = item.drift_percent >= 0 ? '+' : '';
            
            row.innerHTML = `
                <td>${item.resource_type || 'Unknown'}</td>
                <td>${currency} ${item.estimated_cost.toFixed(2)}</td>
                <td>${currency} ${item.actual_cost.toFixed(2)}</td>
                <td>${currency} ${item.drift_amount.toFixed(2)}</td>
                <td class="${driftClass}">${driftSign}${item.drift_percent.toFixed(2)}%</td>
                <td>${item.estimated_count || 0} / ${item.actual_count || 0}</td>
            `;
            
            tbody.appendChild(row);
        });
    },
    
    /**
     * Export trends data
     */
    async exportTrends(format) {
        try {
            if (!this.currentTrendData) {
                this.showError('trends-error', 'Please load trend data first');
                return;
            }
            
            this.getFiltersFromUI();
            
            const params = {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date,
                granularity: this.filters.granularity
            };
            
            if (this.filters.region) {
                params.region = this.filters.region;
            }
            
            if (this.filters.resource_type) {
                params.resource_type = this.filters.resource_type;
            }
            
            await TrendsService.exportTrends(params, format);
        } catch (error) {
            console.error('Export trends error:', error);
            this.showError('trends-error', error.message || 'Failed to export trend data');
        }
    }
};

