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
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Authentication & Session Management         │   │
│  │  (In-memory sessions, OSC4-HMAC-SHA256)            │   │
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
│                                                               │
│  ReadCatalog  ReadConsumptionAccount  ReadAccounts          │
│  ReadVms  ReadVolumes  ReadSnapshots  ReadPublicIps        │
│  ReadNatServices  ReadLoadBalancers  ReadVpns              │
│  ReadOosBuckets  ReadSubregions                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

#### Frontend Components
- **Auth Module** (`frontend/js/auth.js`): Handles user authentication, session management, and credential input
- **Quote Module** (`frontend/js/quote.js`): Quote building interface with resource selection and cost calculation
- **Consumption Module** (`frontend/js/consumption.js`): Consumption history display with filtering and aggregation
- **Cost Module** (`frontend/js/cost.js`): Current cost evaluation and resource cost breakdown
- **Trends Module** (`frontend/js/trends.js`): Trend analysis and visualization
- **Budget Module** (`frontend/js/budget.js`): Budget management and tracking
- **Allocation Module** (`frontend/js/allocation.js`): Cost allocation by tags
- **Accounts Module** (`frontend/js/accounts.js`): Multi-account management

#### Backend Components
- **API Layer** (`backend/api/`): REST API endpoints, request/response handling, validation
- **Service Layer** (`backend/services/`): Business logic for each feature domain
- **Auth Module** (`backend/auth/`): Session management, credential validation
- **Models** (`backend/models/`): Data models and schemas
- **Utils** (`backend/utils/`): Utility functions and helpers
- **Config** (`backend/config/`): Configuration management

## 3. Data Flow

### 3.1 Authentication Flow

```
User → Frontend (Login Form)
  → POST /api/auth/login {access_key, secret_key, region}
  → Backend Auth Module
  → Validate region (must be: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2)
  → Validate credentials via osc-sdk-python (test API call for selected region)
  → Create session (in-memory, 30min timeout) with region
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
  → If miss: Call osc-sdk-python ReadCatalog API (NO AUTHENTICATION REQUIRED)
  → Cache and return catalog
  → Frontend displays resources
  → User selects resource, configures parameters
  → POST /api/quotes {items[], duration, discounts}
  → Backend Quote Service
  → Calculate costs (quantity × unit_price × duration)
  → Apply commitment discounts
  → Apply global discount
  → Return quote with total cost
```

**Note**: ReadCatalog API does not require authentication. Catalog can be accessed without user credentials. However, authenticated features (quotes, consumption, cost evaluation) require valid credentials with region selection.

### 3.3 Consumption History Flow

```
User → Frontend (Consumption Module)
  → GET /api/consumption?from_date=X&to_date=Y&granularity=day
  → Backend Consumption Service
  → Check cache (1h TTL, keyed by params)
  → If miss: Call osc-sdk-python ReadConsumptionAccount API
  → Aggregate by granularity (day/week/month)
  → Cache and return consumption data
  → Frontend displays consumption table/chart
```

### 3.4 Current Cost Evaluation Flow

```
User → Frontend (Cost Module)
  → GET /api/cost/current?region=eu-west-2&format=json
  → Backend Cost Service
  → Fetch current resources (ReadVms, ReadVolumes, etc.)
  → Fetch catalog for pricing
  → Correlate resources with catalog entries
  → Calculate cost per resource
  → Aggregate by resource type
  → Return cost breakdown
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
- **ReadCatalog API does not require authentication** - can be called without credentials
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

## 9. Scalability Considerations

### 9.1 Current Design (MVP)
- In-memory session storage (single server)
- In-memory caching (single server)
- Synchronous API calls
- No database (stateless design)

### 9.2 Future Scalability Options
- **Session Storage**: Move to Redis for multi-server support
- **Caching**: Move to Redis for shared cache
- **Database**: Add PostgreSQL for persistent data (budgets, saved quotes)
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
  - `ReadCatalog`: Catalog prices (**NO AUTHENTICATION REQUIRED**)
  - `ReadConsumptionAccount`: Consumption history (requires authentication)
  - `ReadAccounts`: Account information (requires authentication)
  - `ReadVms`, `ReadVolumes`, `ReadSnapshots`, etc.: Current resources (requires authentication)
  - `ReadSubregions`: Region information (requires authentication)

### 12.2 SDK Usage Pattern

**For ReadCatalog (No Authentication)**:
```python
from osc_sdk_python import OutscaleGateway

# ReadCatalog can be called without credentials
gateway = OutscaleGateway(
    region='eu-west-2'  # Region only, no credentials needed
)

# Make API call (no authentication required)
response = gateway.ReadCatalog(ReadCatalogRequest())
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

### 14.1 Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- No sensitive data in logs
- Request/response logging (excluding credentials)

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

## 16. Future Enhancements

- Multi-user support with role-based access
- Persistent storage for budgets and saved quotes
- Real-time cost updates (WebSocket)
- Advanced forecasting with ML
- Cost optimization recommendations
- Integration with external tools (Slack, email)

