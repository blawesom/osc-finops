/**
 * Trends API client module.
 */
const TrendsService = {
    API_BASE: '/api',
    currentTrendData: null,

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
     * 
     * Note: New validation and projection rules:
     * - to_date must be in the past by at least 1 granularity period
     * - If from_date is in the past: do not show projected trend
     * - If from_date is in the future: query consumption until last period excluding today, then project trend
     * 
     * @param {Object} params - Query parameters
     * @param {string} params.from_date - Start date (YYYY-MM-DD)
     * @param {string} params.to_date - End date (YYYY-MM-DD) - must be in past
     * @param {string} [params.granularity] - Granularity: 'day', 'week', 'month'
     * @param {string} [params.region] - Filter by region
     * @param {string} [params.resource_type] - Filter by resource type
     * @param {boolean} [params.force_refresh] - Force cache refresh
     * @param {string} [params.project_until] - End date for trend projection
     * @param {string} [params.budget_id] - Budget ID for period boundary alignment
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
            if (params.project_until) queryParams.append('project_until', params.project_until);
            if (params.budget_id) queryParams.append('budget_id', params.budget_id);
            
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

};

