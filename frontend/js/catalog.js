/**
 * Catalog service for fetching and managing Outscale catalogs
 */
const CatalogService = {
    API_BASE: '/api',
    
    /**
     * Fetch catalog for a region
     */
    async fetchCatalog(region, category = null, forceRefresh = false) {
        try {
            let url = `${this.API_BASE}/catalog?region=${encodeURIComponent(region)}`;
            if (category) {
                url += `&category=${encodeURIComponent(category)}`;
            }
            if (forceRefresh) {
                url += `&force_refresh=true`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to fetch catalog');
            }
        } catch (error) {
            console.error('Catalog fetch error:', error);
            throw error;
        }
    },
    
    
    /**
     * Parse catalog entries into a more usable format
     */
    parseResources(catalog) {
        const entries = catalog.entries || [];
        return entries.map(entry => ({
            Type: entry.Type || entry.type,
            Title: entry.Title || entry.title || entry.Name || entry.name,
            Category: entry.Category || entry.category,
            UnitPrice: parseFloat(entry.UnitPrice || entry.unitPrice || 0),
            Currency: entry.Currency || entry.currency || 'EUR',
            Flags: entry.Flags || entry.flags || '',
            ...entry
        }));
    },
    
    /**
     * Synthesize VM entries from CustomCore and CustomRam entries
     * Groups CustomCore entries by generation and creates synthetic VM entries
     */
    synthesizeVmEntries(resources) {
        const vmEntriesByGeneration = {};
        const nonVmResources = [];
        let ramEntry = null;
        
        resources.forEach(resource => {
            if (resource.Type && resource.Type.startsWith('CustomCore:')) {
                const generationMatch = resource.Type.match(/CustomCore:(v\d+)-p(\d+)/);
                if (generationMatch) {
                    const generation = generationMatch[1];
                    const performanceLevel = generationMatch[2];
                    
                    if (!vmEntriesByGeneration[generation]) {
                        vmEntriesByGeneration[generation] = {
                            generation: generation,
                            performanceOptions: {}
                        };
                    }
                    
                    // Map performance level: p1=highest, p2=high, p3=medium
                    const performanceMap = {
                        '1': 'highest',
                        '2': 'high',
                        '3': 'medium'
                    };
                    const performanceName = performanceMap[performanceLevel] || 'medium';
                    
                    vmEntriesByGeneration[generation].performanceOptions[performanceName] = resource;
                }
            } else if (resource.Type === 'CustomRam') {
                ramEntry = resource;
            } else {
                // Keep non-VM resources (but filter out GPU allocate and BSU IOPS entries)
                if (resource.Type && resource.Type.startsWith('Gpu:allocate:')) {
                    // Hide allocate GPU entries (same price as attach)
                    return;
                }
                if (resource.Type && resource.Type.startsWith('BSU:VolumeIOPS:')) {
                    // Hide IOPS entries (handled as parameters for io1 volumes)
                    return;
                }
                nonVmResources.push(resource);
            }
        });
        
        // Create synthetic VM entries for each generation
        const syntheticVmEntries = Object.keys(vmEntriesByGeneration).map(generation => {
            const vmData = vmEntriesByGeneration[generation];
            // Use the category from the first CustomCore entry to match backend format
            const firstCoreEntry = Object.values(vmData.performanceOptions)[0];
            const category = firstCoreEntry?.Category || 'Compute'; // Default to 'Compute' if not found
            return {
                Type: `VM:${generation}`,
                Title: `Virtual Machine CPU Tina ${generation.toUpperCase()}`,
                Category: category, // Use actual category from catalog (e.g., 'Compute' not 'compute')
                isSynthetic: true,
                generation: generation,
                performanceOptions: vmData.performanceOptions,
                // Use first available performance option as default for pricing display
                UnitPrice: Object.values(vmData.performanceOptions)[0]?.UnitPrice || 0,
                Currency: Object.values(vmData.performanceOptions)[0]?.Currency || 'EUR',
                ramEntry: ramEntry
            };
        });
        
        // Combine synthetic VM entries with other resources
        return {
            resources: [...syntheticVmEntries, ...nonVmResources],
            vmEntriesByGeneration: vmEntriesByGeneration,
            ramEntry: ramEntry
        };
    },
    
    /**
     * Get parsed and synthesized resources for a catalog
     */
    getProcessedResources(catalog, category = null) {
        // Parse resources
        let resources = this.parseResources(catalog);
        
        // Filter by category if specified (case-insensitive comparison)
        if (category && category !== 'all') {
            const categoryLower = category.toLowerCase();
            resources = resources.filter(r => {
                const resourceCategory = (r.Category || '').toLowerCase();
                return resourceCategory === categoryLower;
            });
        }
        
        // Synthesize VM entries (this happens before final filtering)
        const processed = this.synthesizeVmEntries(resources);
        
        // Apply category filter to synthesized resources if needed
        if (category && category !== 'all') {
            const categoryLower = category.toLowerCase();
            processed.resources = processed.resources.filter(r => {
                const resourceCategory = (r.Category || '').toLowerCase();
                return resourceCategory === categoryLower;
            });
        }
        
        // Sort alphabetically
        processed.resources.sort((a, b) => {
            const nameA = (a.Title || a.Name || a.name || '').toLowerCase();
            const nameB = (b.Title || b.Name || b.name || '').toLowerCase();
            return nameA.localeCompare(nameB);
        });
        
        return processed;
    }
};

// Make CatalogService globally accessible for debugging
window.CatalogService = CatalogService;

