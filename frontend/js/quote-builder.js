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
    isLoading: false, // Track loading state for catalog fetching
    groups: [], // Array of group objects: { group_id, name }
    collapsedGroups: {}, // Track which groups are collapsed: { groupId: true/false }
    draggedItemId: null, // Track item being dragged
    vmEntriesByGeneration: {}, // Store VM entries grouped by generation
    ramEntry: null, // Store RAM entry for VM pricing
    currentParameterConfig: null, // Current parameter configuration
    parameterConfig: {}, // Parameter values

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
            
            // Load groups
            this.groups = this.currentQuote.groups || [];
            
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
        // Use debounced update for number inputs to avoid too many API calls while typing
        let configUpdateTimeout = null;
        const debouncedUpdateConfig = () => {
            clearTimeout(configUpdateTimeout);
            configUpdateTimeout = setTimeout(() => {
                this.updateQuoteConfig();
            }, 500); // Wait 500ms after user stops typing
        };
        
        const durationInput = document.getElementById('quote-duration');
        const durationUnitSelect = document.getElementById('quote-duration-unit');
        const globalDiscountInput = document.getElementById('quote-global-discount');
        const commitmentSelect = document.getElementById('quote-commitment');
        
        // For number inputs, listen to both 'input' (for real-time feedback) and 'change' (for final value)
        if (durationInput) {
            durationInput.addEventListener('input', debouncedUpdateConfig);
            durationInput.addEventListener('change', () => this.updateQuoteConfig());
        }
        if (durationUnitSelect) {
            durationUnitSelect.addEventListener('change', () => this.updateQuoteConfig());
        }
        if (globalDiscountInput) {
            globalDiscountInput.addEventListener('input', debouncedUpdateConfig);
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
        
        // New Group button
        const newGroupBtn = document.getElementById('new-group-btn');
        if (newGroupBtn) {
            newGroupBtn.addEventListener('click', () => this.showCreateGroupDialog());
        }
    },
    
    /**
     * Load catalog for a region
     */
    async loadCatalog(region) {
        try {
            this.isLoading = true;
            this.showLoading(true);
            // Don't pass category to API when it's "all" - fetch all entries and filter client-side
            const categoryForApi = this.selectedCategory === 'all' ? null : this.selectedCategory;
            this.catalog = await CatalogService.fetchCatalog(region, categoryForApi);
            
            // Log catalog data for debugging
            console.log('Catalog loaded:', {
                region: region,
                entryCount: this.catalog?.entry_count || 0,
                entries: this.catalog?.entries?.length || 0,
                category: this.selectedCategory
            });
            
            this.updateResourceDropdown();
            this.isLoading = false;
            this.showLoading(false);
        } catch (error) {
            console.error('Failed to load catalog:', error);
            this.showError(`Failed to load catalog: ${error.message}`);
            this.isLoading = false;
            this.showLoading(false);
        }
    },
    
    /**
     * Update resource dropdown with VM synthesis
     */
    updateResourceDropdown() {
        const resourceSelect = document.getElementById('quote-resource');
        if (!resourceSelect || !this.catalog) {
            console.warn('Cannot update resource dropdown: resourceSelect or catalog is missing');
            return;
        }
        
        resourceSelect.innerHTML = `<option value="">${typeof i18n !== 'undefined' ? i18n.t('quotes.selectResource') : 'Select a resource...'}</option>`;
        
        // Check if catalog has entries
        if (!this.catalog.entries || this.catalog.entries.length === 0) {
            console.warn('Catalog has no entries:', this.catalog);
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = 'No resources available for this region';
            emptyOption.disabled = true;
            resourceSelect.appendChild(emptyOption);
            return;
        }
        
        // Get processed resources with VM synthesis
        // Category filtering is done client-side here (not in API call when category is "all")
        const processed = CatalogService.getProcessedResources(this.catalog, this.selectedCategory);
        const resources = processed.resources;
        
        // Log processed resources for debugging
        console.log('Processed resources:', {
            total: resources.length,
            category: this.selectedCategory,
            resources: resources.map(r => ({ Type: r.Type, Title: r.Title, Category: r.Category }))
        });
        
        // Store VM data for later use
        this.vmEntriesByGeneration = processed.vmEntriesByGeneration;
        this.ramEntry = processed.ramEntry;
        
        if (resources.length === 0) {
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = `No resources found in category "${this.selectedCategory}"`;
            emptyOption.disabled = true;
            resourceSelect.appendChild(emptyOption);
            return;
        }
        
        resources.forEach(resource => {
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
            this.updateParameterInputs();
            return;
        }
        
        this.selectedResource = JSON.parse(selectedOption.dataset.resource);
        this.updateResourceDetails();
        this.updateParameterInputs();
    },
    
    /**
     * Update parameter inputs based on selected resource
     */
    updateParameterInputs() {
        const parameterContainer = document.getElementById('parameter-container');
        const helpTextContainer = document.getElementById('parameter-help-text');
        
        if (!parameterContainer) return;
        
        if (!this.selectedResource) {
            parameterContainer.innerHTML = '';
            if (helpTextContainer) helpTextContainer.style.display = 'none';
            return;
        }
        
        // Get parameter configuration for this resource
        const config = RESOURCE_PARAMETER_HELPER.getResourceParameterConfig(this.selectedResource);
        
        // Clear existing parameters
        parameterContainer.innerHTML = '';
        
        // Generate parameter inputs
        config.parameters.forEach((param, index) => {
            const paramDiv = document.createElement('div');
            paramDiv.className = 'parameter-input-group';
            
            const label = document.createElement('label');
            label.setAttribute('for', `param-${param.name}`);
            label.textContent = param.label + (param.unit ? ` (${param.unit})` : '');
            paramDiv.appendChild(label);
            
            let input;
            if (param.type === 'select') {
                input = document.createElement('select');
                input.id = `param-${param.name}`;
                input.className = 'parameter-input';
                
                // Populate options
                if (param.name === 'cpuGeneration') {
                    // Get generations from catalog
                    const catalog = this.catalog;
                    const options = RESOURCE_PARAMETER_HELPER.getGenerationsFromCatalog(catalog);
                    options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.label;
                        if (opt.value === param.value) option.selected = true;
                        input.appendChild(option);
                    });
                } else {
                    param.options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.value || opt;
                        option.textContent = opt.label || opt;
                        input.appendChild(option);
                    });
                }
                
                input.addEventListener('change', () => {
                    this.updateUnitPrice();
                    this.updateAddButton();
                });
            } else {
                input = document.createElement('input');
                input.type = 'number';
                input.id = `param-${param.name}`;
                input.className = 'parameter-input';
                input.min = param.min || 1;
                input.max = param.max || 1000;
                input.step = param.step || 1;
                input.value = param.value || 1;
                input.addEventListener('input', () => {
                    this.updateUnitPrice();
                    this.updateAddButton();
                });
            }
            
            paramDiv.appendChild(input);
            parameterContainer.appendChild(paramDiv);
            
            // Store parameter config for later use
            if (!this.parameterConfig) {
                this.parameterConfig = {};
            }
            this.parameterConfig[param.name] = param;
        });
        
        // Update help text
        if (helpTextContainer && config.parameters.length > 0) {
            const firstParam = config.parameters[0];
            if (firstParam.helpText) {
                helpTextContainer.textContent = firstParam.helpText;
                helpTextContainer.style.display = 'block';
            } else {
                helpTextContainer.style.display = 'none';
            }
        }
        
        // Store config for use when adding to quote
        this.currentParameterConfig = config;
        
        // Update add button state after parameters are set up
        this.updateAddButton();
    },
    
    /**
     * Get parameter values from form
     */
    getParameterValues() {
        const values = {};
        const config = this.currentParameterConfig;
        
        if (!config || !config.parameters) {
            return { quantity: 1 };
        }
        
        config.parameters.forEach(param => {
            const input = document.getElementById(`param-${param.name}`);
            if (input) {
                if (param.type === 'select') {
                    values[param.name] = input.value;
                } else {
                    values[param.name] = parseFloat(input.value) || param.value || 1;
                }
            }
        });
        
        // For backward compatibility, set quantity
        if (values.vCores !== undefined) {
            values.quantity = values.vCores;
        } else if (values.size !== undefined) {
            values.quantity = values.size;
        } else if (values.iops !== undefined) {
            values.quantity = values.iops;
        } else if (values.ram !== undefined) {
            values.quantity = values.ram;
        } else {
            values.quantity = values.quantity || 1;
        }
        
        return values;
    },
    
    /**
     * Update unit price display
     */
    updateUnitPrice() {
        const unitPriceDisplay = document.getElementById('resource-unit-price');
        if (!unitPriceDisplay) return;
        
        if (!this.selectedResource) {
            unitPriceDisplay.textContent = '-';
            return;
        }
        
        const resource = this.selectedResource;
        let price = 0;
        let currency = 'EUR';
        
        // Handle synthetic VM entries
        if (resource.isSynthetic && resource.Type && resource.Type.startsWith('VM:')) {
            const paramValues = this.getParameterValues();
            const cpuPerformance = paramValues.cpuPerformance || 'medium';
            const vCores = parseFloat(paramValues.vCores) || 1;
            const ram = parseFloat(paramValues.ram) || 4;
            
            // Get the correct CustomCore entry based on generation and performance
            const generation = resource.generation;
            const performanceMap = {
                'highest': '1',
                'high': '2',
                'medium': '3'
            };
            const performanceLevel = performanceMap[cpuPerformance] || '3';
            
            // Find the CustomCore entry
            const vmData = this.vmEntriesByGeneration[generation];
            if (vmData && vmData.performanceOptions[cpuPerformance]) {
                const coreEntry = vmData.performanceOptions[cpuPerformance];
                const corePrice = coreEntry.UnitPrice || coreEntry.Price || 0;
                currency = coreEntry.Currency || coreEntry.currency || 'EUR';
                
                // Get RAM price
                const ramPrice = this.ramEntry ? (this.ramEntry.UnitPrice || this.ramEntry.Price || 0) : 0;
                
                // Calculate total price per hour: (vCores × corePrice) + (RAM × ramPrice)
                price = (vCores * corePrice) + (ram * ramPrice);
                
                const displayText = `${price.toFixed(4)} ${currency} / hour (${vCores} vCores + ${ram} GiB RAM)`;
                unitPriceDisplay.textContent = displayText;
                return;
            }
        }
        
        // Extract price from resource for non-synthetic entries
        price = resource.UnitPrice || resource.Price || resource.price || 0;
        currency = resource.Currency || resource.currency || 'EUR';
        
        // Get parameter values to calculate estimated cost
        const paramConfig = this.currentParameterConfig;
        let displayText = '';
        
        if (price > 0) {
            displayText = `${price.toFixed(4)} ${currency}`;
            
            // Add unit information based on resource type
            const flags = resource.Flags || '';
            if (flags.includes('PER_MONTH')) {
                displayText += ' / GiB / month';
            } else if (resource.Type && resource.Type.startsWith('CustomCore:')) {
                displayText += ' / vCore / hour';
            } else if (resource.Type === 'CustomRam') {
                displayText += ' / GiB / hour';
            } else {
                displayText += ' / unit / hour';
            }
        } else {
            displayText = 'Price not available';
        }
        
        unitPriceDisplay.textContent = displayText;
    },
    
    /**
     * Update add button state based on parameter validation
     */
    updateAddButton() {
        const addButton = document.getElementById('add-resource-btn');
        if (!addButton) return;
        
        // Check if resource is selected or if catalog is loading
        if (!this.selectedResource || this.isLoading) {
            addButton.disabled = true;
            return;
        }
        
        // Check if all required parameters are filled
        const config = this.currentParameterConfig;
        if (config && config.parameters) {
            for (const param of config.parameters) {
                if (param.required) {
                    const input = document.getElementById(`param-${param.name}`);
                    if (!input) {
                        addButton.disabled = true;
                        return;
                    }
                    
                    const value = param.type === 'select' ? input.value : parseFloat(input.value);
                    if (value === undefined || value === null || value === '' || 
                        (typeof value === 'number' && (isNaN(value) || value <= 0))) {
                        addButton.disabled = true;
                        return;
                    }
                }
            }
        }
        
        // All checks passed, enable button
        addButton.disabled = false;
    },
    
    /**
     * Update resource details display
     */
    updateResourceDetails() {
        this.updateUnitPrice();
        this.updateAddButton();
    },
    
    /**
     * Add resource to quote
     */
    async addResourceToQuote() {
        if (!this.selectedResource || !this.currentQuote) return;
        
        try {
            // Get parameter values
            const paramValues = this.getParameterValues();
            
            // Validate parameters
            const config = this.currentParameterConfig;
            if (config && config.parameters) {
                for (const param of config.parameters) {
                    if (param.required) {
                        const value = paramValues[param.name];
                        if (value === undefined || value === null || value === '' || (typeof value === 'number' && value <= 0)) {
                            this.showError(`${param.label} is required and must be greater than 0`);
                            return;
                        }
                    }
                }
            }
            
            // Extract resource information
            const resource = this.selectedResource;
            let resourceName = resource.Title || resource.Name || resource.ProductName || 'Unknown Resource';
            let unitPrice = 0;
            let currency = 'EUR';
            let coreResource = null;
            let ramResource = null;
            
            // Handle synthetic VM entries
            if (resource.isSynthetic && resource.Type && resource.Type.startsWith('VM:')) {
                const generation = resource.generation;
                const cpuPerformance = paramValues.cpuPerformance || 'medium';
                const vCores = parseFloat(paramValues.vCores) || 1;
                const ram = parseFloat(paramValues.ram) || 4;
                
                // Get the correct CustomCore entry based on generation and performance
                const vmData = this.vmEntriesByGeneration[generation];
                if (vmData && vmData.performanceOptions[cpuPerformance]) {
                    coreResource = vmData.performanceOptions[cpuPerformance];
                    ramResource = this.ramEntry;
                    
                    const corePrice = coreResource.UnitPrice || coreResource.Price || 0;
                    const ramPrice = ramResource ? (ramResource.UnitPrice || ramResource.Price || 0) : 0;
                    currency = coreResource.Currency || coreResource.currency || 'EUR';
                    
                    // Calculate total unit price: (vCores × corePrice) + (RAM × ramPrice)
                    unitPrice = (vCores * corePrice) + (ram * ramPrice);
                    
                    // Build resource name
                    resourceName = `Virtual Machine ${generation.toUpperCase()} - ${cpuPerformance.charAt(0).toUpperCase() + cpuPerformance.slice(1)} Performance`;
                } else {
                    this.showError('Unable to find pricing for selected VM configuration');
                    return;
                }
            } else {
                // Non-synthetic resources
                unitPrice = resource.UnitPrice || resource.Price || 0;
                currency = resource.Currency || resource.currency || 'EUR';
            }
            
            // For io1 BSU storage, get IOPS pricing
            let iopsUnitPrice = 0;
            if (resource.Type && resource.Type.startsWith('BSU:VolumeUsage:io1') && paramValues.iops) {
                const allResources = CatalogService.parseResources(this.catalog);
                const iopsResource = allResources.find(r => r.Type === 'BSU:VolumeIOPS:io1');
                if (iopsResource) {
                    iopsUnitPrice = iopsResource.UnitPrice || iopsResource.Price || 0;
                }
            }
            
            // Build display name with parameters
            let displayName = resourceName;
            if (resource.isSynthetic && resource.Type && resource.Type.startsWith('VM:')) {
                const cpuPerformance = paramValues.cpuPerformance || 'medium';
                const vCores = paramValues.vCores || 1;
                const ram = paramValues.ram || 4;
                displayName = `${displayName} (${vCores} vCores, ${ram} GiB RAM)`;
            } else {
                if (paramValues.vCores) {
                    displayName = `${displayName} (${paramValues.vCores} vCores)`;
                }
                if (paramValues.ram) {
                    displayName = `${displayName} (${paramValues.ram} GiB RAM)`;
                }
                if (paramValues.size) {
                    displayName = `${displayName} (${paramValues.size} GiB)`;
                }
                if (paramValues.iops) {
                    displayName = `${displayName} (${paramValues.iops} IOPS)`;
                }
            }
            
            const item = {
                resource_name: displayName,
                resource_type: resource.Type,
                resource_data: resource,
                quantity: paramValues.quantity,
                unit_price: unitPrice,
                iops_unit_price: iopsUnitPrice > 0 ? iopsUnitPrice : null,
                region: this.selectedRegion,
                parameters: paramValues
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
            this.currentParameterConfig = null;
            this.updateResourceDetails();
            this.updateParameterInputs();
            
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
            
            // Debug: Log calculation data
            console.log('Quote config updated, calculation:', {
                hasCalculation: !!this.currentQuote.calculation,
                calculation: this.currentQuote.calculation,
                summary: this.currentQuote.calculation?.summary
            });
            
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
     * Update quote items display with groups
     */
    updateQuoteItems() {
        const tbody = document.getElementById('quote-items-body');
        if (!tbody || !this.currentQuote) return;
        
        const items = this.currentQuote.items || [];
        const groups = this.currentQuote.groups || [];
        this.groups = groups;
        
        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="empty-message">${typeof i18n !== 'undefined' ? i18n.t('quotes.noItems') : 'No items in quote. Add resources to get started.'}</td></tr>`;
            return;
        }
        
        const calculation = this.currentQuote.calculation || {};
        const calculatedItems = calculation.items || [];
        
        // Group items by their group_id
        const groupedItems = {};
        const ungroupedItems = [];
        
        calculatedItems.forEach(item => {
            if (item.group_id) {
                if (!groupedItems[item.group_id]) {
                    groupedItems[item.group_id] = [];
                }
                groupedItems[item.group_id].push(item);
            } else {
                ungroupedItems.push(item);
            }
        });
        
        // Sort items within each group alphabetically
        Object.keys(groupedItems).forEach(groupId => {
            groupedItems[groupId].sort((a, b) => {
                const nameA = (a.resource_name || '').toLowerCase();
                const nameB = (b.resource_name || '').toLowerCase();
                return nameA.localeCompare(nameB);
            });
        });
        ungroupedItems.sort((a, b) => {
            const nameA = (a.resource_name || '').toLowerCase();
            const nameB = (b.resource_name || '').toLowerCase();
            return nameA.localeCompare(nameB);
        });
        
        // Build HTML
        let html = '';
        
        // Add "Create Group" drop zone if no groups exist
        if (groups.length === 0 && items.length > 0) {
            html += `
                <tr class="group-header drop-zone create-group-zone" 
                    data-group-id="__create__"
                    ondragover="event.preventDefault(); QuoteBuilder.handleDragOver(event)"
                    ondrop="QuoteBuilder.handleDropOnCreateGroup(event)"
                    ondragenter="QuoteBuilder.handleDragEnter(event)"
                    ondragleave="QuoteBuilder.handleDragLeave(event)">
                    <td colspan="2" style="font-weight: 700; padding-left: 0; color: var(--text-tertiary); font-style: italic;">
                        <span style="cursor: pointer; user-select: none;">
                            + Drop item here to create a new group
                        </span>
                    </td>
                    <td colspan="6"></td>
                </tr>
            `;
        }
        
        // Render all groups (including empty ones), sorted by group name
        const allGroupIds = groups.map(g => g.group_id).sort((a, b) => {
            const groupA = groups.find(g => g.group_id === a);
            const groupB = groups.find(g => g.group_id === b);
            const nameA = (groupA?.name || '').toLowerCase();
            const nameB = (groupB?.name || '').toLowerCase();
            return nameA.localeCompare(nameB);
        });
        
        allGroupIds.forEach(groupId => {
            const group = groups.find(g => g.group_id === groupId);
            const groupName = group ? group.name : 'Unknown Group';
            const itemsInGroup = groupedItems[groupId] || [];
            const isCollapsed = this.collapsedGroups[groupId];
            const groupSubtotal = itemsInGroup.reduce((sum, item) => sum + (item.cost_after_commitment_discount || 0), 0);
            const currency = itemsInGroup.length > 0 ? (itemsInGroup[0]?.resource_data?.Currency || itemsInGroup[0]?.currency || 'EUR') : 'EUR';
            
            // Group header (drop zone)
            html += `
                <tr class="group-header drop-zone" 
                    data-group-id="${groupId}"
                    ondragover="event.preventDefault(); QuoteBuilder.handleDragOver(event)"
                    ondrop="QuoteBuilder.handleDrop(event, '${groupId}')"
                    ondragenter="QuoteBuilder.handleDragEnter(event)"
                    ondragleave="QuoteBuilder.handleDragLeave(event)">
                    <td colspan="2" style="font-weight: 700; padding-left: 0;">
                        <span style="cursor: pointer; user-select: none; margin-right: 4px;" onclick="QuoteBuilder.toggleGroupCollapse('${groupId}')">
                            ${isCollapsed ? '▶' : '▼'} 
                        </span>
                        <span class="group-name-editable" 
                              ondblclick="QuoteBuilder.startEditGroupName('${groupId}')"
                              title="Double-click to edit group name">
                            ${this.escapeHtml(groupName)}
                        </span>
                        <button class="inline-delete-btn" onclick="QuoteBuilder.deleteGroup('${groupId}')" title="Delete group" style="margin-left: 8px; font-size: 0.75rem; padding: 2px 6px;">×</button>
                    </td>
                    <td colspan="5"></td>
                    <td style="font-weight: 700;">${groupSubtotal.toFixed(2)} ${currency}</td>
                    <td></td>
                </tr>
            `;
            
            // Group items (indented)
            if (!isCollapsed) {
                itemsInGroup.forEach(item => {
                    html += this.renderQuoteItemRow(item, true, groupId);
                });
            }
        });
        
        // Render ungrouped items
        if (ungroupedItems.length > 0) {
            const ungroupedSubtotal = ungroupedItems.reduce((sum, item) => sum + (item.cost_after_commitment_discount || 0), 0);
            const currency = ungroupedItems[0]?.resource_data?.Currency || ungroupedItems[0]?.currency || 'EUR';
            const isCollapsed = this.collapsedGroups['ungrouped'];
            
            html += `
                <tr class="group-header drop-zone" 
                    data-group-id="ungrouped"
                    ondragover="event.preventDefault(); QuoteBuilder.handleDragOver(event)"
                    ondrop="QuoteBuilder.handleDrop(event, 'ungrouped')"
                    ondragenter="QuoteBuilder.handleDragEnter(event)"
                    ondragleave="QuoteBuilder.handleDragLeave(event)">
                    <td colspan="2" style="font-weight: 700; padding-left: 0;">
                        <span style="cursor: pointer; user-select: none;" onclick="QuoteBuilder.toggleGroupCollapse('ungrouped')">
                            ${isCollapsed ? '▶' : '▼'} Ungrouped
                        </span>
                    </td>
                    <td colspan="5"></td>
                    <td style="font-weight: 700;">${ungroupedSubtotal.toFixed(2)} ${currency}</td>
                    <td></td>
                </tr>
            `;
            
            if (!isCollapsed) {
                ungroupedItems.forEach(item => {
                    html += this.renderQuoteItemRow(item, false, null);
                });
            }
        }
        
        tbody.innerHTML = html;
    },
    
    /**
     * Render a single quote item row
     */
    renderQuoteItemRow(item, isGrouped, groupId) {
        const currency = item.resource_data?.Currency || item.currency || 'EUR';
        const itemId = item.id;
        const params = item.parameters || {};
        
        // Build parameter display
        let paramDisplay = '';
        if (params.vCores) {
            paramDisplay = `${params.vCores} vCores`;
            if (params.ram) paramDisplay += `, ${params.ram} GiB RAM`;
        } else if (params.size) {
            paramDisplay = `${params.size} GiB`;
            if (params.iops) paramDisplay += `, ${params.iops} IOPS`;
        } else if (params.iops) {
            paramDisplay = `${params.iops} IOPS`;
        } else if (params.ram) {
            paramDisplay = `${params.ram} GiB RAM`;
        } else {
            paramDisplay = item.quantity.toString();
        }
        
        // Get unit price display
        const resourceData = item.resource_data || {};
        const flags = resourceData.Flags || '';
        let unitPriceDisplay = `${item.unit_price?.toFixed(4) || '0.0000'} ${currency}`;
        
        if (flags.includes('PER_MONTH')) {
            unitPriceDisplay += ' / GiB / month';
        } else if (resourceData.Type && resourceData.Type.startsWith('CustomCore:')) {
            unitPriceDisplay += ' / vCore / hour';
        } else if (resourceData.Type === 'CustomRam') {
            unitPriceDisplay += ' / GiB / hour';
        } else {
            unitPriceDisplay += ' / unit / hour';
        }
        
        const indentStyle = isGrouped ? 'padding-left: 24px;' : '';
        const groupName = this.getGroupName(groupId);
        const groupDisplay = groupName === 'Ungrouped' ? '<em style="color: var(--text-tertiary);">Ungrouped</em>' : this.escapeHtml(groupName);
        
        const duration = this.currentQuote.duration || 1;
        const durationUnit = this.currentQuote.duration_unit || 'months';
        const commitmentDiscount = item.commitment_discount_percent || 0;
        const subtotal = item.cost_after_commitment_discount || 0;
        
        return `
            <tr class="quote-item-row draggable-item" 
                draggable="true" 
                data-item-id="${itemId}"
                style="${indentStyle}"
                ondragstart="QuoteBuilder.handleDragStart(event, '${itemId}')"
                ondragend="QuoteBuilder.handleDragEnd(event)">
                <td class="group-display" title="Drag item to group header to assign">
                    ${groupDisplay}
                </td>
                <td>${this.escapeHtml(item.region || '-')}</td>
                <td>${this.escapeHtml(item.resource_name || 'Unknown')}</td>
                <td>${this.escapeHtml(paramDisplay)}</td>
                <td>${unitPriceDisplay}</td>
                <td>${duration} ${durationUnit}</td>
                <td>${commitmentDiscount > 0 ? `${commitmentDiscount}%` : '-'}</td>
                <td>${subtotal.toFixed(2)} ${currency}</td>
                <td>
                    <button class="btn-remove" onclick="QuoteBuilder.removeItem('${itemId}')" title="Remove item">Remove</button>
                </td>
            </tr>
        `;
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    /**
     * Get group name by ID
     */
    getGroupName(groupId) {
        if (!groupId) return 'Ungrouped';
        const group = this.groups.find(g => g.group_id === groupId);
        return group ? group.name : 'Ungrouped';
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
        const summaryDiv = document.getElementById('quote-summary-content');
        
        if (!this.currentQuote) {
            if (summaryDiv) {
                summaryDiv.innerHTML = '<p class="empty-message">No quote loaded</p>';
            }
            return;
        }
        
        // Check if calculation exists
        if (!this.currentQuote.calculation) {
            console.warn('Quote calculation missing:', this.currentQuote);
            if (summaryDiv) {
                summaryDiv.innerHTML = '<p class="empty-message">Calculation not available. Please refresh the quote.</p>';
            }
            return;
        }
        
        const summary = this.currentQuote.calculation.summary || {};
        
        // Debug: Log summary data
        console.log('Updating quote summary:', {
            summary: summary,
            base_total: summary.base_total,
            commitment_discounts: summary.commitment_discounts,
            subtotal: summary.subtotal,
            global_discount: summary.global_discount,
            total: summary.total
        });
        
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
            
            // Load groups
            this.groups = this.currentQuote.groups || [];
            
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
            
            // Load groups
            this.groups = this.currentQuote.groups || [];
            
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
    },
    
    // ========== Group Management Methods ==========
    
    /**
     * Show create group dialog
     */
    showCreateGroupDialog() {
        const groupName = prompt('Enter name for the new group:');
        if (groupName && groupName.trim()) {
            this.createGroup(groupName.trim());
        }
    },
    
    /**
     * Create a new group
     */
    async createGroup(name) {
        if (!this.currentQuote) return;
        
        if (!name || name.trim() === '') {
            this.showError('Group name cannot be empty');
            return;
        }
        
        // Check if group name already exists
        const existingGroup = this.groups.find(g => g.name.toLowerCase() === name.trim().toLowerCase());
        if (existingGroup) {
            this.showError('A group with this name already exists');
            return;
        }
        
        try {
            await QuoteService.createGroup(this.currentQuote.quote_id, name.trim());
            
            // Reload quote to get updated groups
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteItems();
        } catch (error) {
            console.error('Failed to create group:', error);
            this.showError(`Failed to create group: ${error.message}`);
        }
    },
    
    /**
     * Update group name
     */
    async updateGroup(groupId, name) {
        if (!this.currentQuote) return;
        
        if (!name || name.trim() === '') {
            this.showError('Group name cannot be empty');
            return;
        }
        
        // Check if another group has this name
        const existingGroup = this.groups.find(g => g.group_id !== groupId && g.name.toLowerCase() === name.trim().toLowerCase());
        if (existingGroup) {
            this.showError('A group with this name already exists');
            return;
        }
        
        try {
            await QuoteService.updateGroup(this.currentQuote.quote_id, groupId, name.trim());
            
            // Reload quote
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteItems();
        } catch (error) {
            console.error('Failed to update group:', error);
            this.showError(`Failed to update group: ${error.message}`);
        }
    },
    
    /**
     * Delete a group
     */
    async deleteGroup(groupId) {
        if (!this.currentQuote) return;
        
        const group = this.groups.find(g => g.group_id === groupId);
        if (!group) return;
        
        // Count items in this group
        const itemsInGroup = (this.currentQuote.items || []).filter(item => item.group_id === groupId);
        
        // Confirm deletion if group has items
        if (itemsInGroup.length > 0) {
            const confirmMessage = `Delete group "${group.name}"? ${itemsInGroup.length} item(s) will be moved to Ungrouped.`;
            if (!confirm(confirmMessage)) {
                return;
            }
        }
        
        try {
            await QuoteService.deleteGroup(this.currentQuote.quote_id, groupId);
            
            // Reload quote
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteItems();
        } catch (error) {
            console.error('Failed to delete group:', error);
            this.showError(`Failed to delete group: ${error.message}`);
        }
    },
    
    /**
     * Toggle group collapse
     */
    toggleGroupCollapse(groupId) {
        if (this.collapsedGroups[groupId]) {
            delete this.collapsedGroups[groupId];
        } else {
            this.collapsedGroups[groupId] = true;
        }
        this.updateQuoteItems();
    },
    
    /**
     * Start editing group name inline
     */
    startEditGroupName(groupId) {
        const group = this.groups.find(g => g.group_id === groupId);
        if (!group) return;
        
        const headerRow = document.querySelector(`tr.group-header[data-group-id="${groupId}"]`);
        if (!headerRow) return;
        
        const nameSpan = headerRow.querySelector('.group-name-editable');
        if (!nameSpan) return;
        
        const currentName = group.name;
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentName;
        input.style.cssText = 'font-weight: 700; border: 1px solid var(--accent-color); padding: 2px 4px; border-radius: 3px; background-color: var(--bg-primary); color: var(--text-primary); font-size: inherit;';
        input.style.width = (nameSpan.offsetWidth || 100) + 'px';
        
        const finishEdit = () => {
            const newName = input.value.trim();
            if (newName && newName !== currentName) {
                this.updateGroup(groupId, newName);
            } else {
                nameSpan.textContent = currentName;
            }
            if (input.parentNode === nameSpan) {
                input.remove();
            }
        };
        
        const cancelEdit = () => {
            nameSpan.textContent = currentName;
            if (input.parentNode === nameSpan) {
                input.remove();
            }
        };
        
        input.addEventListener('blur', finishEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                finishEdit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelEdit();
            }
        });
        
        const originalContent = nameSpan.textContent;
        nameSpan.textContent = '';
        nameSpan.appendChild(input);
        input.focus();
        input.select();
        
        input.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    },
    
    // ========== Drag-and-Drop Methods ==========
    
    /**
     * Handle drag start
     */
    handleDragStart(event, itemId) {
        event.dataTransfer.setData('text/plain', itemId);
        event.dataTransfer.effectAllowed = 'move';
        event.currentTarget.classList.add('dragging');
        this.draggedItemId = itemId;
    },
    
    /**
     * Handle drag end
     */
    handleDragEnd(event) {
        event.currentTarget.classList.remove('dragging');
        document.querySelectorAll('.drop-zone').forEach(zone => {
            zone.classList.remove('drag-over');
        });
        this.draggedItemId = null;
    },
    
    /**
     * Handle drag over
     */
    handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    },
    
    /**
     * Handle drag enter
     */
    handleDragEnter(event) {
        event.preventDefault();
        if (event.currentTarget.classList.contains('drop-zone')) {
            event.currentTarget.classList.add('drag-over');
        }
    },
    
    /**
     * Handle drag leave
     */
    handleDragLeave(event) {
        if (event.currentTarget.classList.contains('drop-zone')) {
            event.currentTarget.classList.remove('drag-over');
        }
    },
    
    /**
     * Handle drop on group
     */
    async handleDrop(event, targetGroupId) {
        event.preventDefault();
        event.currentTarget.classList.remove('drag-over');
        
        const itemId = event.dataTransfer.getData('text/plain') || this.draggedItemId;
        if (!itemId || !this.currentQuote) return;
        
        // Handle inline group creation if dropping on a new group name
        if (targetGroupId && targetGroupId !== 'ungrouped') {
            const group = this.groups.find(g => g.group_id === targetGroupId);
            if (!group) {
                // Group doesn't exist, prompt to create
                const groupName = prompt('Enter group name (or cancel to use existing groups):');
                if (groupName && groupName.trim()) {
                    await this.createGroup(groupName.trim());
                    // After creating, assign item to the new group
                    const newGroup = this.currentQuote.groups.find(g => g.name === groupName.trim());
                    if (newGroup) {
                        await this.assignItemToGroup(itemId, newGroup.group_id);
                    }
                    return;
                }
                return;
            }
        }
        
        // Assign item to target group (or ungroup if targetGroupId is 'ungrouped')
        const finalGroupId = targetGroupId === 'ungrouped' ? null : targetGroupId;
        await this.assignItemToGroup(itemId, finalGroupId);
    },
    
    /**
     * Handle drop on create group zone
     */
    async handleDropOnCreateGroup(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('drag-over');
        
        const itemId = event.dataTransfer.getData('text/plain') || this.draggedItemId;
        if (!itemId) return;
        
        const groupName = prompt('Enter name for the new group:');
        if (groupName && groupName.trim()) {
            await this.createGroup(groupName.trim());
            // After creating, assign item to the new group
            const newGroup = this.currentQuote.groups.find(g => g.name === groupName.trim());
            if (newGroup) {
                await this.assignItemToGroup(itemId, newGroup.group_id);
            }
        }
    },
    
    /**
     * Assign item to group
     */
    async assignItemToGroup(itemId, groupId) {
        if (!this.currentQuote) return;
        
        try {
            await QuoteService.assignItemToGroup(this.currentQuote.quote_id, itemId, groupId);
            
            // Reload quote
            this.currentQuote = await QuoteService.getQuote(this.currentQuote.quote_id);
            
            this.updateQuoteItems();
        } catch (error) {
            console.error('Failed to assign item to group:', error);
            this.showError(`Failed to assign item to group: ${error.message}`);
        }
    }
};

// Make QuoteBuilder globally accessible for inline onclick handlers
window.QuoteBuilder = QuoteBuilder;

