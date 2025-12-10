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
     * Submit async trend calculation job.
     * 
     * Note: Projection happens automatically when to_date extends beyond yesterday.
     * If budget_id is provided, projected periods are aligned to budget boundaries.
     * 
     * @param {Object} params - Query parameters
     * @param {string} params.from_date - Start date (YYYY-MM-DD)
     * @param {string} params.to_date - End date (YYYY-MM-DD). If after yesterday, projection will occur.
     * @param {string} [params.granularity] - Granularity: 'day', 'week', 'month'
     * @param {string} [params.region] - Filter by region
     * @param {string} [params.resource_type] - Filter by resource type
     * @param {boolean} [params.force_refresh] - Force cache refresh
     * @param {string} [params.budget_id] - Budget ID for period boundary alignment (optional)
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

