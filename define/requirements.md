# OSC-FinOps Requirements

## 1. Overview

### 1.1 Purpose
Design a comprehensive FinOps service for Outscale customers and users, targeting project managers, CFOs, accountants, and Outscale customer teams. The service provides cost visibility, budgeting, forecasting, and optimization recommendations.

### 1.2 User Personas
- **Project Managers**: Need cost visibility per project, budget tracking, and resource optimization insights
- **CFOs**: Require high-level cost overview, trend analysis, and budget compliance reporting
- **Accountants**: Need detailed consumption history, invoice reconciliation, and cost allocation
- **Outscale Customer Team**: Require account-level cost analysis and optimization recommendations

### 1.3 Key Use Cases
1. **Quote Building**: Create cost estimates for planned infrastructure deployments
2. **Cost Monitoring**: Track current and historical resource costs
3. **Budget Management**: Set budgets, track spending, and receive alerts
4. **Trend Analysis**: Identify cost patterns and forecast future spending
5. **Cost Optimization**: Identify cost drift and optimization opportunities
6. **Reporting**: Generate reports for stakeholders

## 2. Functional Requirements

### 2.1 Quote Building (Reference: cockpit-ext)
**FR-1.1**: Build quotes based on resources and region catalog prices
- Select resources from public catalogs (multi-region support)
- Configure resource parameters (quantity, size, duration)
- Apply commitment-based discounts (1 month, 1 year, 3 years)
- Apply global discount percentages
- Support for monthly and hourly pricing models
- Group resources for organization
- Export quotes to CSV and PDF formats
- Save and load quote templates

**FR-1.2**: Catalog Management
- Load catalogs from Outscale API (ReadPublicCatalog)
- **ReadPublicCatalog API does not require authentication** - catalog can be accessed without user credentials
- Cache catalogs locally with refresh capability
- Support multiple regions: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
- Filter resources by category (Compute, Storage, Network, Licence)
- Handle catalog updates and versioning

### 2.2 Consumption History (Reference: osc-draft-invoicing)
**FR-2.1**: Retrieve consumption history with granularity options
- Query consumption data via ReadConsumptionAccount API
- Support granularity: per day, per week, per month
- Filter by date range (from_date, to_date)
- Filter by region, service, resource type
- Support multiple accounts on multiple regions
- Display consumption entries with cost breakdown

**FR-2.2**: Consumption Analysis
- Aggregate consumption by resource type, region, or tag
- Calculate total costs per period
- Compare consumption across different time periods
- Identify top cost drivers
- Export consumption data to CSV/JSON

### 2.3 Current Cost Evaluation (Reference: osc-cost)
**FR-3.1**: Evaluate current cost of used resources
- Fetch current resources (VMs, Volumes, Snapshots, Public IPs, NAT Services, Load Balancers, VPNs, OOS buckets, etc.)
- Calculate cost per hour, per month, per year
- Correlate resources with catalog prices
- Support resource filtering by tags
- Display cost breakdown by resource type
- Support multiple output formats (human-readable, JSON, CSV, ODS)

**FR-3.2**: Resource Cost Details
- Show individual resource costs with specifications
- Display cost per resource category
- Support cost estimation for resources without pricing
- Handle dedicated instances and flexible GPUs
- Calculate storage costs (BSU volumes with IOPS)

### 2.4 Trend Analysis and Cost Drift (Reference: osc-cost)
**FR-4.1**: Analyze trends of resource usage and cost
- Track cost trends over time (daily, weekly, monthly)
- Identify cost increases/decreases
- Calculate cost growth rate
- Visualize trends with charts and graphs
- Compare actual costs vs. historical averages

**FR-4.2**: Cost Drift Analysis
- Compare estimated costs (from osc-cost) with actual consumption (from digest)
- Calculate drift percentage per resource category
- Identify resources with significant cost variance
- Generate drift reports
- Support drift analysis for specific date ranges

**FR-4.3**: Budget Management
- Create budgets for projects, departments, or accounts
- Set budget alerts (threshold-based: 50%, 75%, 90%, 100%)
- Track budget vs. actual spending
- Support multiple budget periods (monthly, quarterly, yearly)
- Display budget utilization and remaining budget
- Generate budget compliance reports

