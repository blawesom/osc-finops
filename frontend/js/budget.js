/**
 * Budget service module for OSC-FinOps
 * Handles API communication for budget management
 */

const BudgetService = {
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
     * Create a new budget
     * @param {Object} budgetData - Budget data
     * @param {string} budgetData.name - Budget name
     * @param {number} budgetData.amount - Budget amount per period
     * @param {string} budgetData.period_type - Period type: 'monthly', 'quarterly', or 'yearly'
     * @param {string} budgetData.start_date - Start date (YYYY-MM-DD)
     * @param {string} [budgetData.end_date] - End date (YYYY-MM-DD, optional)
     * @returns {Promise<Object>} Created budget
     */
    async createBudget(budgetData) {
        try {
            const response = await fetch(`${this.API_BASE}/budgets`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(budgetData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to create budget');
            }
        } catch (error) {
            console.error('Create budget error:', error);
            throw error;
        }
    },

    /**
     * List all budgets for the current user
     * @returns {Promise<Object>} List of budgets
     */
    async listBudgets() {
        try {
            const response = await fetch(`${this.API_BASE}/budgets`, {
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
                throw new Error(data.error?.message || 'Failed to list budgets');
            }
        } catch (error) {
            console.error('List budgets error:', error);
            throw error;
        }
    },

    /**
     * Get a budget by ID
     * @param {string} budgetId - Budget ID
     * @returns {Promise<Object>} Budget data
     */
    async getBudget(budgetId) {
        try {
            const response = await fetch(`${this.API_BASE}/budgets/${budgetId}`, {
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
                throw new Error(data.error?.message || 'Failed to get budget');
            }
        } catch (error) {
            console.error('Get budget error:', error);
            throw error;
        }
    },

    /**
     * Update a budget
     * @param {string} budgetId - Budget ID
     * @param {Object} budgetData - Budget data to update (all fields optional)
     * @returns {Promise<Object>} Updated budget
     */
    async updateBudget(budgetId, budgetData) {
        try {
            const response = await fetch(`${this.API_BASE}/budgets/${budgetId}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(budgetData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to update budget');
            }
        } catch (error) {
            console.error('Update budget error:', error);
            throw error;
        }
    },

    /**
     * Delete a budget
     * @param {string} budgetId - Budget ID
     * @returns {Promise<Object>} Success response
     */
    async deleteBudget(budgetId) {
        try {
            const response = await fetch(`${this.API_BASE}/budgets/${budgetId}`, {
                method: 'DELETE',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.success) {
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to delete budget');
            }
        } catch (error) {
            console.error('Delete budget error:', error);
            throw error;
        }
    },

    /**
     * Get budget status (spent vs. budget) for a date range
     * @param {string} budgetId - Budget ID
     * @param {Object} params - Query parameters
     * @param {string} params.from_date - Start date (YYYY-MM-DD)
     * @param {string} params.to_date - End date (YYYY-MM-DD)
     * @param {boolean} [params.force_refresh] - Force cache refresh
     * @returns {Promise<Object>} Budget status data
     */
    async getBudgetStatus(budgetId, params) {
        try {
            const queryParams = new URLSearchParams();
            
            // Required parameters
            if (params.from_date) queryParams.append('from_date', params.from_date);
            if (params.to_date) queryParams.append('to_date', params.to_date);
            
            // Optional parameters
            if (params.force_refresh) queryParams.append('force_refresh', 'true');
            
            const response = await fetch(`${this.API_BASE}/budgets/${budgetId}/status?${queryParams.toString()}`, {
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
                throw new Error(data.error?.message || 'Failed to get budget status');
            }
        } catch (error) {
            console.error('Get budget status error:', error);
            throw error;
        }
    }
};

