/**
 * Authentication module for OSC-FinOps
 * Handles login, logout, and session management
 */

const Auth = {
    sessionId: null,
    sessionData: null,
    sessionCheckInterval: null,
    
    /**
     * Initialize authentication module
     */
    init() {
        this.checkSession();
        this.setupEventListeners();
        // Check session every 5 minutes
        this.sessionCheckInterval = setInterval(() => this.checkSession(), 5 * 60 * 1000);
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        const logoutButton = document.getElementById('logout-button');
        if (logoutButton) {
            logoutButton.addEventListener('click', () => this.handleLogout());
        }
    },
    
    /**
     * Check if user has valid session
     */
    async checkSession() {
        const sessionId = localStorage.getItem('osc_finops_session_id');
        if (!sessionId) {
            this.showLoginScreen();
            return;
        }
        
        try {
            const response = await fetch('/api/auth/session?session_id=' + sessionId);
            
            // Try to parse response as JSON
            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                // If response is not JSON, treat as error
                this.clearSession();
                this.showLoginScreen();
                return;
            }
            
            if (response.ok) {
                this.sessionId = sessionId;
                this.sessionData = data.data;
                this.showMainApp();
                this.updateSessionInfo();
            } else {
                // Session expired or invalid - extract error message if available
                const errorMsg = data.error?.message;
                if (errorMsg) {
                    console.log('Session check failed:', errorMsg);
                }
                this.clearSession();
                this.showLoginScreen();
            }
        } catch (error) {
            console.error('Session check failed:', error);
            // On error, show login screen
            this.clearSession();
            this.showLoginScreen();
        }
    },
    
    /**
     * Handle login form submission
     */
    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const accessKey = formData.get('access_key');
        const secretKey = formData.get('secret_key');
        const region = formData.get('region');
        
        // Validate region
        if (!region) {
            this.showError('Please select a region');
            return;
        }
        
        // Show loading state
        const loginButton = document.getElementById('login-button');
        const loginButtonText = document.getElementById('login-button-text');
        const loginButtonSpinner = document.getElementById('login-button-spinner');
        
        loginButton.disabled = true;
        loginButtonText.style.display = 'none';
        loginButtonSpinner.style.display = 'inline-block';
        this.hideError();
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    access_key: accessKey,
                    secret_key: secretKey,
                    region: region
                })
            });
            
            // Try to parse response as JSON
            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                // If response is not JSON, it's likely a network/server error
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            
            if (response.ok) {
                // Login successful
                this.sessionId = data.data.session_id;
                this.sessionData = data.data;
                localStorage.setItem('osc_finops_session_id', this.sessionId);
                this.showMainApp();
                this.updateSessionInfo();
                form.reset();
            } else {
                // Login failed - extract error message from backend
                const errorMsg = data.error?.message || `Login failed (${response.status})`;
                this.showError(errorMsg);
            }
        } catch (error) {
            console.error('Login error:', error);
            // Extract error message from error object or use generic message
            const errorMsg = error.message || 'Network error. Please try again.';
            this.showError(errorMsg);
        } finally {
            // Reset button state
            loginButton.disabled = false;
            loginButtonText.style.display = 'inline';
            loginButtonSpinner.style.display = 'none';
        }
    },
    
    /**
     * Handle logout
     */
    async handleLogout() {
        if (!this.sessionId) {
            this.clearSession();
            this.showLoginScreen();
            return;
        }
        
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-ID': this.sessionId
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearSession();
            this.showLoginScreen();
        }
    },
    
    /**
     * Clear session data
     */
    clearSession() {
        this.sessionId = null;
        this.sessionData = null;
        localStorage.removeItem('osc_finops_session_id');
        if (this.sessionCheckInterval) {
            clearInterval(this.sessionCheckInterval);
        }
    },
    
    /**
     * Show login screen
     */
    showLoginScreen() {
        document.getElementById('login-screen').style.display = 'flex';
        document.getElementById('main-app').style.display = 'none';
    },
    
    /**
     * Show main application
     */
    showMainApp() {
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('main-app').style.display = 'flex';
    },
    
    /**
     * Update session info display
     */
    updateSessionInfo() {
        const sessionInfo = document.getElementById('session-info');
        if (sessionInfo && this.sessionData) {
            const region = this.sessionData.region || 'Unknown';
            const expiresAt = this.sessionData.expires_at 
                ? new Date(this.sessionData.expires_at).toLocaleTimeString()
                : 'Unknown';
            sessionInfo.textContent = `Region: ${region} | Expires: ${expiresAt}`;
        }
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.getElementById('login-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    },
    
    /**
     * Hide error message
     */
    hideError() {
        const errorDiv = document.getElementById('login-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    },
    
    /**
     * Get current session ID for API calls
     */
    getSessionId() {
        return this.sessionId;
    },
    
    /**
     * Get current session data
     */
    getSessionData() {
        return this.sessionData;
    }
};

// Initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Auth.init());
} else {
    Auth.init();
}