**FR-4.4**: Forecasting
- Predict future costs based on historical trends
- Support linear and exponential forecasting models
- Account for seasonal patterns
- Provide confidence intervals
- Forecast at different granularities (daily, weekly, monthly)

### 2.5 Cost Allocation and Tagging
**FR-5.1**: Cost Allocation by Tags
- Filter and group costs by resource tags
- Support multiple tag keys and values
- Allocate costs to projects, departments, or cost centers
- Generate cost allocation reports

**FR-5.2**: Multi-Account Support
- Support multiple Outscale accounts
- Switch between accounts in the UI
- Aggregate costs across accounts
- Per-account budget management

## 3. Non-Functional Requirements

### 3.1 Security
**NFR-1.1**: Authentication and Authorization
- Users must provide Outscale credentials (Access Key, Secret Key) at login
- **Users must select a region when providing credentials** - region must be one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
- Credentials are validated for the selected region
- Credentials stored in memory only for the duration of the session
- No persistent storage of credentials (no database, no files)
- Session timeout: 30 minutes of inactivity (configurable)
- Support session refresh
- Clear credentials on logout or session expiration

**NFR-1.2**: API Authentication
- Use OSC4-HMAC-SHA256 signature method (as per Outscale API documentation)
- Prefer existing SDKs (osc-sdk-python) for API calls
- Implement proper error handling for authentication failures
- Support credential rotation without service interruption

**NFR-1.3**: Data Security
- Encrypt sensitive data in transit (HTTPS)
- No logging of credentials or sensitive data
- Implement proper input validation and sanitization
- Protect against common vulnerabilities (XSS, CSRF, SQL injection)

### 3.2 Performance
**NFR-2.1**: Response Times
- Quote calculation: < 1 second
- Consumption history query: < 5 seconds for 1 month of data
- Current cost evaluation: < 10 seconds for accounts with < 1000 resources
- Trend analysis: < 10 seconds for 12 months of data

**NFR-2.2**: Scalability
- Support concurrent sessions (minimum 50 concurrent users)
- Handle accounts with up to 10,000 resources
- Support consumption history queries for up to 24 months
- Implement pagination for large datasets

**NFR-2.3**: Caching
- Cache catalog data (refresh every 24 hours or on-demand)
- Cache consumption data with TTL (configurable, default 1 hour)
- Implement cache invalidation strategies

### 3.3 Reliability
**NFR-3.1**: Availability
- Service uptime target: 99.5%
- Graceful degradation when Outscale API is unavailable
- Retry logic for transient API failures (exponential backoff)
- Maximum 3 retries with backoff factor

**NFR-3.2**: Error Handling
- User-friendly error messages
- Log errors for debugging (without sensitive data)
- Handle API rate limiting gracefully
- Provide fallback mechanisms for partial failures

**NFR-3.3**: Logging & Monitoring
- Structured JSON-formatted logging with rotating file handlers
- Separate log files for general application logs and error-only logs
- Request context captured in error logs (method, path, endpoint, query params)
- Sensitive data excluded from logs (credentials, tokens)
- Log rotation with configurable size limits and backup counts
- Error logging with full stack traces and request context
- Console logging in development mode

### 3.4 Usability
**NFR-4.1**: User Interface
- Simple, intuitive interface with tab-based navigation
- Responsive design (desktop and tablet support)
- Consistent styling aligned with cockpit-ext reference project
- Dark mode support (optional)
- Loading indicators for long-running operations
- Clear error messages and validation feedback

**NFR-4.2**: Accessibility
- WCAG 2.1 Level AA compliance (minimum)
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support

## 4. Technical Requirements

### 4.1 Architecture
**TR-1.1**: Service Composition
- RESTful Python backend (Flask or FastAPI recommended)
- HTML/CSS/JavaScript frontend (vanilla JS or lightweight framework)
- Atomic, modular functions for each feature
- Separation of concerns: API layer, business logic, data access

**TR-1.2**: Backend Structure
```
backend/
  ├── api/           # REST API endpoi
```