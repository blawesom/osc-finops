/**
 * Cost Management Builder UI module
 * Unified view combining consumption, trends, and budget management
 */
const CostManagementBuilder = {
    currentConsumptionData: null,
    currentTrendData: null,
    currentBudgets: [],
    selectedBudget: null,
    budgetStatus: null,
    chart: null,
    filters: {
        from_date: '',
        to_date: '',
        granularity: 'day',
        region: ''
    },
    editingBudgetId: null,
    initialized: false,
    viewMode: 'simple', // 'simple' or 'compounded'
    
    /**
     * Initialize cost management builder
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
        
        // Load budgets
        await this.loadBudgets();
        
        // Set initial view mode UI state (default to simple if no budget selected)
        if (!this.selectedBudget) {
            this.setViewMode('simple');
        }
        
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
     * Set view mode (simple or compounded) and update UI
     * @param {string} mode - 'simple' or 'compounded'
     */
    setViewMode(mode) {
        if (mode !== 'simple' && mode !== 'compounded') {
            return;
        }
        
        this.viewMode = mode;
        
        // Update UI toggle buttons
        const simpleBtn = document.getElementById('cm-view-simple');
        const compoundedBtn = document.getElementById('cm-view-compounded');
        
        if (simpleBtn && compoundedBtn) {
            if (mode === 'simple') {
                simpleBtn.classList.add('active');
                simpleBtn.classList.remove('btn-secondary');
                simpleBtn.classList.add('btn-primary');
                compoundedBtn.classList.remove('active');
                compoundedBtn.classList.remove('btn-primary');
                compoundedBtn.classList.add('btn-secondary');
            } else {
                compoundedBtn.classList.add('active');
                compoundedBtn.classList.remove('btn-secondary');
                compoundedBtn.classList.add('btn-primary');
                simpleBtn.classList.remove('active');
                simpleBtn.classList.remove('btn-primary');
                simpleBtn.classList.add('btn-secondary');
            }
        }
        
        // Re-render chart with new view mode
        if (this.chart || (this.currentConsumptionData || this.currentTrendData)) {
            this.renderChart();
        }
    },
    
    /**
     * Get granularity from budget period type
     * Maps budget period_type to appropriate granularity:
     * - monthly → week
     * - quarterly → month
     * - yearly → month
     * 
     * @param {string} periodType - Budget period type ('monthly', 'quarterly', 'yearly')
     * @returns {string} Granularity ('day', 'week', 'month')
     */
    getGranularityFromBudgetPeriodType(periodType) {
        if (periodType === 'monthly') {
            return 'week';
        } else if (periodType === 'quarterly' || periodType === 'yearly') {
            return 'month';
        }
        // Default fallback
        return 'day';
    },
    
    /**
     * Calculate default to_date when budget has no end_date
     * Calculates based on period_type and caps at today's date if in the future
     * 
     * @param {string} startDate - Budget start date (YYYY-MM-DD)
     * @param {string} periodType - Budget period type ('monthly', 'quarterly', 'yearly')
     * @returns {string} Calculated to_date (YYYY-MM-DD)
     */
    calculateDefaultToDate(startDate, periodType) {
        const start = new Date(startDate);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        let calculatedDate = new Date(start);
        
        if (periodType === 'monthly') {
            calculatedDate.setMonth(calculatedDate.getMonth() + 1);
        } else if (periodType === 'quarterly') {
            calculatedDate.setMonth(calculatedDate.getMonth() + 3);
        } else if (periodType === 'yearly') {
            calculatedDate.setFullYear(calculatedDate.getFullYear() + 1);
        } else {
            // Default: add 1 month
            calculatedDate.setMonth(calculatedDate.getMonth() + 1);
        }
        
        // Cap at today's date if calculated date is in the future
        if (calculatedDate > today) {
            calculatedDate = today;
        }
        
        return this.formatDate(calculatedDate);
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Load data button
        const loadBtn = document.getElementById('cm-load-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.loadData());
        }
        
        // Create budget button
        const createBudgetBtn = document.getElementById('cm-create-budget-btn');
        if (createBudgetBtn) {
            createBudgetBtn.addEventListener('click', () => this.showBudgetModal());
        }
        
        // Export buttons
        const exportCsvBtn = document.getElementById('cm-export-csv');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportData('csv'));
        }
        
        const exportJsonBtn = document.getElementById('cm-export-json');
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportData('json'));
        }
        
        // View toggle buttons
        const simpleViewBtn = document.getElementById('cm-view-simple');
        if (simpleViewBtn) {
            simpleViewBtn.addEventListener('click', () => this.setViewMode('simple'));
        }
        
        const compoundedViewBtn = document.getElementById('cm-view-compounded');
        if (compoundedViewBtn) {
            compoundedViewBtn.addEventListener('click', () => this.setViewMode('compounded'));
        }
    },
    
    /**
     * Update filter UI with current filter values
     */
    updateFilterUI() {
        const fromDateInput = document.getElementById('cm-from-date');
        const toDateInput = document.getElementById('cm-to-date');
        const granularitySelect = document.getElementById('cm-granularity');
        const regionSelect = document.getElementById('cm-region');
        
        if (fromDateInput) fromDateInput.value = this.filters.from_date;
        if (toDateInput) toDateInput.value = this.filters.to_date;
        if (granularitySelect) granularitySelect.value = this.filters.granularity;
        if (regionSelect) regionSelect.value = this.filters.region;
    },
    
    /**
     * Get filters from UI
     */
    getFiltersFromUI() {
        const fromDateInput = document.getElementById('cm-from-date');
        const toDateInput = document.getElementById('cm-to-date');
        const granularitySelect = document.getElementById('cm-granularity');
        const regionSelect = document.getElementById('cm-region');
        
        this.filters.from_date = fromDateInput?.value || '';
        this.filters.to_date = toDateInput?.value || '';
        this.filters.granularity = granularitySelect?.value || 'day';
        this.filters.region = regionSelect?.value || '';
    },
    
    /**
     * Show loading indicator
     */
    showLoading() {
        const element = document.getElementById('cost-management-loading');
        if (element) {
            element.style.display = 'block';
        }
    },
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        const element = document.getElementById('cost-management-loading');
        if (element) {
            element.style.display = 'none';
        }
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const element = document.getElementById('cost-management-error');
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
        }
    },
    
    /**
     * Hide error message
     */
    hideError() {
        const element = document.getElementById('cost-management-error');
        if (element) {
            element.style.display = 'none';
        }
    },
    
    /**
     * Show progress bar
     */
    showProgressBar() {
        const progressBar = document.getElementById('cm-progress-bar');
        const progressContainer = document.getElementById('cm-progress-container');
        if (progressBar) progressBar.style.display = 'block';
        if (progressContainer) progressContainer.style.display = 'block';
    },
    
    /**
     * Hide progress bar
     */
    hideProgressBar() {
        const progressBar = document.getElementById('cm-progress-bar');
        const progressContainer = document.getElementById('cm-progress-container');
        if (progressBar) progressBar.style.display = 'none';
        if (progressContainer) progressContainer.style.display = 'none';
    },
    
    /**
     * Update progress bar
     */
    updateProgressBar(progress, estimatedRemaining = null) {
        const progressBar = document.getElementById('cm-progress-bar');
        const progressText = document.getElementById('cm-progress-text');
        const progressTime = document.getElementById('cm-progress-time');
        
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
                progressTime.textContent = typeof i18n !== 'undefined' 
                    ? i18n.t('cm.progress.estimated', { time: `${minutes}m ${seconds}s` })
                    : `Estimated time remaining: ${minutes}m ${seconds}s`;
            } else {
                progressTime.textContent = typeof i18n !== 'undefined' 
                    ? i18n.t('cm.progress.estimated', { time: `${seconds}s` })
                    : `Estimated time remaining: ${seconds}s`;
            }
        } else if (progressTime) {
            progressTime.textContent = '';
        }
    },
    
    /**
     * Load all data (consumption, trends, budget status)
     * 
     * Validation rules (enforced by backend):
     * - from_date must be in the past
     * - to_date must be >= from_date + 1 granularity period
     * 
     * Functional rules (not validation):
     * - If from_date is in the past: do not show projected trend
     * - If from_date is in the future: query consumption until last period excluding today, then project trend
     * - When budget is selected: dates are rounded to budget period boundaries, consumption is cumulative
     */
    async loadData() {
        try {
            this.getFiltersFromUI();
            
            // Basic presence check for user experience (all other validation happens on backend)
            if (!this.filters.from_date || !this.filters.to_date) {
                this.showError(typeof i18n !== 'undefined' ? i18n.t('common.error') : 'Please select both from and to dates');
                return;
            }
            
            this.showLoading();
            this.hideError();
            
            // Load trend data - backend automatically projects when to_date is after yesterday
            const trendParams = {
                from_date: this.filters.from_date,
                to_date: this.filters.to_date,
                granularity: this.filters.granularity
            };
            
            if (this.filters.region) {
                trendParams.region = this.filters.region;
            }
            
            // Pass budget_id for boundary alignment (optional)
            if (this.selectedBudget) {
                trendParams.budget_id = this.selectedBudget.budget_id;
            }
            
            // Show progress bar for trends loading (async job)
            this.showProgressBar();
            this.updateProgressBar(0);
            
            // Load trends using async job
            try {
                const jobResponse = await TrendsService.submitTrendsJob(trendParams);
                const jobId = jobResponse.job_id;
                
                const onProgress = (progress, estimatedRemaining) => {
                    this.updateProgressBar(progress, estimatedRemaining);
                };
                
                const statusResponse = await TrendsService.pollJobStatus(jobId, onProgress, 2000);
                this.currentTrendData = statusResponse.result;
            } catch (error) {
                this.showError(error.message || 'Failed to load trends');
                this.currentTrendData = null;
            } finally {
                // Hide progress bar after trends loading completes
                this.hideProgressBar();
            }
            
            // Extract consumption data from trend periods
            if (this.currentTrendData) {
                const consumptionData = this.extractConsumptionFromTrends(this.currentTrendData);
                this.currentConsumptionData = consumptionData;
                this.currentConsumptionMetaData = {
                    from_date: this.filters.from_date,
                    to_date: this.filters.to_date,
                    region: this.filters.region || this.currentTrendData.region,
                    currency: this.currentTrendData.currency,
                    granularity: this.filters.granularity
                };
                this.currentConsumptionTotals = {
                    total_price: consumptionData.entries.reduce((sum, e) => sum + (e.Price || e.price || 0), 0),
                    total_value: consumptionData.entries.reduce((sum, e) => sum + (e.Value || e.value || 0), 0),
                    entry_count: consumptionData.entries.length
                };
            }
            
            // Load budget status if budget is selected
            if (this.selectedBudget) {
                const budgetStatusResponse = await BudgetService.getBudgetStatus(
                    this.selectedBudget.budget_id,
                    {
                        from_date: this.filters.from_date,
                        to_date: this.filters.to_date
                    }
                );
                this.budgetStatus = budgetStatusResponse.data;
            }
            
            // Render all data
            this.renderData();
            
            this.hideLoading();
        } catch (error) {
            console.error('Load data error:', error);
            this.showError(error.message || 'Failed to load data');
            this.hideLoading();
            this.hideProgressBar();
        }
    },
    
    /**
     * Extract consumption data from trend service periods
     * Transforms trend periods into consumption entries format for chart compatibility
     * 
     * @param {Object} trendData - Trend data from trend service
     * @returns {Object} Consumption data in the same format as consumption service response
     */
    extractConsumptionFromTrends(trendData) {
        if (!trendData || !trendData.periods) {
            return { entries: [], currency: 'EUR', region: '', from_date: '', to_date: '' };
        }
        
        // Filter out projected periods (only historical for consumption)
        const historicalPeriods = trendData.periods.filter(p => !p.projected);
        
        const entries = historicalPeriods.map(period => ({
            FromDate: period.from_date,
            ToDate: period.to_date,
            from_date: period.from_date,
            to_date: period.to_date,
            Price: period.cost,
            price: period.cost,
            Value: period.value,
            value: period.value,
            Region: trendData.region || '',
            region: trendData.region || ''
        }));
        
        return {
            entries: entries,
            currency: trendData.currency || 'EUR',
            region: trendData.region || '',
            from_date: trendData.from_date,
            to_date: trendData.to_date,
            entry_count: entries.length
        };
    },
    
    /**
     * Load budgets list
     */
    async loadBudgets() {
        try {
            const response = await BudgetService.listBudgets();
            this.currentBudgets = response.data || [];
            this.renderBudgetsList();
        } catch (error) {
            console.error('Load budgets error:', error);
            // Don't show error for budgets, just log it
        }
    },
    
    /**
     * Render budgets list
     */
    renderBudgetsList() {
        const listContainer = document.getElementById('cm-budgets-list');
        if (!listContainer) {
            return;
        }
        
        if (this.currentBudgets.length === 0) {
            listContainer.innerHTML = `<p class="empty-message">${typeof i18n !== 'undefined' ? i18n.t('cm.noBudgets') : 'No budgets created. Click "Create Budget" to get started.'}</p>`;
            return;
        }
        
        let html = '<div class="budgets-list-items">';
        this.currentBudgets.forEach(budget => {
            const isSelected = this.selectedBudget && this.selectedBudget.budget_id === budget.budget_id;
            html += `
                <div class="budget-item ${isSelected ? 'selected' : ''}" data-budget-id="${budget.budget_id}">
                    <div style="flex: 1;">
                        <h4>${budget.name}</h4>
                        <p style="margin: 4px 0; color: #666;">
                            ${budget.amount.toFixed(2)} ${budget.period_type} | 
                            Start: ${budget.start_date}${budget.end_date ? ` | End: ${budget.end_date}` : ''}
                        </p>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-small ${isSelected ? 'btn-secondary' : 'btn-primary'}" 
                                onclick="${isSelected ? 'CostManagementBuilder.deselectBudget()' : `CostManagementBuilder.selectBudget('${budget.budget_id}')`}">
                            ${isSelected ? 'Selected' : 'Select'}
                        </button>
                        <button class="btn btn-small btn-secondary" 
                                onclick="CostManagementBuilder.editBudget('${budget.budget_id}')">
                            Edit
                        </button>
                        <button class="btn btn-small btn-danger" 
                                onclick="CostManagementBuilder.deleteBudget('${budget.budget_id}')">
                            Delete
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        listContainer.innerHTML = html;
    },
    
    /**
     * Deselect current budget
     */
    async deselectBudget() {
        this.selectedBudget = null;
        this.renderBudgetsList();
        
        // Set default view to simple when budget is deselected
        this.setViewMode('simple');
        
        // Reload data if we have filters
        if (this.filters.from_date && this.filters.to_date) {
            await this.loadData();
        }
    },
    
    /**
     * Select a budget
     */
    async selectBudget(budgetId) {
        const budget = this.currentBudgets.find(b => b.budget_id === budgetId);
        if (!budget) {
            return;
        }
        
        this.selectedBudget = budget;
        this.renderBudgetsList();
        
        // Set default view to compounded when budget is selected
        this.setViewMode('compounded');
        
        // Automatically set dates and granularity based on budget
        this.filters.from_date = budget.start_date;
        
        // Set to_date: use budget's end_date if available, otherwise calculate default
        if (budget.end_date) {
            this.filters.to_date = budget.end_date;
        } else {
            this.filters.to_date = this.calculateDefaultToDate(budget.start_date, budget.period_type);
        }
        
        // Set granularity based on budget period type
        this.filters.granularity = this.getGranularityFromBudgetPeriodType(budget.period_type);
        
        // Update UI fields
        this.updateFilterUI();
        
        // Refresh data with new filters
        await this.loadData();
    },
    
    /**
     * Show budget modal
     */
    showBudgetModal(budgetId = null) {
        this.editingBudgetId = budgetId;
        const modal = document.getElementById('cm-budget-modal');
        const title = document.getElementById('cm-budget-modal-title');
        const saveBtn = document.getElementById('cm-budget-save-btn');
        
        if (!modal) {
            return;
        }
        
        if (budgetId) {
            const budget = this.currentBudgets.find(b => b.budget_id === budgetId);
            if (budget) {
                title.textContent = typeof i18n !== 'undefined' ? i18n.t('cm.budgetModal.edit') : 'Edit Budget';
                saveBtn.textContent = typeof i18n !== 'undefined' ? i18n.t('cm.budgetModal.updateBtn') : 'Update';
                document.getElementById('cm-budget-name').value = budget.name;
                document.getElementById('cm-budget-amount').value = budget.amount;
                document.getElementById('cm-budget-period-type').value = budget.period_type;
                document.getElementById('cm-budget-start-date').value = budget.start_date;
                document.getElementById('cm-budget-end-date').value = budget.end_date || '';
            }
        } else {
            title.textContent = typeof i18n !== 'undefined' ? i18n.t('cm.budgetModal.create') : 'Create Budget';
            saveBtn.textContent = typeof i18n !== 'undefined' ? i18n.t('cm.budgetModal.createBtn') : 'Create';
            document.getElementById('cm-budget-name').value = '';
            document.getElementById('cm-budget-amount').value = '';
            document.getElementById('cm-budget-period-type').value = 'monthly';
            document.getElementById('cm-budget-start-date').value = '';
            document.getElementById('cm-budget-end-date').value = '';
        }
        
        // Hide error
        const errorEl = document.getElementById('cm-budget-modal-error');
        if (errorEl) {
            errorEl.style.display = 'none';
        }
        
        modal.style.display = 'flex';
    },
    
    /**
     * Hide budget modal
     */
    hideBudgetModal() {
        const modal = document.getElementById('cm-budget-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.editingBudgetId = null;
    },
    
    /**
     * Save budget (create or update)
     */
    async saveBudget() {
        try {
            const name = document.getElementById('cm-budget-name').value.trim();
            const amount = parseFloat(document.getElementById('cm-budget-amount').value);
            const periodType = document.getElementById('cm-budget-period-type').value;
            const startDate = document.getElementById('cm-budget-start-date').value;
            const endDate = document.getElementById('cm-budget-end-date').value.trim() || null;
            
            // Validation
            if (!name) {
                this.showBudgetModalError('Budget name is required');
                return;
            }
            
            if (!amount || amount <= 0) {
                this.showBudgetModalError('Budget amount must be greater than 0');
                return;
            }
            
            if (!startDate) {
                this.showBudgetModalError('Start date is required');
                return;
            }
            
            if (endDate && endDate <= startDate) {
                this.showBudgetModalError('End date must be after start date');
                return;
            }
            
            const budgetData = {
                name,
                amount,
                period_type: periodType,
                start_date: startDate,
                end_date: endDate
            };
            
            if (this.editingBudgetId) {
                // Update
                await BudgetService.updateBudget(this.editingBudgetId, budgetData);
            } else {
                // Create
                await BudgetService.createBudget(budgetData);
            }
            
            // Reload budgets
            await this.loadBudgets();
            
            // Hide modal
            this.hideBudgetModal();
            
            // Reload data if we have filters
            if (this.filters.from_date && this.filters.to_date) {
                await this.loadData();
            }
        } catch (error) {
            console.error('Save budget error:', error);
            this.showBudgetModalError(error.message || 'Failed to save budget');
        }
    },
    
    /**
     * Show error in budget modal
     */
    showBudgetModalError(message) {
        const errorEl = document.getElementById('cm-budget-modal-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
    },
    
    /**
     * Edit budget
     */
    editBudget(budgetId) {
        this.showBudgetModal(budgetId);
    },
    
    /**
     * Delete budget
     */
    async deleteBudget(budgetId) {
        if (!confirm('Are you sure you want to delete this budget?')) {
            return;
        }
        
        try {
            await BudgetService.deleteBudget(budgetId);
            
            // Clear selection if deleted budget was selected
            if (this.selectedBudget && this.selectedBudget.budget_id === budgetId) {
                this.selectedBudget = null;
                // Set default view to simple when budget is deselected
                this.setViewMode('simple');
            }
            
            // Reload budgets
            await this.loadBudgets();
            
            // Reload data if we have filters
            if (this.filters.from_date && this.filters.to_date) {
                await this.loadData();
            }
        } catch (error) {
            console.error('Delete budget error:', error);
            alert(error.message || 'Failed to delete budget');
        }
    },
    
    /**
     * Render all data (summary, chart, table)
     */
    renderData() {
        this.renderSummary();
        this.renderChart();
        this.renderTable();
    },
    
    /**
     * Render summary cards
     */
    renderSummary() {
        const currency = this.currentConsumptionData?.currency || this.currentTrendData?.currency || 'EUR';
        
        // Calculate total consumption
        let totalConsumption = 0;
        if (this.currentConsumptionData && this.currentConsumptionData.entries) {
            totalConsumption = this.currentConsumptionData.entries.reduce((sum, entry) => {
                return sum + (parseFloat(entry.Price || entry.price || 0) || 0);
            }, 0);
        }
        
        // Get budget totals
        let totalBudget = 0;
        let totalRemaining = 0;
        if (this.budgetStatus) {
            totalBudget = this.budgetStatus.total_budget || 0;
            totalRemaining = totalBudget - totalConsumption || 0;
            // totalRemaining = this.budgetStatus.total_remaining || 0;
        }
        
        // Get trend direction
        const trendDirection = this.currentTrendData?.trend_direction || '-';
        
        // Update summary cards
        const totalConsumptionEl = document.getElementById('cm-total-consumption');
        const totalBudgetEl = document.getElementById('cm-total-budget');
        const remainingBudgetEl = document.getElementById('cm-remaining-budget');
        const trendDirectionEl = document.getElementById('cm-trend-direction');
        
        if (totalConsumptionEl) {
            totalConsumptionEl.textContent = `${currency} ${totalConsumption.toFixed(2)}`;
        }
        
        if (totalBudgetEl) {
            totalBudgetEl.textContent = `${currency} ${totalBudget.toFixed(2)}`;
        }
        
        if (remainingBudgetEl) {
            remainingBudgetEl.textContent = `${currency} ${totalRemaining.toFixed(2)}`;
            remainingBudgetEl.className = totalRemaining < 0 ? 'negative' : '';
        }
        
        if (trendDirectionEl) {
            trendDirectionEl.textContent = trendDirection.charAt(0).toUpperCase() + trendDirection.slice(1);
            trendDirectionEl.className = trendDirection;
        }
    },
    
    /**
     * Render unified chart
     */
    renderChart() {
        if (!window.Chart) {
            return;
        }
        
        const ctx = document.getElementById('cm-chart');
        if (!ctx) {
            return;
        }
        
        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }
        
        const currency = this.currentConsumptionData?.currency || this.currentTrendData?.currency || 'EUR';
        
        // Collect all data sources and build unified label set
        const consumptionByPeriod = {};
        const trendByPeriod = {};
        const budgetByPeriod = {};
        
        // Collect consumption data
        if (this.currentConsumptionData && this.currentConsumptionData.entries) {
            const aggregated = this.aggregateConsumptionByPeriod();
            Object.assign(consumptionByPeriod, aggregated);
        }
        
        // Collect trend data
        if (this.currentTrendData && this.currentTrendData.periods) {
            this.currentTrendData.periods.forEach(p => {
                trendByPeriod[p.period] = p.cost;
            });
        }
        
        // Collect budget data
        // Map budget periods to trend period keys and distribute across all periods within budget period
        if (this.budgetStatus && this.budgetStatus.periods) {
            this.budgetStatus.periods.forEach(budgetPeriod => {
                const budgetStart = new Date(budgetPeriod.start_date);
                const budgetEnd = new Date(budgetPeriod.end_date);
                const budgetAmount = budgetPeriod.budget_amount;
                
                // For yearly/quarterly budgets, distribute budget across all trend periods within the budget period
                // For monthly budgets, map directly to the period
                if (this.selectedBudget && (this.selectedBudget.period_type === 'yearly' || this.selectedBudget.period_type === 'quarterly')) {
                    // Distribute budget across all trend periods within this budget period
                    if (this.currentTrendData && this.currentTrendData.periods) {
                        this.currentTrendData.periods.forEach(trendPeriod => {
                            // Get the period date - use from_date if available, otherwise parse period field
                            let trendPeriodDate;
                            if (trendPeriod.from_date) {
                                trendPeriodDate = new Date(trendPeriod.from_date);
                            } else if (trendPeriod.period) {
                                // For monthly, period is "YYYY-MM", convert to first day of month
                                if (this.filters.granularity === 'month' && trendPeriod.period.match(/^\d{4}-\d{2}$/)) {
                                    const [year, month] = trendPeriod.period.split('-').map(Number);
                                    trendPeriodDate = new Date(year, month - 1, 1);
                                } else {
                                    trendPeriodDate = new Date(trendPeriod.period);
                                }
                            } else {
                                return; // Skip if we can't determine the date
                            }
                            
                            // Check if trend period falls within budget period
                            // Compare dates (set time to 0 for accurate comparison)
                            budgetStart.setHours(0, 0, 0, 0);
                            budgetEnd.setHours(23, 59, 59, 999);
                            trendPeriodDate.setHours(0, 0, 0, 0);
                            
                            if (trendPeriodDate >= budgetStart && trendPeriodDate <= budgetEnd) {
                                // Use the trend period's period key to match with trend data
                                const periodKey = trendPeriod.period;
                                budgetByPeriod[periodKey] = budgetAmount;
                            }
                        });
                    }
                } else {
                    // For monthly budgets, map directly using period key format
                    const periodKey = this.getPeriodKey(budgetPeriod.start_date, this.filters.granularity);
                    budgetByPeriod[periodKey] = budgetAmount;
                }
            });
        }
        
        // Calculate projected cost by repeating last consumption value
        // Simplified projection: all projected periods use the same cost as the last queriable period
        const projectedCostByPeriod = {};
        if (Object.keys(consumptionByPeriod).length > 0) {
            // Determine end date for projection (use budget end_date if available, otherwise to_date)
            let projectionEndDate = this.filters.to_date;
            if (this.selectedBudget && this.selectedBudget.end_date) {
                projectionEndDate = this.selectedBudget.end_date;
            }
            
            // Note: growthRate parameter kept for backward compatibility but not used in calculation
            const growthRate = this.currentTrendData?.growth_rate || 0;
            const projected = this.calculateProjectedCost(
                consumptionByPeriod,
                growthRate,
                this.filters.granularity,
                projectionEndDate
            );
            Object.assign(projectedCostByPeriod, projected);
        }
        
        // Get all unique labels and sort
        const allLabels = new Set();
        Object.keys(consumptionByPeriod).forEach(label => allLabels.add(label));
        Object.keys(trendByPeriod).forEach(label => allLabels.add(label));
        Object.keys(budgetByPeriod).forEach(label => allLabels.add(label));
        Object.keys(projectedCostByPeriod).forEach(label => allLabels.add(label));
        const labels = Array.from(allLabels).sort();
        
        // Prepare datasets with aligned data
        const datasets = [];
        
        // Consumption dataset
        if (Object.keys(consumptionByPeriod).length > 0) {
            const consumptionData = labels.map(label => consumptionByPeriod[label] || null);
            datasets.push({
                label: `Consumption (${currency})`,
                data: consumptionData,
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                tension: 0.1,
                fill: true,
                spanGaps: true
            });
        }
        
        // Projected cost dataset (calculated from consumption, not trend)
        if (Object.keys(projectedCostByPeriod).length > 0) {
            const projectedData = labels.map(label => projectedCostByPeriod[label] || null);
            datasets.push({
                label: `Projected Cost (${currency})`,
                data: projectedData,
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                borderDash: [5, 5],
                tension: 0.1,
                fill: false,
                spanGaps: true
            });
        }
        
        // Budget dataset
        if (Object.keys(budgetByPeriod).length > 0) {
            const budgetData = labels.map(label => budgetByPeriod[label] || null);
            datasets.push({
                label: `Budget (${currency})`,
                data: budgetData,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                borderDash: [5, 5],
                tension: 0,
                fill: false,
                spanGaps: true
            });
        }
        
        // Create chart
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Cost Management Overview'
                    },
                    legend: {
                        display: true
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: `Cost (${currency})`
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
     * Aggregate consumption by period
     * 
     * Note: When budget is selected, consumption should be cumulative within budget periods
     * and reset at the start of each budget period.
     * 
     * View modes:
     * - Simple: non-cumulative period costs
     * - Compounded: cumulative costs (within budget periods if budget selected, or across all periods if no budget)
     */
    aggregateConsumptionByPeriod() {
        if (!this.currentConsumptionData || !this.currentConsumptionData.entries) {
            return {};
        }
        
        const aggregated = {};
        const granularity = this.filters.granularity;
        
        // Simple view: always non-cumulative
        if (this.viewMode === 'simple') {
            // Standard aggregation by granularity (non-cumulative)
            this.currentConsumptionData.entries.forEach(entry => {
                const periodKey = this.getPeriodKey(entry.FromDate || entry.from_date, granularity);
                // Price is already calculated (quantity × unit_price) in pre-aggregated data
                const cost = parseFloat(entry.Price || entry.price || 0) || 0;
                
                if (!aggregated[periodKey]) {
                    aggregated[periodKey] = 0;  
                }
                aggregated[periodKey] += cost;
            });
            return aggregated;
        }
        
        // Compounded view: cumulative costs
        if (this.selectedBudget && this.budgetStatus) {
            // Use budget periods for aggregation (cumulative within each budget period)
            const budgetPeriods = this.budgetStatus.periods || [];
            budgetPeriods.forEach(periodInfo => {
                const periodKey = periodInfo.start_date;
                // Use cumulative_spent if available, otherwise use spent
                const cumulativeCost = periodInfo.cumulative_spent !== undefined 
                    ? periodInfo.cumulative_spent 
                    : periodInfo.spent || 0;
                aggregated[periodKey] = cumulativeCost;
            });
        } else {
            // No budget: cumulative across all periods
            // First, aggregate by period (non-cumulative)
            const periodCosts = {};
            this.currentConsumptionData.entries.forEach(entry => {
                const periodKey = this.getPeriodKey(entry.FromDate || entry.from_date, granularity);
                const cost = parseFloat(entry.Price || entry.price || 0) || 0;
                
                if (!periodCosts[periodKey]) {
                    periodCosts[periodKey] = 0;  
                }
                periodCosts[periodKey] += cost;
            });
            
            // Then, calculate cumulative costs
            const sortedPeriods = Object.keys(periodCosts).sort();
            let runningTotal = 0;
            sortedPeriods.forEach(periodKey => {
                runningTotal += periodCosts[periodKey];
                aggregated[periodKey] = runningTotal;
            });
        }
        
        return aggregated;
    },
    
    /**
     * Get period key based on granularity
     */
    getPeriodKey(dateStr, granularity) {
        const date = new Date(dateStr);
        
        if (granularity === 'day') {
            return dateStr;
        } else if (granularity === 'week') {
            // Get monthly week start (1st, 8th, 15th, or 22nd of month)
            const dayOfMonth = date.getDate();
            let weekStartDay;
            if (dayOfMonth <= 7) {
                weekStartDay = 1;
            } else if (dayOfMonth <= 14) {
                weekStartDay = 8;
            } else if (dayOfMonth <= 21) {
                weekStartDay = 15;
            } else {
                weekStartDay = 22;
            }
            const weekStart = new Date(date.getFullYear(), date.getMonth(), weekStartDay);
            return this.formatDate(weekStart);
        } else { // month
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        }
    },
    
    /**
     * Get next period key after a given period key
     * @param {string} periodKey - Current period key
     * @param {string} granularity - Granularity ('day', 'week', 'month')
     * @returns {string} Next period key
     */
    getNextPeriodKey(periodKey, granularity) {
        if (granularity === 'day') {
            const date = new Date(periodKey);
            date.setDate(date.getDate() + 1);
            return this.formatDate(date);
        } else if (granularity === 'week') {
            const date = new Date(periodKey);
            const dayOfMonth = date.getDate();
            let nextWeekStartDay;
            if (dayOfMonth <= 7) {
                nextWeekStartDay = 8;
            } else if (dayOfMonth <= 14) {
                nextWeekStartDay = 15;
            } else if (dayOfMonth <= 21) {
                nextWeekStartDay = 22;
            } else {
                // Move to first day of next month
                date.setMonth(date.getMonth() + 1);
                nextWeekStartDay = 1;
            }
            const nextWeekStart = new Date(date.getFullYear(), date.getMonth(), nextWeekStartDay);
            return this.formatDate(nextWeekStart);
        } else { // month
            // Parse YYYY-MM format
            const [year, month] = periodKey.split('-').map(Number);
            let nextYear = year;
            let nextMonth = month + 1;
            if (nextMonth > 12) {
                nextMonth = 1;
                nextYear += 1;
            }
            return `${nextYear}-${String(nextMonth).padStart(2, '0')}`;
        }
    },
    
    /**
     * Calculate projected cost periods from last consumption value
     * Simplified projection: repeats last period's cost for all projected periods
     * 
     * @param {Object} consumptionByPeriod - Object mapping period keys to consumption values
     * @param {number} growthRate - Growth rate percentage (kept for backward compatibility, but not used in calculation)
     * @param {string} granularity - Granularity ('day', 'week', 'month')
     * @param {string} endDate - End date for projection (YYYY-MM-DD)
     * @returns {Object} Object mapping period keys to projected cost values
     */
    calculateProjectedCost(consumptionByPeriod, growthRate, granularity, endDate) {
        const projected = {};
        
        // Find last consumption period and value
        const consumptionPeriods = Object.keys(consumptionByPeriod).sort();
        if (consumptionPeriods.length === 0) {
            return projected;
        }
        
        const lastPeriodKey = consumptionPeriods[consumptionPeriods.length - 1];
        const lastCost = consumptionByPeriod[lastPeriodKey];
        
        if (!lastCost || lastCost <= 0) {
            return projected;
        }
        
        // Parse end date
        const endDateObj = new Date(endDate);
        endDateObj.setHours(23, 59, 59, 999);
        
        // Generate projected periods starting from last consumption period
        // This ensures the first projection point is plotted at the same position as the last consumption point
        let currentPeriodKey = lastPeriodKey;
        
        while (true) {
            // Check if current period exceeds end date
            let currentPeriodDate;
            if (granularity === 'day') {
                currentPeriodDate = new Date(currentPeriodKey);
            } else if (granularity === 'week') {
                currentPeriodDate = new Date(currentPeriodKey);
            } else { // month
                const [year, month] = currentPeriodKey.split('-').map(Number);
                currentPeriodDate = new Date(year, month - 1, 1);
            }
            
            currentPeriodDate.setHours(0, 0, 0, 0);
            
            if (currentPeriodDate > endDateObj) {
                break;
            }
            
            // Simplified projection: repeat last period's cost for all projected periods
            projected[currentPeriodKey] = Math.max(0, lastCost);
            
            // Move to next period
            currentPeriodKey = this.getNextPeriodKey(currentPeriodKey, granularity);
            
            // Safety limit to prevent infinite loops
            if (Object.keys(projected).length > 1000) {
                break;
            }
        }
        
        return projected;
    },
    
    /**
     * Render data table
     */
    renderTable() {
        const tbody = document.getElementById('cm-table-body');
        if (!tbody) {
            return;
        }
        
        // Combine consumption and budget data by period
        const periodData = {};
        const currency = this.currentConsumptionData?.currency || this.currentTrendData?.currency || 'EUR';
        
        // Add consumption data
        if (this.currentConsumptionData && this.currentConsumptionData.entries) {
            const consumptionByPeriod = this.aggregateConsumptionByPeriod();
            Object.keys(consumptionByPeriod).forEach(period => {
                if (!periodData[period]) {
                    periodData[period] = { period, consumption: 0, budget: 0, remaining: 0, utilization: 0 };
                }
                periodData[period].consumption = consumptionByPeriod[period];
            });
        }
        
        // Add budget data
        if (this.budgetStatus && this.budgetStatus.periods) {
            this.budgetStatus.periods.forEach(periodInfo => {
                const period = periodInfo.start_date;
                if (!periodData[period]) {
                    periodData[period] = { period, consumption: 0, budget: 0, remaining: 0, utilization: 0 };
                }
                periodData[period].budget = periodInfo.budget_amount;
                periodData[period].remaining = periodInfo.remaining;
                periodData[period].utilization = periodInfo.utilization_percent;
            });
        }
        
        // Sort periods
        const sortedPeriods = Object.keys(periodData).sort();
        
        if (sortedPeriods.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-message">${typeof i18n !== 'undefined' ? i18n.t('common.empty') : 'No data available'}</td></tr>`;
            return;
        }
        
        // Render rows
        tbody.innerHTML = sortedPeriods.map(period => {
            const data = periodData[period];
            const utilizationClass = data.utilization >= 90 ? 'negative' : data.utilization >= 75 ? 'warning' : '';
            
            return `
                <tr>
                    <td>${data.period}</td>
                    <td>${currency} ${data.consumption.toFixed(2)}</td>
                    <td>${currency} ${data.budget.toFixed(2)}</td>
                    <td class="${data.remaining < 0 ? 'negative' : ''}">${currency} ${data.remaining.toFixed(2)}</td>
                    <td class="${utilizationClass}">${data.utilization.toFixed(1)}%</td>
                </tr>
            `;
        }).join('');
    },
    
    /**
     * Export data
     */
    async exportData(format) {
        try {
            if (!this.currentConsumptionData) {
                this.showError('Please load data first');
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
            
            if (format === 'csv') {
                const blob = await ConsumptionService.exportConsumption(params, 'csv');
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `cost_management_${this.filters.from_date}_to_${this.filters.to_date}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                const data = await ConsumptionService.exportConsumption(params, 'json');
                const jsonStr = JSON.stringify(data, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `cost_management_${this.filters.from_date}_to_${this.filters.to_date}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Export data error:', error);
            this.showError(error.message || 'Failed to export data');
        }
    }
};

