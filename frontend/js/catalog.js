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
     * Get available categories for a region
     */
    async getCategories(region) {
        try {
            const response = await fetch(`${this.API_BASE}/catalog/categories?region=${encodeURIComponent(region)}`);
            const data = await response.json();
            
            if (data.success) {
                return data.data.categories;
            } else {
                throw new Error(data.error?.message || 'Failed to fetch categories');
            }
        } catch (error) {
            console.error('Categories fetch error:', error);
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
    }
};

