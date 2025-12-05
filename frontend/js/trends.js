/**
 * Trends API client module.
 */
const TrendsService = {
    API_BASE: '/api',
    currentTrendData: null,
    currentDriftData: null,

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
     * Get trend analysis data.
     * @param {Object} params - Query parameters
     * @param {string} params.from_date - Start date (YYYY-MM-DD)
     * @param {string} params.to_date - End date (YYYY-MM-DD)
     * @param {string} [params.granularity] - Granularity: 'day', 'week', 'month'
     * @param {string} [params.region] - Filter by region
     * @param {string} [params.resource_type] - Filter by resource type
     * @param {boolean} [params.force_refresh] - Force cache refresh
     * @returns {Promise<Object>} Trend data
     */
    async getTrends(params) {
        try {
            const queryParams = new URLSearchParams();
            
            // Required parameters
            if (params.from_date) queryParams.append('from_date', params.from_date);
            if (params.to_date) queryParams.append('to_date', params.to_date);
            
            // Optional parameters
            if (params.granularity) queryParams.append('granularity', params.granularity);
            if (params.region) queryParams.append('region', params.region);
            if (params.resource_type) queryParams.append('resource_type', params.resource_type);
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            
            const response = await fetch(`${this.API_BASE}/trends?${queryParams.toString()}`, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                this.currentTrendData = data.data;
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to fetch trend data');
            }
        } catch (error) {
            console.error('Get trends error:', error);
            throw error;
        }
    },

    /**
     * Get cost drift analysis.
     * @param {Object} params - Query parameters
     * @param {string} params.from_date - Start date (YYYY-MM-DD)
     * @param {string} params.to_date - End date (YYYY-MM-DD)
     * @param {string} [params.region] - Filter by region
     * @param {number} [params.threshold] - Drift threshold percentage (default: 10.0)
     * @param {boolean} [params.force_refresh] - Force cache refresh
     * @returns {Promise<Object>} Drift data
     */
    async getDrift(params) {
        try {
            const queryParams = new URLSearchParams();
            
            // Required parameters
            if (params.from_date) queryParams.append('from_date', params.from_date);
            if (params.to_date) queryParams.append('to_date', params.to_date);
            
            // Optional parameters
            if (params.region) queryParams.append('region', params.region);
            if (params.threshold !== undefined) queryParams.append('threshold', params.threshold);
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            
            const response = await fetch(`${this.API_BASE}/trends/drift?${queryParams.toString()}`, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                this.currentDriftData = data.data;
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to fetch drift data');
            }
        } catch (error) {
            console.error('Get drift error:', error);
            throw error;
        }
    },

    /**
     * Submit async trend calculation job.
     * @param {Object} params - Query parameters (same as getTrends)
     * @returns {Promise<Object>} Job submission response with job_id
     */
    async submitTrendsJob(params) {
        try {
            const response = await fetch(`${this.API_BASE}/trends/async`, {
                method: 'POST',
                headers: {
                    ...this.getHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to submit trend job');
            }
        } catch (error) {
            console.error('Submit trends job error:', error);
            throw error;
        }
    },

    /**
     * Get job status.
     * @param {string} job_id - Job identifier
     * @returns {Promise<Object>} Job status and result
     */
    async getJobStatus(job_id) {
        try {
            const response = await fetch(`${this.API_BASE}/trends/jobs/${job_id}`, {
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
                throw new Error(data.error?.message || 'Failed to get job status');
            }
        } catch (error) {
            console.error('Get job status error:', error);
            throw error;
        }
    },

    /**
     * Poll job status until complete.
     * @param {string} job_id - Job identifier
     * @param {Function} onProgress - Callback for progress updates (progress, estimated_remaining)
     * @param {number} interval - Polling interval in milliseconds (default: 2000)
     * @returns {Promise<Object>} Final job result
     */
    async pollJobStatus(job_id, onProgress = null, interval = 2000) {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await this.getJobStatus(job_id);
                    
                    // Call progress callback if provided
                    if (onProgress && status.progress !== undefined) {
                        onProgress(status.progress, status.estimated_time_remaining);
                    }
                    
                    if (status.status === 'completed') {
                        resolve(status);
                    } else if (status.status === 'failed') {
                        reject(new Error(status.error || 'Job failed'));
                    } else {
                        // Continue polling
                        setTimeout(poll, interval);
                    }
                } catch (error) {
                    reject(error);
                }
            };
            
            poll();
        });
    },

    /**
     * Export trend data.
     * @param {Object} params - Same as getTrends
     * @param {string} format - Export format: 'csv' or 'json'
     * @returns {Promise<Blob|Object>} Exported data
     */
    async exportTrends(params, format = 'csv') {
        try {
            const queryParams = new URLSearchParams();
            
            // Required parameters
            if (params.from_date) queryParams.append('from_date', params.from_date);
            if (params.to_date) queryParams.append('to_date', params.to_date);
            
            // Optional parameters
            if (params.granularity) queryParams.append('granularity', params.granularity);
            if (params.region) queryParams.append('region', params.region);
            if (params.resource_type) queryParams.append('resource_type', params.resource_type);
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            queryParams.append('format', format);
            
            const response = await fetch(`${this.API_BASE}/trends/export?${queryParams.toString()}`, {
                method: 'GET',
                headers: this.getHeaders()
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (format === 'csv') {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `trends_${params.from_date}_to_${params.to_date}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                return blob;
            } else {
                const data = await response.json();
                return data;
            }
        } catch (error) {
            console.error('Export trends error:', error);
            throw error;
        }
    }
};

