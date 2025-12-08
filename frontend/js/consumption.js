/**
 * Consumption service module for OSC-FinOps
 * Handles API communication for consumption history
 */

const ConsumptionService = {
    API_BASE: '/api',
    currentData: null,

    /**
     * Get session ID from localStorage
     */
    getSessionId() {
        return localStorage.getItem('osc_finops_session_id');
    },

    /**
     * Build headers with session ID
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
     * Get consumption data
     * 
     * Note: ReadAccountConsumption returns pre-aggregated data:
     * - Data separated by type (each resource/service type has its own entry)
     * - Consolidated quantity over the queried period
     * - Unit price (does not vary with period)
     * - Total cost per type already calculated (quantity × unit_price) in Price field
     * 
     * @param {Object} params - Query parameters
     * @param {string} params.from_date - Start date (YYYY-MM-DD) - inclusive
     * @param {string} params.to_date - End date (YYYY-MM-DD) - exclusive
     * @param {string} [params.granularity] - Granularity: 'day', 'week', 'month'
     * @param {string} [params.region] - Filter by region
     * @param {string} [params.service] - Filter by service
     * @param {string} [params.resource_type] - Filter by resource type
     * @param {string} [params.aggregate_by] - Aggregate by: 'resource_type', 'region', 'tag'
     * @param {boolean} [params.force_refresh] - Force cache refresh
     * @returns {Promise<Object>} Consumption data with pre-aggregated entries
     */
    async getConsumption(params) {
        try {
            const queryParams = new URLSearchParams();
            
            // Required parameters
            if (params.from_date) queryParams.append('from_date', params.from_date);
            if (params.to_date) queryParams.append('to_date', params.to_date);
            
            // Optional parameters
            if (params.granularity) queryParams.append('granularity', params.granularity);
            if (params.region) queryParams.append('region', params.region);
            if (params.service) queryParams.append('service', params.service);
            if (params.resource_type) queryParams.append('resource_type', params.resource_type);
            if (params.aggregate_by) queryParams.append('aggregate_by', params.aggregate_by);
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            
            const response = await fetch(`${this.API_BASE}/consumption?${queryParams.toString()}`, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                this.currentData = data.data;
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to fetch consumption data');
            }
        } catch (error) {
            console.error('Get consumption error:', error);
            throw error;
        }
    },

    /**
     * Export consumption data
     * @param {Object} params - Same as getConsumption
     * @param {string} format - Export format: 'csv' or 'json'
     * @returns {Promise<Blob|Object>} Exported data
     */
    async exportConsumption(params, format = 'json') {
        try {
            const queryParams = new URLSearchParams();
            
            // Required parameters
            if (params.from_date) queryParams.append('from_date', params.from_date);
            if (params.to_date) queryParams.append('to_date', params.to_date);
            
            // Optional parameters
            if (params.granularity) queryParams.append('granularity', params.granularity);
            if (params.region) queryParams.append('region', params.region);
            if (params.service) queryParams.append('service', params.service);
            if (params.resource_type) queryParams.append('resource_type', params.resource_type);
            if (params.aggregate_by) queryParams.append('aggregate_by', params.aggregate_by);
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            
            queryParams.append('format', format);
            
            const response = await fetch(`${this.API_BASE}/consumption/export?${queryParams.toString()}`, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (format === 'csv') {
                // Return blob for CSV download
                const blob = await response.blob();
                return blob;
            } else {
                // Return JSON
                const data = await response.json();
                return data;
            }
        } catch (error) {
            console.error('Export consumption error:', error);
            throw error;
        }
    },

};

