# OSC-FinOps Product Requirement Document (PRD)

## Document Information

- **Product Name**: OSC-FinOps
- **Version**: 1.0
- **Date**: 2024
- **Status**: In Development
- **Target Release**: TBD

## 1. Executive Summary

OSC-FinOps is a comprehensive FinOps service designed for Outscale customers, providing cost visibility, budgeting, forecasting, and optimization recommendations. The service enables project managers, CFOs, accountants, and customer teams to effectively manage cloud costs through quote building, consumption tracking, cost evaluation, trend analysis, and budget management.

### 1.1 Problem Statement

Outscale customers need a unified tool to:
- Estimate costs for planned infrastructure deployments
- Track current and historical resource costs
- Manage budgets and receive spending alerts
- Analyze cost trends and identify optimization opportunities
- Allocate costs by projects, departments, or tags

Currently, customers use multiple tools (cockpit-ext, osc-cost, osc-draft-invoicing) separately, which creates workflow friction and lacks integration.

### 1.2 Solution Overview

OSC-FinOps consolidates functionality from existing tools into a single, integrated service with:
- RESTful Python backend for API integration
- Simple HTML/CSS/JavaScript frontend
- Session-based authentication
- Multi-account and multi-region support
- Real-time cost calculations
- Budget management and alerts

### 1.3 Success Metrics

- All functional requirements (FR-1.1 through FR-5.2) implemented
- All non-functional requirements (NFR-1.1 through NFR-4.2, NFR-3.3) met
- Performance targets achieved (response times < 1-10 seconds)
- Security requirements satisfied
- User acceptance testing passed

## 2. User Personas

### 2.1 Project Manager

**Profile**:
- Manages multiple cloud projects
- Needs cost visibility per project
- Tracks budgets and spending
- Requires resource optimization insights

**Goals**:
- Create cost estimates for new projects
- Track project spending against budgets
- Identify cost optimization opportunities
- Generate reports for stakeholders

**Pain Points**:
- Lack of project-level cost visibility
- Difficulty tracking budgets across projects
- No integrated view of costs

**User Stories**:
- As a project manager, I want to create quotes for planned infrastructure so I can estimate project costs
- As a project manager, I want to track costs by project tags so I can monitor project spending
- As a project manager, I want to set budgets per project so I can control spending
- As a project manager, I want to receive budget alerts so I can take action before exceeding budgets
- As a project manager, I want to save quotes so I can work on multiple estimates
- As a project manager, I want to load saved quotes so I can continue editing them
- As a project manager, I want to delete quotes so I can clean up outdated estimates
- As a project manager, I want to see my saved quotes so I can manage my estimates

### 2.2 CFO

**Profile**:
- Oversees financial planning and budgeting
- Needs high-level cost overview
- Requires trend analysis
- Monitors budget compliance

**Goals**:
- View high-level cost overview
- Analyze cost trends over time
- Monitor budget compliance
- Generate financial reports

**Pain Points**:
- Lack of high-level cost visibility
- Difficulty identifying cost trends
- No automated budget compliance monitoring

**User Stories**:
- As a CFO, I want to view total costs across all accounts so I can understand overall spending
- As a CFO, I want to analyze cost trends so I can forecast future spending
- As a CFO, I want to see budget compliance reports so I can monitor adherence to budgets
- As a CFO, I want to export cost data so I can include it in financial reports

### 2.3 Accountant

**Profile**:
- Handles detailed cost accounting
- Needs detailed consumption history
- Performs invoice reconciliation
- Allocates costs to cost centers

**Goals**:
- Access detailed consumption history
- Reconcile invoices with consumption data
- Allocate costs by tags, projects, or departments
- Export data for accounting systems

**Pain Points**:
- Lack of detailed consumption data
- Difficulty reconciling invoices
- Manual cost allocation processes

**User Stories**:
- As an accountant, I want to view detailed consumption history so I can reconcile invoices
- As an accountant, I want to filter consumption by date range so I can match billing periods
- As an accountant, I want to allocate costs by tags so I can assign costs to cost centers
- As an accountant, I want to export consumption data so I can import it into accounting systems

### 2.4 Outscale Customer Team

**Profile**:
- Provides customer support
- Analyzes account-level costs
- Provides optimization recommendations
- Monitors customer spending

