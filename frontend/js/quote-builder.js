/**
 * Quote Builder UI module
 */
const QuoteBuilder = {
    currentQuote: null,
    selectedRegion: 'eu-west-2',
    selectedCategory: 'all',
    selectedResource: null,
    catalog: null,
    initialized: false,  // Track initialization state to prevent duplicate event listeners
    
    /**
     * Initialize quote builder
     */
    async init() {
        // Prevent duplicate initialization
        if (this.initialized) {
            return;
        }
        
        // Create or load quote
        await this.loadOrCreateQuote();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load catalog for default region
        await this.loadCatalog(this.selectedRegion);
        
        // Mark as initialized
        this.initialized = true;
    },
    
    /**
     * Load or create a quote
     */
    async loadOrCreateQuote() {
        try {
            // Try to get active quote for user
            const quotes = await QuoteService.listQuotes();
            const activeQuote = quotes.find(q => q.status === 'active');
            
            if (activeQuote) {
                // Load active quote
                this.currentQuote = await QuoteService.getQuote(activeQuote.quote_id);
            } else {
                // Create new quote
                this.currentQuote = await QuoteService.createQuote('My Quote');
            }
            
            QuoteService.currentQuoteId = this.currentQuote.quote_id;
            
            // Update UI
            this.updateQuoteConfigUI();
            this.updateQuoteItems();
            this.updateQuoteSummary();
            this.updateQuoteManagementUI();
            this.updateQuoteSelector();
        } catch (error) {
            console.error('Failed to load/create quote:', error);
            // If auth error, user needs to login
            if (error.message && error.message.includes('Authentication')) {
                this.showError(typeof i18n !== 'undefined' ? i18n.t('common.error') : 'Please login to manage quotes');
            } else {
                this.showError(typeof i18n !== 'undefined' ? i18n.t('common.error') : 'Failed to initialize quote');
            }
        }
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Quote selector
        const quoteSelector = document.getElementById('quote-selector');
        if (quoteSelector) {
            quoteSelector.addEventListener('change', (e) => {
                this.handleQuoteSelectorChange(e.target.value);
            });
        }
        
        // Region selection
        const regionSelect = document.getElementById('quote-region');
        if (regionSelect) {
            regionSelect.addEventListener('change', (e) => {
                this.selectedRegion = e.target.value;
                this.loadCatalog(this.selectedRegion);
            });
        }
        
        // Category selection
        const categorySelect = document.getElementById('quote-category');
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                this.selectedCategory = e.target.value;
                this.updateResourceDropdown();
            });
        }
        
        // Resource selection
        const resourceSelect = document.getElementById('quote-resource');
        if (resourceSelect) {
            resourceSelect.addEventListener('change', (e) => {
                this.onResourceSelected(e.target.value);
            });
        }
        
        // Add resource button
        const addBtn = document.getElementById('add-resource-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.addResourceToQuote());
        }
        
        // Quote configuration
        const durationInput = document.getElementById('quote-duration');
        const durationUnitSelect = document.getElementById('quote-duration-unit');
        const globalDiscountInput = document.getElementById('quote-global-discount');
        const commitmentSelect = document.getElementById('quote-commitment');
        
        if (durationInput) {
            durationInput.addEventListener('change', () => this.updateQuoteConfig());
        }
        if (durationUnitSelect) {
            durationUnitSelect.addEventListener('change', () => this.updateQuoteConfig());
        }
        if (globalDiscountInput) {
            globalDiscountInput.addEventListener('change', () => this.updateQuoteConfig());
        }
        if (commitmentSelect) {
            commitmentSelect.addEventListener('change', () => this.updateQuoteConfig());
        }
        
        // Export button
        const exportBtn = document.getElementById('export-csv-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportToCSV());
        }
    },
    
    /**
     * Load catalog for a region
     */
    async loadCatalog(region) {
        try {
            this.showLoading(true);
            this.catalog = await CatalogService.fetchCatalog(region, this.selectedCategory);
            this.updateResourceDropdown();
            this.showLoading(false);
        } catch (error) {
            console.error('Failed to load catalog:', error);
            this.showError(`Failed to load catalog: ${error.message}`);
            this.showLoading(false);
        }
    },
    
    /**
     * Update resource dropdown
     */
    updateResourceDropdown() {
        const resourceSelect = document.getElementById('quote-resource');
        if (!resourceSelect || !this.catalog) return;
        
        resourceSelect.innerHTML = `<option value="">${typeof i18n !== 'undefined' ? i18n.t('quotes.selectResource') : 'Select a resource...'}</option>`;
        
        const resources = CatalogService.parseResources(this.catalog);
        
        // Filter by category if not 'all'
        const filteredResources = this.selectedCategory === 'all' 
            ? resources 
            : resources.filter(r => (r.Category || '').toLowerCase() === this.selectedCategory.toLowerCase());
        
        filteredResources.forEach(resource => {
            const option = document.createElement('option');
            option.value = resource.Type || resource.type;
            option.textContent = resource.Title || resource.title || resource.Name || resource.name;
            option.dataset.resource = JSON.stringify(resource);
            resourceSelect.appendChild(option);
        });
    },
    
    /**
     * Handle resource selection
     */
    onResourceSelected(resourceType) {
        const resourceSelect = document.getElementById('quote-resource');
        if (!resourceSelect) return;
        
        const selectedOption = resourceSelect.options[resourceSelect.selectedIndex];
        if (!selectedOption || !selectedOption.dataset.resource) {
            this.selectedResource = null;
            this.updateResourceDetails();
            return;
        }
        
        this.selectedResource = JSON.parse(selectedOption.dataset.resource);
        this.updateResourceDetails();
    },
    
    /**
     * Update resource details display
     */
    updateResourceDetails() {
        const unitPriceDisplay = document.getElementById('resource-unit-price');
        const addBtn = document.getElementById('add-resource-btn');
        
        if (this.selectedResource) {
            const price = this.selectedResource.UnitPrice || 0;
            const currency = this.selectedResource.Currency || 'EUR';
            if (unitPriceDisplay) {
                unitPriceDisplay.textContent = `${price.toFixed(4)} ${currency}`;
            }
            if (addBtn) {
                addBtn.disabled = false;
            }
        } else {
            if (unitPriceDisplay) {
                unitPriceDisplay.textContent = '-';
            }
            if (addBtn) {
                addBtn.disabled = true;
            }
        }
    },
    
    /**
     * Add resource to quote
     */
    async addResourceToQuote() {
        if (!this.selectedResource || !this.currentQuote) return;
        
        try {
            const quantityInput = document.getElementById('resource-quantity');
            const quantity = parseFloat(quantityInput?.value || 1);
            
            const item = {
                resource_name: this.selectedResource.Title || this.selectedResource.Name,
                resource_type: this.selectedResource.Type,
                resource_data: this.selectedResource,
                quantity: quantity,
                unit_price: this.selectedResource.UnitPrice || 0,
                region: this.selectedRegion
            };
            
            await QuoteService.addItem(this.currentQuote.quote_id, item);
            
            // Reload quote to get updated calculation
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteItems();
            this.updateQuoteSummary();
            this.updateQuoteManagementUI();
            
            // Reset selection
            document.getElementById('quote-resource').value = '';
            this.selectedResource = null;
            this.updateResourceDetails();
            
        } catch (error) {
            console.error('Failed to add resource:', error);
            this.showError(`Failed to add resource: ${error.message}`);
        }
    },
    
    /**
     * Update quote configuration
     */
    async updateQuoteConfig() {
        if (!this.currentQuote) return;
        
        const duration = parseFloat(document.getElementById('quote-duration')?.value || 1);
        const durationUnit = document.getElementById('quote-duration-unit')?.value || 'months';
        const globalDiscount = parseFloat(document.getElementById('quote-global-discount')?.value || 0);
        const commitment = document.getElementById('quote-commitment')?.value || 'none';
        
        try {
            await QuoteService.updateQuote(this.currentQuote.quote_id, {
                duration,
                duration_unit: durationUnit,
                global_discount_percent: globalDiscount,
                commitment_period: commitment === 'none' ? null : commitment
            });
            
            // Reload quote to get updated calculation
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteItems();
            this.updateQuoteSummary();
        } catch (error) {
            console.error('Failed to update quote config:', error);
            this.showError(`Failed to update configuration: ${error.message}`);
        }
    },
    
    /**
     * Update quote config UI from current quote data
     */
    updateQuoteConfigUI() {
        if (!this.currentQuote) return;
        
        const durationInput = document.getElementById('quote-duration');
        const durationUnitSelect = document.getElementById('quote-duration-unit');
        const globalDiscountInput = document.getElementById('quote-global-discount');
        const commitmentSelect = document.getElementById('quote-commitment');
        
        if (durationInput) durationInput.value = this.currentQuote.duration || 1;
        if (durationUnitSelect) durationUnitSelect.value = this.currentQuote.duration_unit || 'months';
        if (globalDiscountInput) globalDiscountInput.value = this.currentQuote.global_discount_percent || 0;
        if (commitmentSelect) commitmentSelect.value = this.currentQuote.commitment_period || 'none';
    },
    
    /**
     * Update quote items display
     */
    updateQuoteItems() {
        const tbody = document.getElementById('quote-items-body');
        if (!tbody || !this.currentQuote) return;
        
        const items = this.currentQuote.items || [];
        
        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-message">${typeof i18n !== 'undefined' ? i18n.t('quotes.noItems') : 'No items in quote. Add resources to get started.'}</td></tr>`;
            return;
        }
        
        tbody.innerHTML = items.map((item, index) => {
            const resourceName = item.resource_name || 'Unknown';
            const quantity = item.quantity || 0;
            const unitPrice = item.unit_price || 0;
            const region = item.region || '-';
            
            return `
                <tr>
                    <td>${resourceName}</td>
                    <td>${region}</td>
                    <td>${quantity}</td>
                    <td>${unitPrice.toFixed(4)}</td>
                    <td>
                        <button class="btn-remove" onclick="QuoteBuilder.removeItem('${item.id}')" title="Remove item">
                            Remove
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    },
    
    /**
     * Remove item from quote
     */
    async removeItem(itemId) {
        if (!this.currentQuote) return;
        
        try {
            await QuoteService.removeItem(this.currentQuote.quote_id, itemId);
            
            // Reload quote
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteItems();
            this.updateQuoteSummary();
            this.updateQuoteManagementUI();
        } catch (error) {
            console.error('Failed to remove item:', error);
            this.showError(`Failed to remove item: ${error.message}`);
        }
    },
    
    /**
     * Update quote summary
     */
    updateQuoteSummary() {
        if (!this.currentQuote || !this.currentQuote.calculation) return;
        
        const summary = this.currentQuote.calculation.summary || {};
        const summaryDiv = document.getElementById('quote-summary-content');
        
        if (summaryDiv) {
            summaryDiv.innerHTML = `
                <div class="summary-row">
                    <span>Base Total:</span>
                    <span>${summary.base_total?.toFixed(2) || '0.00'} EUR</span>
                </div>
                <div class="summary-row">
                    <span>Commitment Discounts:</span>
                    <span>-${summary.commitment_discounts?.toFixed(2) || '0.00'} EUR</span>
                </div>
                <div class="summary-row">
                    <span>Subtotal:</span>
                    <span>${summary.subtotal?.toFixed(2) || '0.00'} EUR</span>
                </div>
                <div class="summary-row">
                    <span>Global Discount:</span>
                    <span>-${summary.global_discount?.toFixed(2) || '0.00'} EUR</span>
                </div>
                <div class="summary-row summary-total">
                    <span>Total:</span>
                    <span>${summary.total?.toFixed(2) || '0.00'} EUR</span>
                </div>
            `;
        }
        
        // Show export button if there are items
        const exportBtn = document.getElementById('export-csv-btn');
        if (exportBtn) {
            exportBtn.style.display = (this.currentQuote.items || []).length > 0 ? 'inline-block' : 'none';
        }
    },
    
    /**
     * Export quote to CSV
     */
    async exportToCSV() {
        if (!this.currentQuote) return;
        
        try {
            await QuoteService.exportToCSV(this.currentQuote.quote_id);
        } catch (error) {
            console.error('Failed to export:', error);
            this.showError(`Failed to export: ${error.message}`);
        }
    },
    
    /**
     * Show loading state
     */
    showLoading(show) {
        const loadingDiv = document.getElementById('quote-loading');
        if (loadingDiv) {
            loadingDiv.style.display = show ? 'block' : 'none';
        }
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.getElementById('quote-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    },
    
    /**
     * Update quote management UI (save, load, delete, list)
     */
    async updateQuoteManagementUI() {
        // Update quote name display
        const quoteNameDisplay = document.getElementById('quote-name-display');
        if (this.currentQuote) {
            if (quoteNameDisplay) {
                quoteNameDisplay.textContent = this.currentQuote.name || 'Untitled Quote';
            }
        }
        
        // Update active quote indicator
        const activeIndicator = document.getElementById('active-quote-indicator');
        if (activeIndicator && this.currentQuote) {
            if (this.currentQuote.status === 'active') {
                activeIndicator.style.display = 'inline';
                activeIndicator.textContent = typeof i18n !== 'undefined' ? i18n.t('quotes.active') : 'Active';
            } else {
                activeIndicator.style.display = 'none';
            }
        }
        
        // Update quote metadata
        const quoteMetadata = document.getElementById('quote-metadata');
        if (quoteMetadata && this.currentQuote) {
            const created = new Date(this.currentQuote.created_at).toLocaleDateString();
            const updated = new Date(this.currentQuote.updated_at).toLocaleDateString();
            quoteMetadata.innerHTML = `
                <small>Created: ${created} | Updated: ${updated}</small>
            `;
        }
        
        // Update quote selector and list
        await this.updateQuoteSelector();
        await this.updateSavedQuotesList();
    },
    
    /**
     * Update quote selector dropdown
     */
    async updateQuoteSelector() {
        try {
            const quotes = await QuoteService.listQuotes();
            const selector = document.getElementById('quote-selector');
            
            if (!selector) return;
            
            // Clear existing options
            selector.innerHTML = '';
            
            // Add all quotes
            quotes.forEach(quote => {
                const option = document.createElement('option');
                option.value = quote.quote_id;
                if (quote.status === 'active') {
                    option.textContent = `[Active] ${quote.name} (${quote.item_count} items)`;
                    option.selected = true;
                } else {
                    option.textContent = `${quote.name} (${quote.item_count} items)`;
                }
                selector.appendChild(option);
            });
            
            // If no quotes, show message
            if (quotes.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                    option.textContent = typeof i18n !== 'undefined' ? i18n.t('common.empty') : 'No quotes available';
                selector.appendChild(option);
            }
        } catch (error) {
            console.error('Failed to update quote selector:', error);
            const selector = document.getElementById('quote-selector');
            if (selector) {
                selector.innerHTML = `<option value="">${typeof i18n !== 'undefined' ? i18n.t('common.error') : 'Error loading quotes'}</option>`;
            }
        }
    },
    
    /**
     * Handle quote selector change
     */
    async handleQuoteSelectorChange(quoteId) {
        if (!quoteId) return;
        
        // Auto-save current quote before switching
        if (this.currentQuote && this.currentQuote.status === 'active') {
            try {
                await this.saveCurrentQuote();
            } catch (error) {
                console.error('Failed to auto-save quote:', error);
                // Continue anyway
            }
        }
        
        // Load selected quote
        await this.loadSavedQuote(quoteId);
    },
    
    /**
     * Update saved quotes list (shows all quotes with active highlighted)
     * Note: This is no longer displayed in UI, but kept for potential future use
     */
    async updateSavedQuotesList() {
        // Quotes are now managed via the dropdown selector only
        // This method is kept for potential future use but doesn't update any UI element
        return;
    },
    
    /**
     * Save current quote (auto-save, no UI button needed)
     */
    async saveCurrentQuote() {
        if (!this.currentQuote) return;
        
        try {
            await QuoteService.saveQuote(this.currentQuote.quote_id);
            
            // Reload quote to get updated status
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteManagementUI();
        } catch (error) {
            console.error('Failed to save quote:', error);
            // Don't show error for auto-save, just log it
        }
    },
    
    /**
     * Load a saved quote (with auto-save of current quote)
     */
    async loadSavedQuote(quoteId) {
        // Auto-save current quote if it's active and different from the one being loaded
        if (this.currentQuote && this.currentQuote.status === 'active' && this.currentQuote.quote_id !== quoteId) {
            try {
                await this.saveCurrentQuote();
            } catch (error) {
                console.error('Failed to auto-save quote:', error);
                // Continue anyway
            }
        }
        
        try {
            this.currentQuote = await QuoteService.loadQuote(quoteId);
            QuoteService.currentQuoteId = this.currentQuote.quote_id;
            
            this.updateQuoteConfigUI();
            this.updateQuoteItems();
            this.updateQuoteSummary();
            this.updateQuoteManagementUI();
            
            // Don't show success message for auto-loads (e.g., from dropdown)
            // Only show if explicitly called by user action
        } catch (error) {
            console.error('Failed to load quote:', error);
            this.showError(`Failed to load quote: ${error.message}`);
        }
    },
    
    /**
     * Delete a saved quote
     */
    async deleteSavedQuote(quoteId) {
        if (!confirm('Are you sure you want to delete this quote?')) {
            return;
        }
        
        try {
            await QuoteService.deleteQuote(quoteId);
            
            // If deleted quote was current, create new one
            if (this.currentQuote && this.currentQuote.quote_id === quoteId) {
                await this.loadOrCreateQuote();
            } else {
                this.updateSavedQuotesList();
            }
            
            this.showSuccess('Quote deleted successfully');
        } catch (error) {
            console.error('Failed to delete quote:', error);
            this.showError(`Failed to delete quote: ${error.message}`);
        }
    },
    
    /**
     * Show new quote modal
     */
    showNewQuoteModal() {
        const modal = document.getElementById('new-quote-modal');
        const nameInput = document.getElementById('new-quote-name-input');
        if (modal) {
            modal.style.display = 'flex';
            if (nameInput) {
                nameInput.value = '';
                nameInput.focus();
            }
        }
    },
    
    /**
     * Hide new quote modal
     */
    hideNewQuoteModal() {
        const modal = document.getElementById('new-quote-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    },
    
    /**
     * Create new quote from modal (with auto-save)
     */
    async createNewQuoteFromModal() {
        const nameInput = document.getElementById('new-quote-name-input');
        const name = nameInput?.value?.trim() || 'Untitled Quote';
        
        // Auto-save current quote if it's active
        if (this.currentQuote && this.currentQuote.status === 'active') {
            try {
                await this.saveCurrentQuote();
            } catch (error) {
                console.error('Failed to auto-save quote:', error);
                // Continue anyway
            }
        }
        
        try {
            this.currentQuote = await QuoteService.createQuote(name);
            QuoteService.currentQuoteId = this.currentQuote.quote_id;
            
            this.hideNewQuoteModal();
            
            this.updateQuoteConfigUI();
            this.updateQuoteItems();
            this.updateQuoteSummary();
            this.updateQuoteManagementUI();
            
            this.showSuccess('New quote created');
        } catch (error) {
            console.error('Failed to create quote:', error);
            this.showError(`Failed to create quote: ${error.message}`);
        }
    },
    
    /**
     * Create new quote (legacy method, redirects to modal)
     */
    async createNewQuote() {
        this.showNewQuoteModal();
    },
    
    /**
     * Show rename quote modal
     */
    showRenameQuoteModal() {
        if (!this.currentQuote) return;
        
        const modal = document.getElementById('rename-quote-modal');
        const nameInput = document.getElementById('rename-quote-name-input');
        if (modal) {
            modal.style.display = 'flex';
            if (nameInput) {
                nameInput.value = this.currentQuote.name || '';
                nameInput.focus();
            }
        }
    },
    
    /**
     * Hide rename quote modal
     */
    hideRenameQuoteModal() {
        const modal = document.getElementById('rename-quote-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    },
    
    /**
     * Confirm and execute quote rename
     */
    async confirmRenameQuote() {
        if (!this.currentQuote) return;
        
        const nameInput = document.getElementById('rename-quote-name-input');
        if (!nameInput) return;
        
        const newName = nameInput.value.trim();
        if (!newName) {
            this.showError(typeof i18n !== 'undefined' ? i18n.t('common.error') : 'Quote name cannot be empty');
            return;
        }
        
        try {
            await QuoteService.updateQuote(this.currentQuote.quote_id, { name: newName });
            
            // Reload quote
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.hideRenameQuoteModal();
            this.updateQuoteManagementUI();
            this.showSuccess('Quote name updated');
        } catch (error) {
            console.error('Failed to update quote name:', error);
            this.showError(`Failed to update quote name: ${error.message}`);
        }
    },
    
    /**
     * Show delete current quote modal
     */
    showDeleteCurrentQuoteModal() {
        if (!this.currentQuote) return;
        
        const modal = document.getElementById('delete-current-quote-modal');
        const nameDisplay = document.getElementById('delete-quote-name-display');
        if (modal) {
            modal.style.display = 'flex';
            if (nameDisplay) {
                nameDisplay.textContent = this.currentQuote.name || 'Untitled Quote';
            }
        }
    },
    
    /**
     * Hide delete current quote modal
     */
    hideDeleteCurrentQuoteModal() {
        const modal = document.getElementById('delete-current-quote-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    },
    
    /**
     * Confirm and execute delete current quote
     */
    async confirmDeleteCurrentQuote() {
        if (!this.currentQuote) return;
        
        const quoteId = this.currentQuote.quote_id;
        const quoteName = this.currentQuote.name || 'Untitled Quote';
        
        try {
            const result = await QuoteService.deleteQuote(quoteId);
            
            this.hideDeleteCurrentQuoteModal();
            
            // If replacement quote provided, load it
            if (result.replacement_quote) {
                this.currentQuote = await QuoteService.getQuote(result.replacement_quote.quote_id);
                QuoteService.currentQuoteId = this.currentQuote.quote_id;
                
                this.updateQuoteConfigUI();
                this.updateQuoteItems();
                this.updateQuoteSummary();
                this.updateQuoteManagementUI();
                
                this.showSuccess(`Quote "${quoteName}" deleted. Loaded next saved quote.`);
            } else {
                // No saved quotes, create new one
                await this.loadOrCreateQuote();
                this.showSuccess(`Quote "${quoteName}" deleted. Created new quote.`);
            }
        } catch (error) {
            console.error('Failed to delete quote:', error);
            this.showError(`Failed to delete quote: ${error.message}`);
            this.hideDeleteCurrentQuoteModal();
        }
    },
    
    /**
     * Show success message
     */
    showSuccess(message) {
        const errorDiv = document.getElementById('quote-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.className = 'message success';
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
                errorDiv.className = 'error-message';
            }, 3000);
        }
    }
};

