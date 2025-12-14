/**
 * Quote service for managing quotes via API
 */
const QuoteService = {
    API_BASE: '/api',
    currentQuoteId: null,
    
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
     * Create a new quote
     */
    async createQuote(name = 'Untitled Quote') {
        try {
            const response = await fetch(`${this.API_BASE}/quotes`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ name })
            });
            
            const data = await response.json();
            if (data.success) {
                this.currentQuoteId = data.data.quote_id;
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to create quote');
            }
        } catch (error) {
            console.error('Create quote error:', error);
            throw error;
        }
    },
    
    /**
     * Get quote by ID
     */
    async getQuote(quoteId) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}`, {
                headers: this.getHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to get quote');
            }
        } catch (error) {
            console.error('Get quote error:', error);
            throw error;
        }
    },
    
    /**
     * Update quote configuration
     */
    async updateQuote(quoteId, updates) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(updates)
            });
            
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to update quote');
            }
        } catch (error) {
            console.error('Update quote error:', error);
            throw error;
        }
    },
    
    /**
     * Add item to quote
     */
    async addItem(quoteId, item) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}/items`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(item)
            });
            
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to add item');
            }
        } catch (error) {
            console.error('Add item error:', error);
            throw error;
        }
    },
    
    /**
     * Remove item from quote
     */
    async removeItem(quoteId, itemId) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}/items/${itemId}`, {
                method: 'DELETE',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to remove item');
            }
        } catch (error) {
            console.error('Remove item error:', error);
            throw error;
        }
    },
    
    
    /**
     * Export quote to CSV
     */
    async exportToCSV(quoteId) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}/export/csv`, {
                headers: this.getHeaders()
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `quote_${quoteId.substring(0, 8)}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const data = await response.json();
                throw new Error(data.error?.message || 'Failed to export quote');
            }
        } catch (error) {
            console.error('Export error:', error);
            throw error;
        }
    },
    
    /**
     * List all user's quotes
     */
    async listQuotes() {
        try {
            const response = await fetch(`${this.API_BASE}/quotes`, {
                headers: this.getHeaders()
            });
            const data = await response.json();
            
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to list quotes');
            }
        } catch (error) {
            console.error('List quotes error:', error);
            throw error;
        }
    },
    
    /**
     * Save active quote (changes status to saved)
     */
    async saveQuote(quoteId) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify({ status: 'saved' })
            });
            
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to save quote');
            }
        } catch (error) {
            console.error('Save quote error:', error);
            throw error;
        }
    },
    
    /**
     * Load saved quote (makes it active)
     */
    async loadQuote(quoteId) {
        try {
            // Loading a quote via GET automatically makes it active
            return await this.getQuote(quoteId);
        } catch (error) {
            console.error('Load quote error:', error);
            throw error;
        }
    },
    
    /**
     * Delete quote (active or saved).
     * Returns replacement quote if available (when deleting active quote).
     */
    async deleteQuote(quoteId) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}`, {
                method: 'DELETE',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            if (data.success) {
                return data; // Includes replacement_quote if available
            } else {
                throw new Error(data.error?.message || 'Failed to delete quote');
            }
        } catch (error) {
            console.error('Delete quote error:', error);
            throw error;
        }
    },
    
    /**
     * Create a group for a quote
     */
    async createGroup(quoteId, name) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}/groups`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ name })
            });
            
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to create group');
            }
        } catch (error) {
            console.error('Create group error:', error);
            throw error;
        }
    },
    
    /**
     * Update a group's name
     */
    async updateGroup(quoteId, groupId, name) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}/groups/${groupId}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify({ name })
            });
            
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to update group');
            }
        } catch (error) {
            console.error('Update group error:', error);
            throw error;
        }
    },
    
    /**
     * Delete a group
     */
    async deleteGroup(quoteId, groupId) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}/groups/${groupId}`, {
                method: 'DELETE',
                headers: this.getHeaders()
            });
            
            const data = await response.json();
            if (data.success) {
                return data;
            } else {
                throw new Error(data.error?.message || 'Failed to delete group');
            }
        } catch (error) {
            console.error('Delete group error:', error);
            throw error;
        }
    },
    
    /**
     * Assign an item to a group (or ungroup if groupId is null)
     */
    async assignItemToGroup(quoteId, itemId, groupId) {
        try {
            const response = await fetch(`${this.API_BASE}/quotes/${quoteId}/items/${itemId}/group`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify({ group_id: groupId })
            });
            
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data.error?.message || 'Failed to assign item to group');
            }
        } catch (error) {
            console.error('Assign item to group error:', error);
            throw error;
        }
    }
};