**Goals**:
- Analyze account-level costs
- Identify cost optimization opportunities
- Provide recommendations to customers
- Monitor customer spending patterns

**Pain Points**:
- Lack of integrated cost analysis tools
- Difficulty identifying optimization opportunities
- No automated cost drift detection

**User Stories**:
- As a customer team member, I want to evaluate current costs so I can understand customer spending
- As a customer team member, I want to analyze cost drift so I can identify optimization opportunities
- As a customer team member, I want to view cost trends so I can provide recommendations
- As a customer team member, I want to compare estimated vs. actual costs so I can identify discrepancies

## 3. Feature Specifications

### 3.1 Quote Building (FR-1.1, FR-1.2)

#### Feature Description
Enable users to build cost estimates (quotes) for planned infrastructure deployments by selecting resources from catalogs, configuring parameters, and applying discounts.

#### User Stories
- **US-1.1**: As a project manager, I want to select resources from catalogs so I can build cost estimates
- **US-1.2**: As a project manager, I want to configure resource parameters (quantity, size) so I can accurately estimate costs
- **US-1.3**: As a project manager, I want to apply commitment discounts so I can see cost savings
- **US-1.4**: As a project manager, I want to apply global discounts so I can account for negotiated rates
- **US-1.5**: As a project manager, I want to export quotes so I can share them with stakeholders
- **US-1.6**: As a project manager, I want to save quotes so I can work on them later
- **US-1.7**: As a project manager, I want to load saved quotes so I can continue working on them
- **US-1.8**: As a project manager, I want to delete quotes so I can remove outdated estimates
- **US-1.9**: As a project manager, I want to see my saved quotes list so I can manage multiple estimates

#### Acceptance Criteria
- [ ] **ReadPublicCatalog API works without authentication** - catalog can be accessed without user credentials
- [ ] Users can select resources from multiple region catalogs (cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2)
- [ ] Users can filter resources by category (Compute, Storage, Network, Licence)
- [ ] Users can configure resource parameters (quantity, size, duration)
- [ ] System calculates costs correctly (quantity × unit_price × duration)
- [ ] System applies commitment discounts (1 month: 30%, 1 year: 40%, 3 years: 50% for compute)
- [ ] System applies global discount percentage
- [ ] System handles monthly and hourly pricing models
- [ ] Users can group resources in quotes
- [ ] Users can export quotes to CSV format
- [ ] Users can export quotes to PDF format (optional for MVP)
- [ ] Users can save and load quote templates
- [ ] Catalog data is cached (24h TTL)
- [ ] Catalog can be refreshed on demand
- [ ] Users can create a new quote (becomes active)
- [ ] Only one active quote per user at a time
- [ ] Users can save active quotes (moves to saved state)
- [ ] Users can load saved quotes (becomes active)
- [ ] Users can delete saved quotes
- [x] Users can delete active quotes (automatically loads next saved quote)
- [x] Quotes are automatically saved when switching or creating new quotes
- [x] Quotes are automatically loaded when selected from dropdown
- [ ] Quotes persist across sessions (user-scoped)
- [ ] Quote metadata includes creation timestamp, last update timestamp, and owner
- [ ] Users can list all their saved quotes
- [ ] Active quote is automatically loaded when user logs in

#### Technical Requirements
- Integration with osc-sdk-python ReadPublicCatalog API
- Multi-region catalog support
- Catalog caching with 24-hour TTL
- Cost calculation logic matching cockpit-ext
- Discount rules per resource category
- Export functionality (CSV, PDF)
- Quote persistence (user-scoped storage)
- Quote lifecycle management (active/saved states)
- Quote metadata tracking (timestamps, owner)
- Quote CRUD operations (create, save, load, delete, list)

#### Quote Management & Lifecycle
- Quotes have two lifecycle states: "active" (only one active quote per user at a time) and "saved"
- Users can create new quotes (automatically becomes active)
- Users can save active quotes (moves to saved state, allows new active quote)
- Users can load saved quotes (becomes active, previous active becomes saved)
- Users can delete saved quotes
- Quotes are user-scoped (persist across sessions, tied to authenticated user)
- Quote metadata: creation timestamp, last update timestamp, owner (user identifier)

#### Priority: **HIGH** (Core Feature)

---

### 3.2 Consumption History (FR-2.1, FR-2.2)

