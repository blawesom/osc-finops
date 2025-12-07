/**
 * Main application module for OSC-FinOps
 * Handles tab navigation and main app logic
 */

const App = {
    currentTab: 'quotes',
    
    /**
     * Initialize application
     */
    init() {
        this.initTheme();
        this.setupTabNavigation();
    },
    
    /**
     * Initialize theme system
     */
    initTheme() {
        // Get theme preference from localStorage, default to 'light'
        const savedTheme = localStorage.getItem('osc-finops-theme');
        const theme = savedTheme || 'light';
        
        this.setTheme(theme);
        
        // Setup theme toggle button - use event delegation or ensure it's attached when app shows
        this.setupThemeToggle();
    },
    
    /**
     * Set theme
     */
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('osc-finops-theme', theme);
        this.updateThemeToggleButton(theme);
    },
    
    /**
     * Toggle theme
     */
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    },
    
    /**
     * Update theme toggle button text/icon
     */
    updateThemeToggleButton(theme) {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
            themeToggle.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
        }
    },
    
    /**
     * Setup tab navigation
     */
    setupTabNavigation() {
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
    },
    
    /**
     * Setup theme toggle button event listener
     * This can be called multiple times safely
     */
    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            // Remove existing listener if any (to prevent duplicates)
            const newToggle = themeToggle.cloneNode(true);
            themeToggle.parentNode.replaceChild(newToggle, themeToggle);
            
            // Attach event listener
            newToggle.addEventListener('click', () => this.toggleTheme());
            this.updateThemeToggleButton(document.documentElement.getAttribute('data-theme') || 'light');
        }
    },
    
    /**
     * Switch to a different tab
     */
    switchTab(tabName) {
        // Update button states
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-tab') === tabName) {
                btn.classList.add('active');
            }
        });
        
        // Update panel visibility
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.style.display = 'none';
        });
        
        const targetPanel = document.getElementById(`tab-${tabName}`);
        if (targetPanel) {
            targetPanel.style.display = 'block';
        }
        
        this.currentTab = tabName;
        
        // Initialize quote builder if switching to quotes tab
        // Only init if not already initialized (prevents duplicate event listeners)
        if (tabName === 'quotes' && typeof QuoteBuilder !== 'undefined' && !QuoteBuilder.initialized) {
            QuoteBuilder.init();
        }
        
        // Initialize cost builder if switching to cost tab
        if (tabName === 'cost' && typeof CostBuilder !== 'undefined' && !CostBuilder.initialized) {
            CostBuilder.init();
        }
        
        // Initialize cost management builder if switching to cost-management tab
        if (tabName === 'cost-management' && typeof CostManagementBuilder !== 'undefined' && !CostManagementBuilder.initialized) {
            CostManagementBuilder.init();
        }
    }
};

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}

