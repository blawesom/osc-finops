# OSC-FinOps Architecture Document

## 1. Overview

OSC-FinOps is a comprehensive FinOps service designed for Outscale customers, providing cost visibility, budgeting, forecasting, and optimization recommendations. The service follows a client-server architecture with a RESTful Python backend and a vanilla JavaScript frontend.

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  (HTML/CSS/JavaScript - Vanilla JS, No Framework)           │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Auth   │  │  Quote   │  │Consumption│  │   Cost   │  │
│  │  Module  │  │  Module  │  │  Module   │  │  Module  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Trends  │  │  Budget  │  │Allocation│  │ Accounts │  │
│  │  Module  │  │  Module  │  │  Module  │  │  Module  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Backend Layer                          │
│              (Python - Flask/FastAPI)                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              API Layer (REST Endpoints)             │   │
│  │  /api/auth/*  /api/catalog/*  /api/quotes/*        │   │
│  │  /api/consumption/*  /api/cost/*  /api/budgets/*   │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Service Layer (Business Logic)            │   │
│  │  catalog_service  quote_service  consumption_service │   │
│  │  cost_service  trend_service  drift_service         │   │
│  │  budget_service  allocation_service                 │   │
│  │  Quote Service: CRUD, lifecycle (active/saved),    │   │
│  │  ownership verification, user-scoped persistence,   │   │
│  │  auto-save on switch, auto-load on delete          │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Authentication & Session Management         │   │
│  │  (Database-backed sessions, OSC4-HMAC-SHA256)       │   │
│  │  (SQLite/PostgreSQL with SQLAlchemy ORM)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Caching Layer                            │   │
│  │  (Catalog cache: 24h TTL, Consumption: 1h TTL)      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ OSC4-HMAC-SHA256
                            │ Authentication
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Outscale API (via SDK)                     │
│                                                             │
│  ReadPublicCatalog  ReadConsumptionAccount  ReadAccounts    │
│  ReadVms  ReadVolumes  ReadSnapshots  ReadPublicIps         │
│  ReadNatServices  ReadLoadBalancers  ReadVpns               │
│  ReadOosBuckets  ReadSubregions                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

#### Frontend Components
- **Auth Module** (`frontend/js/auth.js`): Handles user authentication, session management, and credential input
- **Quote Module** (`frontend/js/quote.js`, `frontend/js/quote-builder.js`): Quote building interface with resource selection, cost calculation, and quote management (create, save, load, delete)
- **Consumption Module** (`frontend/js/consumption.js`): Consumption history API service (used by Cost Management)
- **Cost Module** (`frontend/js/cost.js`, `frontend/js/cost-builder.js`): Current cost evaluation and resource cost breakdown
- **Trends Module** (`frontend/js/trends.js`): Trend analysis API service (used by Cost Management)
- **Budget Module** (`frontend/js/budget.js`): Budget service for API communication
- **Cost Management Module** (`frontend/js/cost-management-builder.js`): Unified view combining consumption, trends, and budget management

**Note**: Consumption, Trends, and Budgets functionality is integrated into the unified "Cost Management" tab. The original API service modules (consumption.js, trends.js) are preserved for API communication, but the separate builder modules and tabs have been removed.

#### Backend Components
- **API Layer** (`backend/api/`): REST API endpoints, request/response handling, validation
- **Service Layer** (`backend/services/`): Business logic for each feature domain
  - catalog_service  quote_service_db  consumption_service
  - cost_service  trend_service
  - budget_service
  - **consumption_service**: Pre-aggregated data handling, date validation and rounding utilities,
    granularity selection from budget, period boundary alignment, monthly weeks calculation
  - **trend_service**: Async trend calculation with progress tracking, 
    date validation (to_date must be in past), projection rules based on from_date position,
    accurate cost calculation (UnitPrice × Value), trend projection with budget boundary alignment
  - **budget_service**: Budget CRUD operations, period calculation, 
    budget status calculation (spent vs. budget per period), date rounding (from_date down, to_date up),
    cumulative consumption calculation, granularity selection, period boundary validation
- **Auth Module** (`backend/auth/`): Session management, credential validation
- **Models** (`backend/models/`): Data models including Budget model for database persistence
- **Models** (`backend/models/`): Data models and schemas
- **Utils** (`backend/utils/`): Utility functions and helpers
  - `logger.py`: Logging configuration and setup
  - `error_logger.py`: Error logging with request context
- **Config** (`backend/config/`): Configuration management

## 3. Data Flow

### 3.1 Authentication Flow

```
User → Frontend (Login Form)
  → POST /api/auth/login {access_key, secret_key, region}
  → Backend Auth Module
  → Validate region (must be: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2)
  → Validate credentials via osc-sdk-python (test API call for selected region)
  → Create session (database-backed, 30min timeout) with region
  → Return session_id
  → Frontend stores session_id
  → Subsequent requests include session_id (region stored in session)
```

**Note**: Region selection is mandatory when providing credentials. The region must be one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2. Credentials are validated for the selected region.

### 3.2 Quote Building Flow

```
User → Frontend (Quote Module)
  → GET /api/catalog?region=eu-west-2
  → Backend Catalog Service
  → Check cache (24h TTL)
  → If miss: Call ReadPublicCatalog API via requests.post (NO AUTHENTICATION REQUIRED)
  → Cache and return catalog
  → Frontend displays resources
  → User selects resource, configures parameters
  → POST /api/quotes (create new quote - becomes active)
  → Backend Quote Service
  → Create quote with "active" state, set owner from session
  → Calculate costs (quantity × unit_price × duration)
  → Apply commitment discounts
  → Apply global discount
  → Return quote with total cost
  → User can save quote: PUT /api/quotes/{id} {status: "saved"}
  → User can load quote: GET /api/quotes/{id} (becomes active)
  → User can list quotes: GET /api/quotes (list all user's quotes)
  → User can delete quote: DELETE /api/quotes/{id}
```

**Note**: ReadPublicCatalog API does not require authentication. Catalog can be accessed without user credentials. However, authenticated features (quotes, consumption, cost evaluation) require valid credentials with region selection.

### 3.2.1 Quote Management Flow

```
User → Frontend (Quote Management)
  → GET /api/quotes (list all user's quotes)
  → Backend Quote Service
  → Filter quotes by owner (from session)
  → Return list of quotes with metadata
  → Frontend displays quote list
  → User selects quote to load
  → GET /api/quotes/{id}
  → If saved quote loaded, it becomes active (previous active saved automatically)
  → User can delete quotes (active or saved)
  → If active quote deleted, next saved quote automatically loaded
  → If no saved quotes, new empty quote created
  → Backend Quote Service
  → Verify ownership
  → Set quote status to "active"
  → Set previous active quote to "saved"
  → Return quote data
  → Frontend loads quote into builder
```

### 3.3 Consumption History Flow

```
User → Frontend (Consumption Module)
  → GET /api/consumption?from_date=X&to_date=Y&granularity=day
  → Backend Consumption API
  → Validate to_date is in past by at least 1 granularity period
  → Validate from_date < to_date (ToDate is exclusive)
  → Backend Consumption Service
  → Check cache (1h TTL, keyed by params)
  → If miss: Call osc-sdk-python ReadConsumptionAccount API
    → API returns pre-aggregated data:
      - Separated by type
      - Consolidated quantity over period
      - Unit price (per hour or per month)
    → Calculate total cost per type: quantity × unit_price
  → Cache and return consumption data
  → Frontend displays consumption table/chart (Price already calculated)
```

**Key Changes**:
- ReadAccountConsumption returns pre-aggregated data (quantity consolidated, cost calculated)
- FromDate is inclusive, ToDate is exclusive
- to_date must be in the past by at least 1 granularity period
- Total cost calculation: quantity × unit_price (done in service layer)

### 3.4 Trend Analysis Flow

```
User → Frontend (Cost Management Module)
  → POST /api/trends/async (submit job with from_date, to_date, granularity, budget_id)
  → Backend Trends API (async endpoint)
  → Validate to_date is in past by at least 1 granularity period
  → Validate from_date < to_date (ToDate is exclusive)
  → Create async job and return job_id
  → Background thread processes job:
    → Backend Trend Service
    → Check if from_date is in past or future
    → If from_date in past: Query consumption until to_date, no projection
    → If from_date in future: Query consumption until last period excluding today, then project
    → If budget provided: Align periods to budget boundaries
    → Calculate trends (growth rate, historical average, period changes)
    → Project trend if needed (respecting budget boundaries)
    → Update job progress during processing
    → Store result in job queue
  → Frontend polls GET /api/trends/jobs/<job_id> for status
  → When completed, retrieve result from job
  → Frontend displays trends (projected periods shown with dashed line)
```

**Key Changes**:
- to_date must be in past by at least 1 granularity period
- If from_date in past: no projected trend shown
- If from_date in future: query until last period excluding today, then project
- Periods align with budget boundaries when budget is provided

### 3.5 Budget Status Flow

```
User → Frontend (Cost Management Module)
  → GET /api/budgets/{budget_id}/status?from_date=X&to_date=Y
  → Backend Budget API
  → Validate from_date < to_date (ToDate is exclusive)
  → Backend Budget Service
  → Round dates to budget period boundaries (from_date down, to_date up)
  → Determine consumption granularity (one level under budget)
    - Budget yearly/quarterly → monthly
    - Budget monthly → weekly (special month-based weeks)
    - Budget weekly → daily
  → Generate consumption periods (respecting budget boundaries)
  → Fetch consumption data for each period
  → Calculate cumulative consumption (progressive within period, reset at start)
  → Return budget status with cumulative consumption per period
  → Frontend displays cumulative consumption vs. budget
```

**Key Changes**:
- Date rounding: from_date round down, to_date round up to budget period boundaries
- Consumption granularity: one level under budget granularity
- Monthly weeks: start on 1st, 4th week extends to month end
- Cumulative consumption: progressive within budget periods, reset at period start
- Periods must not cross budget boundaries

### 3.6 Current Cost Evaluation Flow

```
User → Frontend (Cost Tab)
  → GET /api/cost {region, tags, include_oos, format, force_refresh}
    → Backend (Cost API)
      → Auth Middleware (require_auth)
        → Cost Service (get_current_costs)
          → OSC SDK (ReadVms, ReadVolumes, ReadSnapshots, ReadPublicIps, ReadNatServices, ReadLoadBalancers, ReadVpns, ReadOosBuckets)
          → Catalog Service (get_catalog)
          → Cost Calculation Logic (calculate_vm_price, calculate_volume_cost, etc.)
          → Cost Cache (5m TTL)
        → Response (JSON/CSV/Human)
```

## 4. Security Architecture

### 4.1 Authentication & Authorization

**Session Management**:
- Sessions stored in-memory (Python dictionary)
- Session timeout: 30 minutes of inactivity (configurable)
- Session ID generated using secure random (UUID)
- No persistent storage of credentials

**Credential Handling**:
- Credentials and region provided at login via POST request
- **Region selection is mandatory** - must be one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
- Credentials validated by making test API call via osc-sdk-python for the selected region
- Credentials and region stored in session object (in-memory only)
- Credentials cleared on logout or session expiration
- No logging of credentials or sensitive data

**API Authentication**:
- **ReadPublicCatalog API does not require authentication** - can be called without credentials
- All other Outscale API calls use OSC4-HMAC-SHA256 signature method
- Implemented via osc-sdk-python SDK (no manual signature generation)
- Credentials and region retrieved from session for each authenticated API call
- Support for credential rotation (user can re-login with new credentials)
- Region must match the region used during login

### 4.2 Data Security

**In Transit**:
- HTTPS enforced in production
- TLS 1.2+ required
- CORS configured for frontend origin only

**At Rest**:
- No persistent storage of credentials
- Session data in memory only (lost on server restart)
- Catalog cache stored in memory (can be regenerated)
- No sensitive data in logs

**Input Validation**:
- All API inputs validated using marshmallow schemas
- SQL injection protection (no SQL database, but input sanitization)
- XSS protection (output escaping in frontend)
- CSRF protection (session-based tokens)

### 4.3 Security Best Practices

- No credentials in URL parameters
- No credentials in logs or error messages
- Secure session cookie settings (HttpOnly, Secure, SameSite)
- Rate limiting on authentication endpoints
- Input sanitization and validation
- Error messages don't leak sensitive information

## 5. Technology Stack

### 5.1 Backend Technology

**Framework Choice: Flask**
- **Rationale**: 
  - Lightweight and flexible
  - Good for REST APIs
  - Extensive ecosystem
  - Easy to integrate with osc-sdk-python
  - Lower learning curve than FastAPI
  - Sufficient for the requirements (no async needed initially)

**Alternative Considered: FastAPI**
- Pros: Modern, async support, automatic OpenAPI docs
- Cons: Steeper learning curve, async complexity not needed for MVP
- **Decision**: Flask chosen for simplicity and team familiarity

**Key Libraries**:
- `flask`: Web framework
- `flask-cors`: CORS support
- `flask-session`: Session management
- `osc-sdk-python`: Outscale API integration
- `marshmallow`: Data validation and serialization
- `pandas`: Data processing and aggregation
- `cachetools`: Caching implementation

### 5.2 Frontend Technology

**Framework Choice: Vanilla JavaScript**
- **Rationale**:
  - Requirements specify "as simple as possible"
  - No heavy frameworks needed
  - Aligns with cockpit-ext reference project
  - Faster load times
  - Easier to maintain

**Key Libraries**:
- `Chart.js` (or similar): For trend visualization
- No build tools required (direct browser execution)

### 5.3 Development Tools

- `pytest`: Testing framework (with timeout support)
- `black`: Code formatting
- `flake8`: Linting
- `mypy`: Type checking (optional)

## 6. Reference Projects

### 6.1 cockpit-ext
**Reference Points**:
- Quote building logic and cost calculation
- Catalog integration and caching
- Discount application rules
- Frontend styling and UI patterns
- Resource selection and parameter configuration

**Key Learnings**:
- Catalog caching strategy (24h TTL)
- Commitment discount rules per resource category
- Monthly vs. hourly pricing handling
- Group organization of quote items

### 6.2 osc-cost
**Reference Points**:
- Current cost evaluation logic
- Resource cost calculation per type
- Catalog correlation for pricing
- Cost drift analysis methodology
- Output format handling (human/json/csv/ods)

**Key Learnings**:
- Resource type handling (VMs, Volumes, Snapshots, etc.)
- IOPS cost calculation for BSU volumes
- Dedicated instances and flexible GPUs handling
- Cost aggregation and breakdown

### 6.3 osc-draft-invoicing
**Reference Points**:
- Consumption history retrieval
- Date range filtering
- Consumption aggregation
- Catalog correlation for consumption entries

**Key Learnings**:
- ReadConsumptionAccount API usage
- Consumption entry processing
- Date range handling
- Multi-region consumption support

### 6.4 oks-explorer
**Reference Points**:
- Simple Python backend with http.server (we use Flask instead)
- Frontend structure and organization
- API proxy pattern
- Session management approach

**Key Learnings**:
- Simple architecture patterns
- Frontend-backend separation
- Static file serving

## 7. Caching Strategy

### 7.1 Catalog Cache
- **TTL**: 24 hours
- **Key**: Region name
- **Storage**: In-memory dictionary
- **Invalidation**: Manual refresh endpoint or TTL expiration
- **Size**: ~1-5 MB per region (estimated)

### 7.2 Consumption Cache
- **TTL**: 1 hour (configurable)
- **Key**: Combination of from_date, to_date, region, account
- **Storage**: In-memory dictionary with TTL tracking
- **Invalidation**: TTL expiration or manual clear
- **Size**: Variable (depends on date range)

### 7.3 Session Cache
- **TTL**: 30 minutes of inactivity
- **Key**: Session ID (UUID)
- **Storage**: In-memory dictionary
- **Invalidation**: Timeout or explicit logout
- **Size**: ~1 KB per session

## 8. Error Handling

### 8.1 API Error Handling
- **Outscale API Errors**: Wrapped and returned as user-friendly messages
- **Rate Limiting**: Retry with exponential backoff (max 3 retries)
- **Network Errors**: Graceful degradation, user notification
- **Validation Errors**: Clear error messages with field-level details

### 8.2 Frontend Error Handling
- **API Errors**: Display user-friendly messages
- **Network Errors**: Retry mechanism with user feedback
- **Validation Errors**: Inline field validation feedback
- **Session Expiration**: Auto-redirect to login

### 8.3 Error Logging Flow

```
Exception/Error → Flask Error Handler
  → log_exception() or log_error_message()
  → Extract request context (method, path, endpoint, query params)
  → Filter sensitive data (credentials, tokens)
  → Build structured log data (exception type, message, stack trace, context)
  → Write to logs/errors.log (ERROR level)
  → Write to logs/app.log (INFO/ERROR level)
  → Return user-friendly error response
```

**Error Logging Features**:
- Automatic request context extraction
- Sensitive data filtering
- Full stack trace capture
- Structured JSON format for log analysis
- Separate error-only log file for monitoring

## 9. Scalability Considerations

### 9.1 Current Design (MVP)
- SQLite database for persistent storage (users, sessions, quotes)
- Database-backed session storage
- In-memory caching for catalogs and consumption (single server)
- Synchronous API calls
- SQLAlchemy ORM for database operations

### 9.2 Database Schema

**Users Table**:
- `user_id` (UUID, PRIMARY KEY)
- `account_id` (VARCHAR, UNIQUE, NOT NULL) - Outscale account ID (unique identifier)
- `access_key` (VARCHAR, NOT NULL) - Outscale access key (non-unique)
- `created_at`, `last_login_at`, `is_active`

**Sessions Table**:
- `session_id` (UUID, PRIMARY KEY)
- `user_id` (UUID, FOREIGN KEY → users.user_id)
- `access_key`, `secret_key`, `region`
- `created_at`, `last_activity`, `expires_at`

**Quotes Table**:
- `quote_id` (UUID, PRIMARY KEY)
- `user_id` (UUID, FOREIGN KEY → users.user_id)
- `name`, `status` ('active' or 'saved')
- `duration`, `duration_unit`, `commitment_period`, `global_discount_percent`
- `created_at`, `updated_at`

**Quote Items Table**:
- `item_id` (UUID, PRIMARY KEY)
- `quote_id` (UUID, FOREIGN KEY → quotes.quote_id, ON DELETE CASCADE)
- `resource_name`, `resource_type`, `resource_data` (JSON), `quantity`, `unit_price`
- `region`, `parameters` (JSON), `iops_unit_price`, `display_order`
- `created_at`, `updated_at`

**Budgets Table**:
- `budget_id` (UUID, PRIMARY KEY)
- `user_id` (UUID, FOREIGN KEY → users.user_id)
- `name` (VARCHAR, NOT NULL)
- `amount` (FLOAT, NOT NULL, > 0)
- `period_type` (VARCHAR, 'monthly', 'quarterly', or 'yearly')
- `start_date` (DATE, NOT NULL)
- `end_date` (DATE, nullable, optional)
- `created_at`, `updated_at`

### 9.3 Future Scalability Options
- **Session Storage**: Move to Redis for multi-server support (optional)
- **Caching**: Move to Redis for shared cache
- **Database**: Migrate from SQLite to PostgreSQL for production
- **Async Processing**: Move to FastAPI with async/await for better concurrency
- **Load Balancing**: Add load balancer for multiple backend instances

## 10. Deployment Architecture

### 10.1 Development
- Single server running Flask development server
- Frontend served as static files
- Local virtual environment

### 10.2 Production (Future)
- WSGI server (gunicorn or uwsgi)
- Reverse proxy (nginx) for static files and SSL termination
- Environment-based configuration
- Logging and monitoring setup

## 11. API Design Principles

### 11.1 RESTful Design
- Resource-based URLs (`/api/quotes/{id}`)
- HTTP methods for actions (GET, POST, PUT, DELETE)
- Standard HTTP status codes
- JSON request/response format

### 11.2 Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### 11.3 Success Response Format
```json
{
  "data": {},
  "metadata": {
    "pagination": {},
    "cache": {}
  }
}
```

## 12. Integration Points

### 12.1 Outscale API Integration
- **SDK**: osc-sdk-python (v0.38.0+)
- **Authentication**: OSC4-HMAC-SHA256 (handled by SDK)
- **APIs Used**:
  - `ReadPublicCatalog`: Catalog prices (**NO AUTHENTICATION REQUIRED**)
  - `ReadConsumptionAccount`: Consumption history (requires authentication)
  - `ReadAccounts`: Account information (requires authentication)
  - `ReadVms`, `ReadVolumes`, `ReadSnapshots`, etc.: Current resources (requires authentication)
  - `ReadSubregions`: Region information (requires authentication)

### 12.2 SDK Usage Pattern

**For ReadPublicCatalog (No Authentication)**:
```python
import requests
import json

# ReadPublicCatalog can be called without credentials using direct HTTP request
url = "https://api.eu-west-2.outscale.com/api/v1/ReadPublicCatalog"
response = requests.post(
    url,
    headers={'Content-Type': 'application/json'},
    data=json.dumps({})
)
catalog_data = response.json()
```

**For Authenticated APIs**:
```python
from osc_sdk_python import OutscaleGateway

# Initialize with session credentials and region
gateway = OutscaleGateway(
    access_key=session['access_key'],
    secret_key=session['secret_key'],
    region=session['region']  # Region from login
)

# Make authenticated API calls
response = gateway.ReadConsumptionAccount(ReadConsumptionAccountRequest())
```

**Supported Regions**:
- cloudgouv-eu-west-1
- eu-west-2
- us-west-1
- us-east-2

## 13. Performance Targets

- Quote calculation: < 1 second
- Consumption history query: < 5 seconds for 1 month
- Current cost evaluation: < 10 seconds for < 1000 resources
- Trend analysis: < 10 seconds for 12 months
- Support 50+ concurrent sessions
- Handle accounts with up to 10,000 resources

## 14. Monitoring & Logging

### 14.1 Logging Infrastructure

**Logging Configuration**:
- **Setup**: `backend/utils/logger.py` - Configures JSON-formatted rotating file handlers
- **Error Logging**: `backend/utils/error_logger.py` - Captures exceptions with request context
- **Log Files**: 
  - `logs/app.log` - General application logs (INFO and above)
  - `logs/errors.log` - Error-only logs (ERROR and above)
- **Log Format**: JSON with timestamp, level, name, message, and structured data
- **Rotation**: Configurable max bytes (default 10MB) and backup count (default 5)
- **Request Context**: Automatically captured for errors (method, path, endpoint, query params, user agent)
- **Security**: Sensitive data (access_key, secret_key, password, token) automatically excluded

**Error Handling Integration**:
- All Flask error handlers log exceptions using `log_exception()`
- APIError exceptions logged with status codes
- 404 and 500 errors logged with context
- Unhandled exceptions logged with full stack traces
- Request context automatically extracted and included in error logs

**Configuration** (from `backend/config/settings.py`):
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE_PATH`: Log directory path (default: "logs/")
- `LOG_MAX_BYTES`: Max file size before rotation (default: 10485760 = 10MB)
- `LOG_BACKUP_COUNT`: Number of backup files to keep (default: 5)
- `ERROR_LOG_FILE`: Error log filename (default: "errors.log")
- `APP_LOG_FILE`: Application log filename (default: "app.log")

**Logging Features**:
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- No sensitive data in logs
- Request/response logging (excluding credentials)
- Separate error-only log file for easier monitoring
- Console logging in development mode

### 14.2 Metrics (Future)
- Response times per endpoint
- API call counts
- Cache hit/miss rates
- Session counts
- Error rates

## 15. Testing Strategy

### 15.1 Unit Tests
- Service layer functions
- Cost calculation logic
- Data transformation functions
- Validation logic

### 15.2 Integration Tests
- API endpoints
- SDK integration
- Caching behavior
- Session management

### 15.3 End-to-End Tests
- Complete user workflows
- Multi-step operations
- Error scenarios

## 16. Data Models

### 16.1 Quote Data Model

```
Quote:
  - quote_id: UUID (unique identifier)
  - name: string (user-defined quote name)
  - status: "active" | "saved" (lifecycle state)
  - owner: string (user identifier from session)
  - items: array of quote items
    - id: UUID (item identifier)
    - resource_name: string
    - resource_type: string
    - resource_data: object (catalog entry data)
    - quantity: float
    - unit_price: float
    - region: string
    - parameters: object (optional resource-specific parameters)
  - duration: float
  - duration_unit: string ("hours", "days", "weeks", "months", "years")
  - commitment_period: string | null ("1month", "1year", "3years", or null)
  - global_discount_percent: float (0-100)
  - created_at: datetime (ISO format)
  - updated_at: datetime (ISO format)
```

### 16.2 Quote Status Transitions

- **New quote created** → status: "active"
- **Save active quote** → status: "saved"
- **Load saved quote** → status: "active" (previous active quote becomes "saved")
- **Delete active quote** → next saved quote automatically loaded (if available), otherwise new quote created
- **Delete saved quote** → quote removed, no replacement
- **Only one "active" quote per user at a time**

### 16.3 Quote Ownership

- Quotes are user-scoped (tied to authenticated user)
- Owner identifier derived from session (access_key or session_id)
- All quote operations verify ownership before execution
- Users can only access their own quotes

## 17. API Endpoints Reference

### 17.1 Quote API Endpoints

**Create Quote**:
- `POST /api/quotes`
- **Auth**: Required
- **Request Body**: `{ "name": "Quote Name" }`
- **Response**: Quote object with "active" status
- **Behavior**: Creates new quote, sets as active, saves previous active quote if exists

**List Quotes**:
- `GET /api/quotes`
- **Auth**: Required
- **Response**: Array of quote summaries (filtered by owner)
- **Fields**: quote_id, name, status, item_count, created_at, updated_at

**Get Quote**:
- `GET /api/quotes/{id}`
- **Auth**: Required
- **Response**: Full quote object with calculation
- **Behavior**: Verifies ownership, if loading saved quote, sets to active and saves previous active

**Update Quote**:
- `PUT /api/quotes/{id}`
- **Auth**: Required
- **Request Body**: `{ "name": "...", "status": "saved", "duration": ..., "duration_unit": "...", "commitment_period": "...", "global_discount_percent": ... }`
- **Response**: Updated quote object
- **Behavior**: Verifies ownership, updates fields, manages status transitions

**Delete Quote**:
- `DELETE /api/quotes/{id}`
- **Auth**: Required
- **Response**: Success message with optional `replacement_quote` field
- **Behavior**: Verifies ownership, deletes quote (active or saved)
- **Replacement**: If deleting active quote, returns next saved quote (if available) and makes it active

**Add Item to Quote**:
- `POST /api/quotes/{id}/items`
- **Auth**: Required
- **Request Body**: Quote item object
- **Response**: Updated quote object

**Remove Item from Quote**:
- `DELETE /api/quotes/{id}/items/{item_id}`
- **Auth**: Required
- **Response**: Updated quote object

**Export Quote to CSV**:
- `GET /api/quotes/{id}/export/csv`
- **Auth**: Required
- **Response**: CSV file download

## 18. Future Enhancements

- Multi-user support with role-based access
- Persistent storage for budgets and saved quotes (database)
- Real-time cost updates (WebSocket)
- Advanced forecasting with ML
- Cost optimization recommendations
- Integration with external tools (Slack, email)