#### Feature Description
Enable users to retrieve and analyze consumption history with various granularities and filters.

**Note**: This feature is now integrated into the unified "Cost Management" tab (see section 3.5) which combines consumption, trends, and budget management in a single cohesive view.

#### User Stories
- **US-2.1**: As an accountant, I want to view consumption history so I can reconcile invoices
- **US-2.2**: As an accountant, I want to filter consumption by date range so I can match billing periods
- **US-2.3**: As an accountant, I want to view consumption by day/week/month so I can analyze patterns
- **US-2.4**: As a CFO, I want to see consumption trends so I can understand spending patterns
- **US-2.5**: As a project manager, I want to filter consumption by tags so I can track project costs

#### Acceptance Criteria
- [x] Users can query consumption for date ranges
- [x] System supports granularity: day, week, month
- [x] Users can filter by region, service, resource type
- [x] System supports multiple accounts and regions
- [x] System displays consumption entries with cost breakdown
- [x] System aggregates consumption by resource type, region, or tag
- [x] System calculates total costs per period
- [x] System identifies top cost drivers
- [x] Users can export consumption data to CSV/JSON
- [x] Consumption data is cached (1h TTL)
- [x] Query performance < 5 seconds for 1 month of data
- [x] Currency is extracted from catalog entries
- [x] Region is displayed in consumption data
- [x] Total cost is calculated and displayed in summary

#### Technical Requirements
- Integration with osc-sdk-python ReadConsumptionAccount API
- **ReadAccountConsumption returns pre-aggregated data**:
  - Data separated by type (each resource/service type has its own entry)
  - Consolidated quantity over the queried period
  - Unit price (does not vary with period - per hour or per month)
  - Total cost per type calculated: quantity × unit_price
- **Date range semantics**: FromDate is inclusive, ToDate is exclusive (must be later than FromDate)
- **Date validation**: to_date must be in the past by at least 1 granularity period
- Data aggregation by granularity (when needed for display)
- Multi-account and multi-region support
- Consumption caching with 1-hour TTL
- Export functionality (CSV, JSON)

#### Priority: **HIGH** (Core Feature)

---

### 3.3 Current Cost Evaluation (FR-3.1, FR-3.2)

#### Feature Description
Enable users to evaluate current costs of used resources by fetching live resource states and correlating with catalog prices.

#### User Stories
- **US-3.1**: As a customer team member, I want to evaluate current costs so I can understand customer spending
- **US-3.2**: As a project manager, I want to see current resource costs so I can monitor spending
- **US-3.3**: As a CFO, I want to view total current costs so I can understand overall spending
- **US-3.4**: As an accountant, I want to filter costs by tags so I can allocate costs

#### Acceptance Criteria
- [x] System fetches current resources (VMs, Volumes, Snapshots, Public IPs, NAT Services, Load Balancers, VPNs, OOS buckets)
- [x] System calculates cost per hour, per month, per year
- [x] System correlates resources with catalog prices
- [x] Users can filter resources by tags
- [x] System displays cost breakdown by resource type
- [x] System supports multiple output formats (human-readable, JSON, CSV, ODS)
- [x] System shows individual resource costs with specifications
- [x] System displays cost per resource category
- [x] System handles dedicated instances and flexible GPUs
- [x] System calculates BSU volume IOPS costs
- [x] Query performance < 10 seconds for < 1000 resources
- [x] OOS bucket calculation is optional (off by default)
- [x] Catalog price lookup matches actual catalog structure (Type, Service, Operation fields)
- [x] Cost calculations use correct pricing units (monthly for volumes/snapshots, hourly for VMs)

#### Technical Requirements
- Integration with osc-sdk-python resource APIs (ReadVms, ReadVolumes, etc.)
- Catalog correlation for pricing
- Cost calculation per resource type
- Tag-based filtering
- Export functionality (human, JSON, CSV, ODS)

#### Priority: **HIGH** (Core Feature)

---

### 3.4 Trend Analysis & Cost Drift (FR-4.1, FR-4.2)

#### Feature Description
Enable users to analyze cost trends over time and compare estimated costs with actual consumption to identify cost drift.

**Note**: This feature is now integrated into the unified "Cost Management" tab (see section 3.5) which combines consumption, trends, and budget management in a single cohesive view. Trend projection is automatically extended until the end of the budget period when a budget is selected.

