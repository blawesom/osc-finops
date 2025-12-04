/**
 * Cost service for fetching current resource costs
 */
const CostService = {
    API_BASE: '/api',
    
    /**
     * Get session ID from localStorage
     */
    getSessionId() {
        return localStorage.getItem('osc_finops_session_id');
    },
    
    /**
     * Get headers with session ID
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        const sessionId = this.getSessionId();
        if (sessionId) {
            headers['X-Session-ID'] = sessionId;
        }
        return headers;
    },
    
    /**
     * Get current costs
     * @param {Object} params - Query parameters
     * @param {string} params.region - Region name (optional)
     * @param {string} params.tag_key - Tag key to filter by (optional)
     * @param {string} params.tag_value - Tag value to filter by (optional)
     * @param {boolean} params.include_oos - Include OOS buckets (default: false)
     * @param {string} params.format - Response format: 'json', 'human', 'csv', 'ods' (default: 'json')
     * @param {boolean} params.force_refresh - Force refresh cache (default: false)
     * @returns {Promise<Object>} Cost data
     */
    async getCurrentCosts(params = {}) {
        try {
            const queryParams = new URLSearchParams();
            
            // Optional parameters
            if (params.region) queryParams.append('region', params.region);
            if (params.tag_key) queryParams.append('tag_key', params.tag_key);
            if (params.tag_value) queryParams.append('tag_value', params.tag_value);
            if (params.include_oos !== undefined) queryParams.append('include_oos', params.include_oos.toString());
            if (params.format) queryParams.append('format', params.format);
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            
            const response = await fetch(`${this.API_BASE}/cost?${queryParams.toString()}`, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to fetch cost data');
            }
        } catch (error) {
            console.error('Get current costs error:', error);
            throw error;
        }
    },
    
    /**
     * Export cost data
     * @param {Object} params - Same as getCurrentCosts
     * @param {string} format - Export format: 'csv', 'ods', 'json'
     * @returns {Promise<Blob>} Exported file
     */
    async exportCosts(params, format = 'csv') {
        try {
            const queryParams = new URLSearchParams();
            
            // Optional parameters
            if (params.region) queryParams.append('region', params.region);
            if (params.tag_key) queryParams.append('tag_key', params.tag_key);
            if (params.tag_value) queryParams.append('tag_value', params.tag_value);
            if (params.include_oos !== undefined) queryParams.append('include_oos', params.include_oos.toString());
            queryParams.append('format', format);
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            
            const response = await fetch(`${this.API_BASE}/cost/export?${queryParams.toString()}`, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Get blob from response
            const blob = await response.blob();
            
            // Trigger download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || `cost_export.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            return blob;
        } catch (error) {
            console.error('Export costs error:', error);
            throw error;
        }
    }
};

