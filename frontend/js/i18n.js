/**
 * Internationalization module for OSC-FinOps
 * Handles translations for English and French
 */

const i18n = {
    currentLanguage: 'en',
    translations: {
        en: {
            // Login
            'login.title': 'OSC-FinOps',
            'login.subtitle': 'Financial Operations for Outscale',
            'login.accessKey': 'Access Key',
            'login.secretKey': 'Secret Key',
            'login.region': 'Region',
            'login.regionRequired': '*',
            'login.selectRegion': 'Select a region...',
            'login.regionHelp': 'Credentials will be validated for the selected region',
            'login.button': 'Login',
            'login.error': 'Login error',
            
            // Header
            'header.title': 'OSC FinOps Portal',
            'header.logout': 'Logout',
            'header.sessionInfo': 'Region: {region} | Expires: {expires}',
            
            // Tabs
            'tab.quotes': 'Quotes',
            'tab.cost': 'Cost',
            'tab.costManagement': 'Cost Management',
            
            // Quotes
            'quotes.currentQuote': 'Current Quote:',
            'quotes.loading': 'Loading quotes...',
            'quotes.newQuote': 'New Quote',
            'quotes.myQuote': 'My Quote',
            'quotes.active': 'Active',
            'quotes.rename': 'Rename',
            'quotes.delete': 'Delete',
            'quotes.addResource': 'Add Resource to Quote',
            'quotes.region': 'Region',
            'quotes.category': 'Category',
            'quotes.allCategories': 'All Categories',
            'quotes.resource': 'Resource',
            'quotes.selectResource': 'Select a resource...',
            'quotes.quantity': 'Quantity',
            'quotes.unitPrice': 'Unit Price',
            'quotes.addToQuote': 'Add to Quote',
            'quotes.items': 'Quote Items',
            'quotes.resourceName': 'Resource Name',
            'quotes.quantityCol': 'Quantity',
            'quotes.unitPriceCol': 'Unit Price',
            'quotes.actions': 'Actions',
            'quotes.noItems': 'No items in quote. Add resources to get started.',
            'quotes.config': 'Quote Configuration',
            'quotes.duration': 'Duration',
            'quotes.durationUnit': 'Duration Unit',
            'quotes.hours': 'Hours',
            'quotes.days': 'Days',
            'quotes.weeks': 'Weeks',
            'quotes.months': 'Months',
            'quotes.years': 'Years',
            'quotes.globalDiscount': 'Global Discount (%)',
            'quotes.commitment': 'Commitment Period',
            'quotes.commitmentNone': 'None',
            'quotes.commitment1Month': '1 Month',
            'quotes.commitment1Year': '1 Year',
            'quotes.commitment3Years': '3 Years',
            'quotes.summary': 'Cost Summary',
            'quotes.exportCsv': 'Export to CSV',
            'quotes.noSummary': 'Add resources to see cost summary',
            'quotes.newQuoteModal.title': 'Create New Quote',
            'quotes.newQuoteModal.message': 'The current quote will be automatically saved with its current name.',
            'quotes.newQuoteModal.name': 'Quote Name',
            'quotes.newQuoteModal.placeholder': 'Enter quote name',
            'quotes.newQuoteModal.cancel': 'Cancel',
            'quotes.newQuoteModal.create': 'Create',
            'quotes.renameModal.title': 'Rename Quote',
            'quotes.renameModal.message': 'Are you sure you want to rename this quote?',
            'quotes.renameModal.name': 'New Quote Name',
            'quotes.renameModal.placeholder': 'Enter new quote name',
            'quotes.renameModal.rename': 'Rename',
            'quotes.deleteModal.title': 'Delete Quote',
            'quotes.deleteModal.message': 'Are you sure you want to delete "{name}"?',
            'quotes.deleteModal.warning': 'This action cannot be undone.',
            'quotes.deleteModal.delete': 'Delete',
            
            // Cost
            'cost.title': 'Current Cost Evaluation',
            'cost.loading': 'Loading cost data...',
            'cost.filters': 'Filters',
            'cost.useSessionRegion': 'Use Session Region',
            'cost.tagKey': 'Tag Key',
            'cost.tagKeyPlaceholder': 'Enter tag key',
            'cost.tagValue': 'Tag Value',
            'cost.tagValuePlaceholder': 'Enter tag value',
            'cost.includeOos': 'Include OOS Buckets (may take up to 10 minutes)',
            'cost.refresh': 'Refresh Costs',
            'cost.exportCsv': 'Export CSV',
            'cost.exportJson': 'Export JSON',
            'cost.summary': 'Summary',
            'cost.perHour': 'Cost per Hour',
            'cost.perMonth': 'Cost per Month',
            'cost.perYear': 'Cost per Year',
            'cost.resourceCount': 'Resource Count',
            'cost.resources': 'Resource Costs',
            'cost.resourceId': 'Resource ID',
            'cost.resourceType': 'Resource Type',
            'cost.zone': 'Zone',
            'cost.noResources': 'No resources found.',
            'cost.breakdown': 'Breakdown',
            'cost.breakdownByType': 'Breakdown by Resource Type',
            'cost.breakdownByCategory': 'Breakdown by Category',
            'cost.noBreakdown': 'No breakdown data available.',
            
            // Cost Management
            'cm.loading': 'Loading cost management data...',
            'cm.filters': 'Filters',
            'cm.fromDate': 'From Date',
            'cm.toDate': 'To Date',
            'cm.granularity': 'Granularity',
            'cm.granularityDay': 'Day',
            'cm.granularityWeek': 'Week',
            'cm.granularityMonth': 'Month',
            'cm.loadData': 'Load Data',
            'cm.exportCsv': 'Export CSV',
            'cm.exportJson': 'Export JSON',
            'cm.budgets': 'Budgets',
            'cm.createBudget': 'Create Budget',
            'cm.noBudgets': 'No budgets created. Click "Create Budget" to get started.',
            'cm.summary': 'Summary',
            'cm.totalConsumption': 'Total Consumption',
            'cm.totalBudget': 'Total Budget',
            'cm.remainingBudget': 'Remaining Budget',
            'cm.trendDirection': 'Trend Direction',
            'cm.analysis': 'Cost Analysis',
            'cm.periodDetails': 'Period Details',
            'cm.period': 'Period',
            'cm.consumption': 'Consumption',
            'cm.budget': 'Budget',
            'cm.remaining': 'Remaining',
            'cm.utilization': 'Utilization %',
            'cm.noData': 'Load data to see period details',
            'cm.budgetModal.create': 'Create Budget',
            'cm.budgetModal.edit': 'Edit Budget',
            'cm.budgetModal.name': 'Budget Name',
            'cm.budgetModal.namePlaceholder': 'Enter budget name',
            'cm.budgetModal.amount': 'Budget Amount',
            'cm.budgetModal.amountPlaceholder': '0.00',
            'cm.budgetModal.periodType': 'Period Type',
            'cm.budgetModal.monthly': 'Monthly',
            'cm.budgetModal.quarterly': 'Quarterly',
            'cm.budgetModal.yearly': 'Yearly',
            'cm.budgetModal.startDate': 'Start Date',
            'cm.budgetModal.endDate': 'End Date (Optional)',
            'cm.budgetModal.endDateHelp': 'Leave empty for indefinite budget',
            'cm.budgetModal.cancel': 'Cancel',
            'cm.budgetModal.createBtn': 'Create',
            'cm.budgetModal.updateBtn': 'Update',
            'cm.progress.estimated': 'Estimated time remaining: {time}',
            
            // Common
            'common.loading': 'Loading...',
            'common.error': 'Error',
            'common.cancel': 'Cancel',
            'common.save': 'Save',
            'common.delete': 'Delete',
            'common.edit': 'Edit',
            'common.close': 'Close',
            'common.empty': 'No data available',
            'common.select': 'Select...',
        },
        fr: {
            // Login
            'login.title': 'OSC-FinOps',
            'login.subtitle': 'Opérations Financières pour Outscale',
            'login.accessKey': 'Clé d\'accès',
            'login.secretKey': 'Clé secrète',
            'login.region': 'Région',
            'login.regionRequired': '*',
            'login.selectRegion': 'Sélectionner une région...',
            'login.regionHelp': 'Les identifiants seront validés pour la région sélectionnée',
            'login.button': 'Connexion',
            'login.error': 'Erreur de connexion',
            
            // Header
            'header.title': 'Portail OSC FinOps',
            'header.logout': 'Déconnexion',
            'header.sessionInfo': 'Région: {region} | Expire: {expires}',
            
            // Tabs
            'tab.quotes': 'Devis',
            'tab.cost': 'Coût',
            'tab.costManagement': 'Gestion des Coûts',
            
            // Quotes
            'quotes.currentQuote': 'Devis actuel:',
            'quotes.loading': 'Chargement des devis...',
            'quotes.newQuote': 'Nouveau Devis',
            'quotes.myQuote': 'Mon Devis',
            'quotes.active': 'Actif',
            'quotes.rename': 'Renommer',
            'quotes.delete': 'Supprimer',
            'quotes.addResource': 'Ajouter une Ressource au Devis',
            'quotes.region': 'Région',
            'quotes.category': 'Catégorie',
            'quotes.allCategories': 'Toutes les Catégories',
            'quotes.resource': 'Ressource',
            'quotes.selectResource': 'Sélectionner une ressource...',
            'quotes.quantity': 'Quantité',
            'quotes.unitPrice': 'Prix Unitaire',
            'quotes.addToQuote': 'Ajouter au Devis',
            'quotes.items': 'Éléments du Devis',
            'quotes.resourceName': 'Nom de la Ressource',
            'quotes.quantityCol': 'Quantité',
            'quotes.unitPriceCol': 'Prix Unitaire',
            'quotes.actions': 'Actions',
            'quotes.noItems': 'Aucun élément dans le devis. Ajoutez des ressources pour commencer.',
            'quotes.config': 'Configuration du Devis',
            'quotes.duration': 'Durée',
            'quotes.durationUnit': 'Unité de Durée',
            'quotes.hours': 'Heures',
            'quotes.days': 'Jours',
            'quotes.weeks': 'Semaines',
            'quotes.months': 'Mois',
            'quotes.years': 'Années',
            'quotes.globalDiscount': 'Remise Globale (%)',
            'quotes.commitment': 'Période d\'Engagement',
            'quotes.commitmentNone': 'Aucune',
            'quotes.commitment1Month': '1 Mois',
            'quotes.commitment1Year': '1 An',
            'quotes.commitment3Years': '3 Ans',
            'quotes.summary': 'Résumé des Coûts',
            'quotes.exportCsv': 'Exporter en CSV',
            'quotes.noSummary': 'Ajoutez des ressources pour voir le résumé des coûts',
            'quotes.newQuoteModal.title': 'Créer un Nouveau Devis',
            'quotes.newQuoteModal.message': 'Le devis actuel sera automatiquement enregistré avec son nom actuel.',
            'quotes.newQuoteModal.name': 'Nom du Devis',
            'quotes.newQuoteModal.placeholder': 'Entrez le nom du devis',
            'quotes.newQuoteModal.cancel': 'Annuler',
            'quotes.newQuoteModal.create': 'Créer',
            'quotes.renameModal.title': 'Renommer le Devis',
            'quotes.renameModal.message': 'Êtes-vous sûr de vouloir renommer ce devis?',
            'quotes.renameModal.name': 'Nouveau Nom du Devis',
            'quotes.renameModal.placeholder': 'Entrez le nouveau nom du devis',
            'quotes.renameModal.rename': 'Renommer',
            'quotes.deleteModal.title': 'Supprimer le Devis',
            'quotes.deleteModal.message': 'Êtes-vous sûr de vouloir supprimer "{name}"?',
            'quotes.deleteModal.warning': 'Cette action ne peut pas être annulée.',
            'quotes.deleteModal.delete': 'Supprimer',
            
            // Cost
            'cost.title': 'Évaluation des Coûts Actuels',
            'cost.loading': 'Chargement des données de coût...',
            'cost.filters': 'Filtres',
            'cost.useSessionRegion': 'Utiliser la Région de Session',
            'cost.tagKey': 'Clé de Tag',
            'cost.tagKeyPlaceholder': 'Entrez la clé de tag',
            'cost.tagValue': 'Valeur de Tag',
            'cost.tagValuePlaceholder': 'Entrez la valeur de tag',
            'cost.includeOos': 'Inclure les Buckets OOS (peut prendre jusqu\'à 10 minutes)',
            'cost.refresh': 'Actualiser les Coûts',
            'cost.exportCsv': 'Exporter CSV',
            'cost.exportJson': 'Exporter JSON',
            'cost.summary': 'Résumé',
            'cost.perHour': 'Coût par Heure',
            'cost.perMonth': 'Coût par Mois',
            'cost.perYear': 'Coût par Année',
            'cost.resourceCount': 'Nombre de Ressources',
            'cost.resources': 'Coûts des Ressources',
            'cost.resourceId': 'ID de Ressource',
            'cost.resourceType': 'Type de Ressource',
            'cost.zone': 'Zone',
            'cost.noResources': 'Aucune ressource trouvée.',
            'cost.breakdown': 'Répartition',
            'cost.breakdownByType': 'Répartition par Type de Ressource',
            'cost.breakdownByCategory': 'Répartition par Catégorie',
            'cost.noBreakdown': 'Aucune donnée de répartition disponible.',
            
            // Cost Management
            'cm.loading': 'Chargement des données de gestion des coûts...',
            'cm.filters': 'Filtres',
            'cm.fromDate': 'Date de Début',
            'cm.toDate': 'Date de Fin',
            'cm.granularity': 'Granularité',
            'cm.granularityDay': 'Jour',
            'cm.granularityWeek': 'Semaine',
            'cm.granularityMonth': 'Mois',
            'cm.loadData': 'Charger les Données',
            'cm.exportCsv': 'Exporter CSV',
            'cm.exportJson': 'Exporter JSON',
            'cm.budgets': 'Budgets',
            'cm.createBudget': 'Créer un Budget',
            'cm.noBudgets': 'Aucun budget créé. Cliquez sur "Créer un Budget" pour commencer.',
            'cm.summary': 'Résumé',
            'cm.totalConsumption': 'Consommation Totale',
            'cm.totalBudget': 'Budget Total',
            'cm.remainingBudget': 'Budget Restant',
            'cm.trendDirection': 'Direction de la Tendance',
            'cm.analysis': 'Analyse des Coûts',
            'cm.periodDetails': 'Détails de la Période',
            'cm.period': 'Période',
            'cm.consumption': 'Consommation',
            'cm.budget': 'Budget',
            'cm.remaining': 'Restant',
            'cm.utilization': 'Utilisation %',
            'cm.noData': 'Chargez les données pour voir les détails de la période',
            'cm.budgetModal.create': 'Créer un Budget',
            'cm.budgetModal.edit': 'Modifier le Budget',
            'cm.budgetModal.name': 'Nom du Budget',
            'cm.budgetModal.namePlaceholder': 'Entrez le nom du budget',
            'cm.budgetModal.amount': 'Montant du Budget',
            'cm.budgetModal.amountPlaceholder': '0.00',
            'cm.budgetModal.periodType': 'Type de Période',
            'cm.budgetModal.monthly': 'Mensuel',
            'cm.budgetModal.quarterly': 'Trimestriel',
            'cm.budgetModal.yearly': 'Annuel',
            'cm.budgetModal.startDate': 'Date de Début',
            'cm.budgetModal.endDate': 'Date de Fin (Optionnel)',
            'cm.budgetModal.endDateHelp': 'Laisser vide pour un budget indéfini',
            'cm.budgetModal.cancel': 'Annuler',
            'cm.budgetModal.createBtn': 'Créer',
            'cm.budgetModal.updateBtn': 'Mettre à Jour',
            'cm.progress.estimated': 'Temps restant estimé: {time}',
            
            // Common
            'common.loading': 'Chargement...',
            'common.error': 'Erreur',
            'common.cancel': 'Annuler',
            'common.save': 'Enregistrer',
            'common.delete': 'Supprimer',
            'common.edit': 'Modifier',
            'common.close': 'Fermer',
            'common.empty': 'Aucune donnée disponible',
            'common.select': 'Sélectionner...',
        }
    },
    
    /**
     * Initialize i18n system
     */
    init() {
        // Get language preference from localStorage or default to 'en'
        const savedLanguage = localStorage.getItem('osc-finops-language');
        this.currentLanguage = savedLanguage || 'en';
        
        // Set HTML lang attribute
        document.documentElement.setAttribute('lang', this.currentLanguage);
        
        // Translate all elements with data-i18n attribute
        this.translatePage();
        
        // Setup language toggle button
        const langToggle = document.getElementById('language-toggle');
        if (langToggle) {
            langToggle.addEventListener('click', () => this.toggleLanguage());
            this.updateLanguageToggleButton();
        }
    },
    
    /**
     * Get translation for a key
     * Supports placeholders like {name} which will be replaced with values from params
     */
    t(key, params = {}) {
        const translation = this.translations[this.currentLanguage]?.[key] || 
                          this.translations.en[key] || 
                          key;
        
        // Replace placeholders
        return translation.replace(/\{(\w+)\}/g, (match, paramKey) => {
            return params[paramKey] !== undefined ? params[paramKey] : match;
        });
    },
    
    /**
     * Set language
     */
    setLanguage(lang) {
        if (!this.translations[lang]) {
            console.warn(`Language ${lang} not supported, defaulting to English`);
            lang = 'en';
        }
        
        this.currentLanguage = lang;
        localStorage.setItem('osc-finops-language', lang);
        document.documentElement.setAttribute('lang', lang);
        
        // Retranslate page
        this.translatePage();
        this.updateLanguageToggleButton();
    },
    
    /**
     * Toggle language
     */
    toggleLanguage() {
        const newLang = this.currentLanguage === 'en' ? 'fr' : 'en';
        this.setLanguage(newLang);
    },
    
    /**
     * Translate all elements with data-i18n attribute
     */
    translatePage() {
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            // Handle different element types
            if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translation;
            } else if (element.tagName === 'INPUT' && element.placeholder) {
                element.placeholder = translation;
            } else if (element.tagName === 'OPTION') {
                element.textContent = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // Also translate elements with data-i18n-placeholder
        const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
        placeholderElements.forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
        
        // Translate title attribute
        const titleElements = document.querySelectorAll('[data-i18n-title]');
        titleElements.forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });
    },
    
    /**
     * Update language toggle button
     */
    updateLanguageToggleButton() {
        const langToggle = document.getElementById('language-toggle');
        if (langToggle) {
            langToggle.textContent = this.currentLanguage === 'en' ? 'FR' : 'EN';
            langToggle.setAttribute('aria-label', 
                this.currentLanguage === 'en' 
                    ? 'Switch to French' 
                    : 'Switch to English');
        }
    },
    
    /**
     * Get current language
     */
    getLanguage() {
        return this.currentLanguage;
    }
};

// Initialize i18n when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => i18n.init());
} else {
    i18n.init();
}