#### User Stories
- **US-4.1**: As a CFO, I want to analyze cost trends so I can forecast future spending
- **US-4.2**: As a customer team member, I want to analyze cost drift so I can identify optimization opportunities
- **US-4.3**: As a project manager, I want to see cost growth rates so I can plan budgets
- **US-4.4**: As a CFO, I want to compare actual costs vs. historical averages so I can identify anomalies

#### Acceptance Criteria
- [x] System tracks cost trends over time (daily, weekly, monthly)
- [x] System identifies cost increases/decreases
- [x] System calculates cost growth rate
- [x] System visualizes trends with charts
- [x] System compares actual costs vs. historical averages
- [ ] System compares estimated costs (osc-cost format) with actual consumption
- [x] System calculates drift percentage per resource category
- [x] System identifies resources with significant cost variance
- [x] System generates drift reports
- [x] Users can analyze drift for specific date ranges
- [x] Query performance < 10 seconds for 12 months of data (with async processing)
- [x] System supports async job processing for long-running trend calculations
- [x] System provides progress updates during trend calculation
- [x] Cost calculation uses UnitPrice × Value for accurate period costs
- [x] Date range iteration correctly handles day/week/month boundaries
- [x] **to_date validation**: Must be in the past by at least 1 granularity period
- [x] **from_date in past**: Do not show projected trend
- [x] **from_date in future**: Query consumption until last period excluding today, then project trend from last period to to_date
- [x] **Period boundary alignment**: When budget is provided, trend periods align with budget period boundaries (no crossing)

#### Technical Requirements
- Trend calculation algorithms
- Cost drift calculation logic (matching osc-cost)
- Chart visualization (Chart.js or similar)
- Historical data processing
- Export functionality

#### Priority: **MEDIUM** (Advanced Feature)

---

### 3.5 Cost Management (Unified View) - FR-2.1, FR-2.2, FR-4.1, FR-4.2, FR-4.3

#### Feature Description
Unified "Cost Management" tab that combines consumption history, trend analysis, and budget management into a single cohesive view. This replaces the separate Consumption, Trends, and Budgets tabs, providing an integrated experience for cost monitoring and budget tracking.

The unified view displays:
- **Past Consumption**: Historical consumption data for available periods
- **Budget Management**: Create and manage repeatable budgets per period (monthly, quarterly, yearly)
- **Trend Projection**: Consumption trends projected until the end of the budget period
- **Unified Graph**: Single chart showing consumption, budget limits, and trend projections together
- **Period Details**: Table showing consumption, budget, remaining budget, and utilization per period

#### User Stories
- **US-5.1**: As a project manager, I want to create budgets per project so I can control spending
- **US-5.2**: As a CFO, I want to set budgets for departments so I can manage organizational spending
- **US-5.3**: As a project manager, I want to see consumption, trends, and budgets in one view so I can make informed decisions
- **US-5.4**: As a CFO, I want to see budget compliance with consumption trends so I can monitor adherence
- **US-5.5**: As a project manager, I want to see trend projections until budget end date so I can plan ahead
- **US-5.6**: As a CFO, I want to visualize consumption vs. budget in a unified graph so I can quickly identify issues

#### Acceptance Criteria
- [x] Users can create budgets with name, amount, period type (monthly/quarterly/yearly), start date, and optional end date
- [x] Budgets repeat automatically per period type until end date (if specified) or indefinitely
- [x] System tracks budget vs. actual spending per period
- [x] System displays budget utilization and remaining budget per period
- [x] System shows consumption data for available historical periods
- [x] System projects consumption trends until the end of the selected budget period
- [x] Unified graph displays consumption line, budget line, and trend projection line
- [x] System shows period details table with consumption, budget, remaining, and utilization
- [x] Users can select a budget to analyze against consumption and trends
- [x] Budget calculations are accurate per period
- [x] All data sources (consumption, trends, budget) load and display correctly
- [x] Trend data only appears within the requested date range (from_date to to_date)
- [x] Budget periods are displayed throughout the entire date range, not just after to_date
- [x] Consumption data points are evenly spaced and aligned with timeline periods
- [x] All datasets (consumption, trend, budget) use consistent period keys aligned to the timeline
- [x] Timeline serves as master reference ensuring all data points align correctly on X-axis
- [x] **Date rounding**: All dates rounded to budget period boundaries (from_date round down, to_date round up)
- [x] **Consumption granularity selection**: One level under budget granularity
  - Budget yearly/quarterly → monthly
  - Budget monthly → weekly (with special month-based weeks: start on 1st, 4th week extends to month end)
  - Budget weekly → daily
