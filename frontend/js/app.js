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
        this.setupTabNavigation();
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
        
        // Initialize consumption builder if switching to consumption tab
        // Only init if not already initialized (prevents duplicate event listeners)
        if (tabName === 'consumption' && typeof ConsumptionBuilder !== 'undefined' && !ConsumptionBuilder.initialized) {
            ConsumptionBuilder.init();
        }
    }
};

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}

