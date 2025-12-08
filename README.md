# OSC-FinOps

[![Project Status](https://img.shields.io/badge/status-development-yellow)]()

A comprehensive FinOps service for Outscale customers, providing cost visibility, budgeting, forecasting, and optimization recommendations.

## Overview

OSC-FinOps is designed to help Outscale customers and users (project managers, CFOs, accountants, and customer teams) manage cloud costs effectively. The service provides:

- **Quote Building**: Create cost estimates for planned infrastructure deployments
- **Cost Monitoring**: Track current and historical resource costs
- **Budget Management**: Set budgets, track spending, and receive alerts
- **Trend Analysis**: Identify cost patterns and forecast future spending
- **Cost Optimization**: Identify cost drift and optimization opportunities
- **Reporting**: Generate reports for stakeholders

## Features

### Core Features
- **Quote Building**: Build quotes based on resources and region catalog prices (like cockpit-ext)
- **Cost Management**: Unified view combining consumption history, trend analysis, and budget management
  - View past consumption for available periods
  - Create and manage repeatable budgets per period (monthly, quarterly, yearly)
  - See consumption trends projected until budget end date
  - Visualize consumption, budget, and trends in a single cohesive graph
- **Current Cost Evaluation**: Evaluate current cost of used resources (like osc-cost)

### User Experience Features
- **Dark/Light Theme Toggle**: Switch between light and dark themes with preference persistence
- **Multi-language Support**: French and English language switching with full UI translation

### Advanced Features
- **Cost Allocation**: Allocate costs by tags, projects, or departments
- **Multi-Account Support**: Manage multiple Outscale accounts and regions
- **Export Capabilities**: Export data to CSV, JSON, PDF, and ODS formats

## Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **pip** (Python package manager)
- **An Outscale account** with API access (Access Key and Secret Key)
- **Network access** to Outscale API endpoints
- **Modern web browser** (Chrome, Firefox, Safari, Edge - latest versions)
  - JavaScript enabled
  - localStorage support (for theme and language preferences)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd osc-finops
```

### 2. Set Up Python Virtual Environment

It is recommended to use a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 4. Database Setup

The application uses SQLite by default (no additional setup required). The database file `osc_finops.db` will be created automatically in the project root on first run.

For production, you can switch to PostgreSQL by setting the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost/osc_finops"
```

### 5. Verify Installation

```bash
# Check Python version (should be 3.8+)
python --version

# Verify key dependencies
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import osc_sdk_python; print('OSC SDK installed')"
```

## Configuration

### Environment Variables (Optional)

You can configure the application using environment variables:

```bash
# Flask configuration
export FLASK_APP=backend/app.py
export FLASK_ENV=development  # or 'production'
export FLASK_DEBUG=1  # Set to 0 in production

# Session configuration
export SESSION_TIMEOUT=1800  # 30 minutes in seconds

# Cache configuration
export CATALOG_CACHE_TTL=86400  # 24 hours in seconds
export CONSUMPTION_CACHE_TTL=3600  # 1 hour in seconds

# Server configuration
export SERVER_HOST=0.0.0.0
export SERVER_PORT=5000
```

### Configuration File (Future)

A configuration file (`config.json`) can be created for persistent settings (not yet implemented in MVP).

## Development Setup

### Project Structure

```
osc-finops/
├── backend/              # Python backend code
│   ├── api/             # REST API endpoints
│   ├── services/        # Business logic services
│   ├── models/          # Data models
│   ├── auth/            # Authentication module
│   ├── utils/           # Utility functions
│   ├── config/          # Configuration management
│   └── app.py           # Flask application entry point
├── frontend/            # Frontend code
│   ├── css/             # Stylesheets
│   │   └── styles.css   # Main stylesheet with theme support
│   ├── js/              # JavaScript modules
│   │   ├── app.js       # Main app logic and theme management
│   │   ├── auth.js      # Authentication
│   │   ├── i18n.js      # Internationalization (FR/EN)
│   │   ├── quote-builder.js
│   │   ├── cost-builder.js
│   │   ├── cost-management-builder.js
│   │   └── ...
│   ├── assets/          # Static assets
│   └── index.html       # Main HTML file
├── tests/               # Test files
│   ├── unit/            # Unit tests
│   └── integration/      # Integration tests
├── docs/                # Documentation
│   ├── ARCHITECTURE.md   # Architecture document
│   ├── TEST_SCENARIOS.md # Test scenarios
│   └── PRD.md           # Product Requirement Document
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Running the Development Server

1. **Activate virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate
   ```

2. **Start the Flask development server**:
   ```bash
   # From project root
   python -m flask --app backend/app run --host=0.0.0.0 --port=5000 --debug
   
   # Or if FLASK_APP is set:
   flask run --host=0.0.0.0 --port=5000 --debug
   ```

3. **Access the application**:
   - Open your browser and navigate to: `http://localhost:5000`
   - The frontend will be served from the `frontend/` directory

### Development Workflow

1. **Make code changes** in `backend/` or `frontend/`
2. **Flask auto-reloads** on code changes (when `--debug` is enabled)
3. **Refresh browser** to see frontend changes
4. **Check console** for errors and logs

## Quick Start

### Automated Setup

```bash
# Run setup script (creates venv and installs dependencies)
./setup.sh

# Start development server
./start.sh
```

The application will be available at: **http://localhost:5000**

For detailed testing instructions, see [tests/TESTING.md](tests/TESTING.md).

## Usage

### First Time Setup

1. **Start the server** (see Development Setup above)
2. **Open the application** in your browser: `http://localhost:5000`
3. **Customize Your Experience** (Available immediately):
   - **Theme Toggle**: Click the 🌙/☀️ button in the header to switch between light and dark themes
   - **Language Toggle**: Click the EN/FR button in the header to switch between English and French
   - Preferences are saved and persist across sessions
4. **Browse Catalogs** (No login required):
   - You can browse catalogs and build quotes without authentication
   - Select from supported regions: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
5. **Login** (Required for authenticated features):
   - Access Key
   - Secret Key
   - **Region (mandatory)** - must be one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
   - Credentials are validated for the selected region

### Using the Application

#### Quote Building
1. Navigate to the "Quotes" tab (no login required for catalog browsing)
2. Select a region (cloudgouv-eu-west-1, eu-west-2, us-west-1, or us-east-2)
3. Choose a resource from the catalog (ReadPublicCatalog API works without authentication)
4. Configure resource parameters
5. Add to quote
6. Apply discounts and duration
7. Export quote as CSV or PDF
8. **Note**: Saving quotes may require authentication (future feature)

#### Cost Management (Unified View)
1. Navigate to the "Cost Management" tab
2. Select date range and granularity (day/week/month)
   - **Note**: to_date must be in the past by at least 1 granularity period
   - **Date semantics**: from_date is inclusive, to_date is exclusive
3. Optionally select region filter
4. Create a budget:
   - Click "Create Budget"
   - Enter budget name, amount, period type (monthly/quarterly/yearly)
   - Set start date and optional end date
   - Budget will repeat automatically per period
5. Select a budget to analyze
   - **When budget is selected**:
     - Dates are automatically rounded to budget period boundaries (from_date down, to_date up)
     - Consumption granularity is automatically selected (one level under budget):
       - Budget yearly/quarterly → monthly
       - Budget monthly → weekly (special month-based weeks: start on 1st, 4th week extends to month end)
       - Budget weekly → daily
     - Consumption is displayed cumulatively (progressive within budget periods, reset at period start)
     - All periods align with budget boundaries (no crossing)
6. Click "Load Data" to see:
   - Consumption data for available periods (pre-aggregated with total cost calculated)
   - Budget limits per period
   - Trend projections (only if from_date is in the future):
     - If from_date is in the past: no projected trend shown
     - If from_date is in the future: consumption queried until last period excluding today, then trend projected
   - Unified graph showing all datasets (consumption, budget, trend projection if applicable)
   - Period details table with consumption, budget, remaining, and utilization
7. Export data as CSV or JSON

**Important Notes**:
- **ReadAccountConsumption** returns pre-aggregated data: quantity consolidated, total cost calculated (quantity × unit_price)
- **Trend projection rules**: Projected trends only shown when from_date is in the future
- **Budget-aware processing**: When budget is selected, all dates and periods are aligned to budget boundaries
- **Cumulative consumption**: Within each budget period, consumption accumulates progressively and resets at period start

#### Current Cost Evaluation
1. Navigate to the "Cost" tab
2. Select region and filters
3. View current resource costs
4. Export in desired format (human/json/csv/ods)

#### User Interface Customization
- **Theme Switching**: Use the theme toggle button (🌙/☀️) in the header to switch between light and dark themes
  - Light theme is the default
  - Theme preference is saved in browser localStorage
  - Applies to all pages and persists across sessions
- **Language Switching**: Use the language toggle button (EN/FR) in the header to switch between English and French
  - English is the default
  - Language preference is saved in browser localStorage
  - All UI text, labels, buttons, and messages are translated

## API Documentation

API documentation will be available at `/api/docs` (OpenAPI/Swagger) once implemented.

For now, refer to:
- `docs/ARCHITECTURE.md` for API design principles
- `docs/PRD.md` for detailed feature specifications

## Testing

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with timeout (as per user rules)
pytest --timeout=30

# Run specific test file
pytest tests/unit/test_quote_service.py

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Test Structure

- **Unit Tests**: `tests/unit/` - Test individual functions and services
- **Integration Tests**: `tests/integration/` - Test API endpoints and integrations
- **Test Scenarios**: See `docs/TEST_SCENARIOS.md` for comprehensive test cases

## Project Status

**Current Phase**: Phase 0 - Project Foundation & Documentation

This project is in active development. See the implementation plan for phase details.

## Contributing

### Development Guidelines

1. **Use virtual environment** for Python development
2. **Follow PEP 8** style guidelines (enforced by black and flake8)
3. **Write tests** for new features
4. **Update documentation** when adding features
5. **Commit messages** should be explicit and descriptive
6. **Separate commits** for unrelated changes

### Code Style

```bash
# Format code
black backend/

# Lint code
flake8 backend/

# Type check (optional)
mypy backend/
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'flask'`
- **Solution**: Activate virtual environment and install dependencies: `pip install -r requirements.txt`

**Issue**: `Connection refused` when accessing API
- **Solution**: Ensure Flask server is running and check port number

**Issue**: `Authentication failed` when logging in
- **Solution**: Verify Access Key and Secret Key are correct for the selected region, check network connectivity to Outscale API
- **Note**: Region must be one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2

**Issue**: `Session expired` frequently
- **Solution**: Check SESSION_TIMEOUT configuration, increase if needed for development

**Issue**: Catalog not loading
- **Solution**: 
  - Catalog does not require authentication - check network connectivity
  - Verify region name is one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
  - If using authenticated access, verify credentials are valid for the selected region

## Security Notes

- **Never commit credentials** to the repository
- **Use environment variables** for sensitive configuration
- **Credentials are stored in-memory only** (not persisted)
- **Sessions expire** after 30 minutes of inactivity
- **HTTPS required** in production environments
- **Region selection is mandatory** when providing credentials
- **Supported regions**: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
- **ReadPublicCatalog API does not require authentication** - catalog can be accessed without credentials

## References

This project references and learns from:
- **cockpit-ext**: Quote building and cost calculation logic
- **osc-cost**: Current cost evaluation and resource cost calculation
- **osc-draft-invoicing**: Consumption history retrieval patterns
- **osc-sdk-python**: Outscale API integration

## Documentation

- **Architecture**: `docs/ARCHITECTURE.md`
- **Test Scenarios**: `docs/TEST_SCENARIOS.md`
- **Product Requirements**: `docs/PRD.md`
- **Requirements**: `define/requirements.md`

## License

[To be determined]

## Support

For issues, questions, or contributions, please contact the development team.

## Roadmap

See the implementation plan for detailed phases:
- Phase 0: Project Foundation & Documentation ✅ **COMPLETED & VALIDATED**
- Phase 1: Authentication & Session Management ✅ **COMPLETED & VALIDATED**
- Phase 2: Catalog Integration & Quote Building ✅ **COMPLETED & VALIDATED**
- Phase 3: Consumption History ✅ **COMPLETED & VALIDATED**
- Phase 4: Current Cost Evaluation ✅ **COMPLETED & VALIDATED**
- Phase 5: Trend Analysis & Cost Drift ✅ **COMPLETED & VALIDATED**
- Phase 6: Cost Management (Unified View) ✅ **COMPLETED**
  - Budget Management with database persistence
  - Unified view combining consumption, trends, and budgets
  - Trend projection until budget end date
  - Integrated graph visualization
- Phase 7: Cost Allocation & Multi-Account Support
- Phase 8: Polish, Testing & Documentation