- [x] **Cumulative consumption**: Progressively cumulated within budget periods, reset at period start
- [x] **Period boundary alignment**: Period calculations must NOT cross budget period boundaries
- [ ] Users can set budget alert thresholds (50%, 75%, 90%, 100%) - Future enhancement
- [ ] Alerts trigger at correct thresholds - Future enhancement
- [ ] Multi-account budget support - Future enhancement

#### Technical Requirements
- Budget storage in database (SQLite/PostgreSQL with SQLAlchemy)
- Budget API endpoints (CRUD operations)
- Budget status calculation (spent vs. budget per period)
- **Date rounding utilities**: Round from_date down, to_date up to budget period boundaries
- **Granularity selection**: Determine consumption granularity from budget period type
- **Monthly weeks calculation**: Special week calculation for monthly budgets (start on 1st, 4th week extends to month end)
- **Cumulative consumption calculation**: Progressive accumulation within budget periods, reset at period start
- **Period boundary validation**: Ensure periods do not cross budget boundaries
- Trend projection extension until budget end date (with boundary alignment)
- Unified chart visualization (Chart.js) with multiple datasets
- Data aggregation and alignment for unified display
- Period calculation (monthly/quarterly/yearly) with proper date handling

#### Integration Notes
- Consumption History (section 3.2) functionality is integrated into this tab
- Trend Analysis (section 3.4) functionality is integrated into this tab with projection support
- Separate Consumption, Trends, and Budgets tabs are hidden but code preserved for potential future use

#### Priority: **MEDIUM** (Advanced Feature)

---

### 3.6 Cost Allocation & Multi-Account Support (FR-5.1, FR-5.2)

#### Feature Description
Enable users to allocate costs by tags and manage multiple Outscale accounts.

#### User Stories
- **US-6.1**: As an accountant, I want to allocate costs by tags so I can assign costs to cost centers
- **US-6.2**: As a CFO, I want to aggregate costs across accounts so I can see total spending
- **US-6.3**: As a project manager, I want to switch between accounts so I can manage multiple projects
- **US-6.4**: As a CFO, I want to set budgets per account so I can manage multi-account spending

#### Acceptance Criteria
- [ ] Users can filter and group costs by resource tags
- [ ] System supports multiple tag keys and values
- [ ] Users can allocate costs to projects, departments, or cost centers
- [ ] System generates cost allocation reports
- [ ] Users can switch between accounts in the UI
- [ ] System aggregates costs across accounts
- [ ] Per-account budget management works
- [ ] Allocation calculations are accurate

#### Technical Requirements
- Tag-based filtering
- Cost allocation logic
- Multi-account session management
- Cross-account aggregation
- Report generation

#### Priority: **MEDIUM** (Advanced Feature)

---

### 3.7 Forecasting (FR-4.4)

#### Feature Description
Enable users to predict future costs based on historical trends.

#### User Stories
- **US-7.1**: As a CFO, I want to forecast future costs so I can plan budgets
- **US-7.2**: As a project manager, I want to see cost predictions so I can plan project spending

#### Acceptance Criteria
- [ ] System predicts future costs based on historical trends
- [ ] System supports linear forecasting model
- [ ] System supports exponential forecasting model
- [ ] System accounts for seasonal patterns (future enhancement)
- [ ] System provides confidence intervals
- [ ] System forecasts at different granularities (daily, weekly, monthly)

#### Technical Requirements
- Forecasting algorithms (linear, exponential)
- Historical data analysis
- Confidence interval calculation
- Visualization

#### Priority: **LOW** (Future Enhancement - Out of MVP Scope)

---

## 4. User Interface Requirements

### 4.1 Design Principles

- **Simplicity**: Interface should be simple and intuitive
- **Consistency**: Styling aligned with cockpit-ext reference project
- **Responsiveness**: Support desktop and tablet devices
- **Accessibility**: WCAG 2.1 Level AA compliance

### 4.2 Navigation

- **Tab-based navigation**: Main features accessible via tabs
  - Quotes (can access catalog without authentication, but saving quotes requires authentication)
  - Consumption (requires authentication)
  - Cost (requires authentication)
  - Trends (requires authentication)
  - Budgets (requires authentication)
  - Settings (optional)

### 4.3 Common UI Elements

- **Login Form**: Access Key, Secret Key, **Region selection (mandatory)**
  - Region must be one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
  - Region dropdown with only valid options
  - Credentials validated for selected region
- **Catalog Access**: Can be accessed without authentication
  - Users can browse catalogs and build quotes without logging in
  - Authentication required only for saving quotes or accessing authenticated features
- **Quote List View**: Display list of saved quotes with name, creation date, last update, item count
- **Quote Actions**: Save, Load, Delete buttons for quote management
- **Active Quote Indicator**: Visual indicator showing which quote is currently active
- **New Quote Button**: Create new quote (makes it active, saves previous active quote)
- **Quote Name Editor**: Allow users to name their quotes
- **Quote Metadata Display**: Show created date, last updated, owner
- **Loading Indicators**: Show during async operations
- **Error Messages**: User-friendly, clear error messages
- **Export Buttons**: CSV, JSON, PDF, ODS export options
- **Date Pickers**: For date range selection
- **Filters**: Region, service, resource type, tag filters

### 4.4 Responsive Design

- **Desktop**: Full feature set, optimal layout
- **Tablet**: Adapted layout, touch-friendly
- **Mobile**: Basic support (future enhancement)

### 4.5 Dark Mode (Optional)

- Toggle between light and dark themes
- Preference persistence
- Aligned with cockpit-ext dark mode

## 5. Acceptance Criteria Summary

### 5.1 Functional Requirements

All functional requirements (FR-1.1 through FR-5.2) must be implemented with:
- Complete feature functionality
- Proper error handling
- User-friendly interfaces
- Export capabilities where specified

### 5.2 Non-Functional Requirements

All non-functional requirements must be met:
- **Security**: NFR-1.1, NFR-1.2, NFR-1.3
- **Performance**: NFR-2.1, NFR-2.2, NFR-2.3
- **Reliability**: NFR-3.1, NFR-3.2, NFR-3.3
- **Usability**: NFR-4.1, NFR-4.2

### 5.3 Testing

- All test scenarios from TEST_SCENARIOS.md must pass
- Unit test coverage: 80%+
- Integration tests for all API endpoints
- End-to-end tests for major workflows

## 6. Priority Matrix

### High Priority (MVP - Must Have)
1. **Quote Building** (FR-1.1, FR-1.2)
2. **Consumption History** (FR-2.1, FR-2.2)
3. **Current Cost Evaluation** (FR-3.1, FR-3.2)
4. **Authentication & Session Management** (NFR-1.1, NFR-1.2)

### Medium Priority (Important - Should Have)
5. **Trend Analysis & Cost Drift** (FR-4.1, FR-4.2)
6. **Budget Management** (FR-4.3)
7. **Cost Allocation & Multi-Account** (FR-5.1, FR-5.2)

### Low Priority (Nice to Have - Future)
8. **Forecasting** (FR-4.4)
9. **Advanced Forecasting with ML** (Future)
10. **Cost Optimization Recommendations** (Future)

## 7. Roadmap

### Phase 0: Project Foundation ✅ **COMPLETED & VALIDATED**
- Project structure setup
- Documentation (Architecture, README, Test Scenarios, PRD)
- Development environment setup
- **Status**: All deliverables completed and validated by stakeholders

### Phase 1: Authentication & Session Management ✅ **COMPLETED & VALIDATED**
- Login/logout functionality
- Session management (in-memory, 30min timeout)
- Security implementation
- Frontend authentication UI
- Region validation and credential validation
- **Status**: All Phase 1 deliverables completed and validated
- Login/logout functionality
- Session management
- Security implementation

### Phase 2: Core Features - Quote Building ✅ **COMPLETED & VALIDATED**
- Catalog integration (ReadPublicCatalog API, unauthenticated access)
- Quote creation and management (CRUD operations)
- Quote lifecycle management (active/saved states)
- Database persistence (SQLite with SQLAlchemy)
- User and session management (database-backed)
- Quote selector UI with auto-save/auto-load
- Active quote deletion with automatic replacement
- Cost calculation (commitment discounts, global discounts)
- Export functionality (CSV export)
- **Status**: All Phase 2 deliverables completed and validated

### Phase 3: Core Features - Consumption History ✅ **COMPLETED & VALIDATED**
- Consumption query and display
- Filtering and aggregation
- Export functionality
- Currency extraction from catalog
- Region display in consumption data
- Total cost calculation and display
- **Status**: All Phase 3 deliverables completed and validated

### Phase 4: Core Features - Current Cost Evaluation ✅ **COMPLETED & VALIDATED**
- Resource cost evaluation (VMs, Volumes, Snapshots, Public IPs, NAT Services, Load Balancers, VPNs, OOS buckets)
- Catalog correlation with correct price lookup (matching actual catalog structure)
- Cost calculation per hour, month, and year
- Tag-based filtering
- Cost breakdown by resource type and category
- Export functionality (human-readable, JSON, CSV, ODS)
- OOS bucket calculation (optional, off by default)
- Cost caching (5m TTL)
- **Status**: All Phase 4 deliverables completed and validated

### Phase 5: Advanced Features - Trends & Drift
- Trend analysis
- Cost drift calculation
- Visualization

### Phase 6: Advanced Features - Budget Management
- Budget creation and tracking
- Alert system
- Compliance reports

### Phase 7: Advanced Features - Allocation & Multi-Account
- Cost allocation by tags
- Multi-account support
- Cross-account aggregation

### Phase 8: Polish & Testing
- Error handling enhancement
- Performance optimization
- Comprehensive testing
- Documentation completion

## 8. Dependencies

### External Dependencies
- **osc-sdk-python**: Outscale API integration
- **Outscale API**: Catalog, consumption, resource APIs
- **Modern Web Browser**: Chrome, Firefox, Safari, Edge

### Internal Dependencies
- **Flask**: Web framework
- **pandas**: Data processing
- **Chart.js**: Visualization (frontend)

## 9. Risks & Mitigation

### Risk 1: API Rate Limiting
- **Mitigation**: Implement caching, retry logic with exponential backoff

### Risk 2: Performance Issues with Large Accounts
- **Mitigation**: Implement pagination, optimize queries, caching

### Risk 3: Security Vulnerabilities
- **Mitigation**: Security review, input validation, secure session management

### Risk 4: Requirement Drift
- **Mitigation**: Validation checkpoints at each phase, stakeholder sign-off

## 10. Success Criteria

### MVP Success Criteria
- [ ] All high-priority features implemented
- [ ] All functional requirements (FR-1.1 through FR-3.2) working
- [ ] All non-functional requirements met
- [ ] Performance targets achieved
- [ ] Security requirements satisfied
- [ ] User acceptance testing passed

### Full Release Success Criteria
- [ ] All features (high + medium priority) implemented
- [ ] All functional requirements working
- [ ] Comprehensive test coverage
- [ ] Documentation complete
- [ ] Production deployment ready

## 11. Out of Scope (MVP)

The following features are explicitly out of scope for MVP but may be considered for future releases:

- Multi-user support with role-based access control
- Persistent storage for budgets and quotes (database)
- Real-time cost updates (WebSocket)
- Advanced forecasting with machine learning
- Cost optimization recommendations
- Integration with external tools (Slack, email)
- Mobile app
- Advanced reporting and dashboards

## 12. Appendix

### 12.1 Reference Documents
- Requirements Document: `define/requirements.md`
- Architecture Document: `docs/ARCHITECTURE.md`
- Test Scenarios: `docs/TEST_SCENARIOS.md`

### 12.2 Reference Projects
- **cockpit-ext**: Quote building and cost calculation
- **osc-cost**: Current cost evaluation
- **osc-draft-invoicing**: Consumption history
- **osc-sdk-python**: API integration

### 12.3 Glossary
- **FinOps**: Financial Operations - practice of managing cloud costs
- **Quote**: Cost estimate for planned infrastructure
- **Consumption**: Actual resource usage and billing data
- **Cost Drift**: Difference between estimated and actual costs
- **Budget**: Spending limit for a period
- **Granularity**: Time period for data aggregation (day/week/month)

