# OSC-FinOps

[![Project Status](https://img.shields.io/badge/status-production-ready-green)]()
[![Test Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)]()

A comprehensive FinOps service for Outscale customers, providing cost visibility, budgeting, forecasting, and optimization recommendations.

## What is OSC-FinOps?

OSC-FinOps helps Outscale customers manage cloud costs effectively. It provides:

- **Quote Building**: Create cost estimates for planned infrastructure deployments
- **Cost Monitoring**: Track current and historical resource costs
- **Budget Management**: Set budgets, track spending, and receive alerts
- **Trend Analysis**: Identify cost patterns and forecast future spending
- **Cost Optimization**: Identify cost drift and optimization opportunities

## Quick Start

### Prerequisites

- Python 3.8+ (Python 3.9+ recommended)
- An Outscale account with API access (Access Key and Secret Key)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd osc-finops

# Run automated setup (creates venv and installs dependencies)
./setup.sh

# Start the development server
./start_dev.sh
```

The application will be available at: **http://localhost:8000**

### Manual Installation

If you prefer manual setup:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m flask --app backend/app run --host=0.0.0.0 --port=8000 --debug
```

## Getting Started

1. **Open the application**: Navigate to `http://localhost:8000` in your browser

2. **Customize your experience**:
   - Click the 🌙/☀️ button to switch between light and dark themes
   - Click the EN/FR button to switch between English and French
   - Preferences are saved automatically

3. **Browse catalogs** (no login required):
   - Select a region: cloudgouv-eu-west-1, eu-west-2, us-west-1, or us-east-2
   - Browse resources and build quotes

4. **Login for authenticated features**:
   - Access Key
   - Secret Key
   - Region (mandatory): cloudgouv-eu-west-1, eu-west-2, us-west-1, or us-east-2

## Key Features

### Quote Building
Build cost estimates by selecting resources from the catalog, configuring parameters, and applying discounts. Export quotes as CSV or PDF.

### Cost Management
Unified view combining:
- **Consumption History**: View past consumption for available periods
- **Budget Management**: Create repeatable budgets (monthly, quarterly, yearly)
- **Trend Projections**: See consumption trends projected until budget end date
- **Visual Analytics**: Single graph showing consumption, budget, and trends

### Current Cost Evaluation
Evaluate the current cost of used resources with region and tag filtering. Export data in multiple formats (human/json/csv/ods).

## Usage Tips

- **Date ranges**: `to_date` must be in the past by at least 1 granularity period
- **Budget selection**: When a budget is selected, dates automatically align to budget period boundaries
- **Trend projections**: Only shown when `from_date` is in the future
- **Consumption data**: Pre-aggregated with total cost calculated (quantity × unit_price)

## Troubleshooting

**ModuleNotFoundError**: Activate virtual environment and install dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Connection refused**: Ensure Flask server is running on port 8000

**Authentication failed**: Verify Access Key and Secret Key are correct for the selected region

**Catalog not loading**: Check network connectivity and verify region name is correct

## Configuration

### Development Configuration

Set environment variables for customization:

```bash
export FLASK_ENV=development
export SESSION_TIMEOUT=1800  # 30 minutes
export SERVER_PORT=8000
```

### Production Configuration

For production deployment, see `production.env.example` for all available configuration options. Key requirements:

- **SECRET_KEY**: Must be set in production (generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- **DATABASE_URL**: Use PostgreSQL for production (not SQLite)
- **CORS_ORIGINS**: Set to specific domains (not `*`)
- **SESSION_COOKIE_SECURE**: Should be `true` in production

Example production configuration:
```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export SECRET_KEY="your-generated-secret-key"
export DATABASE_URL="postgresql://user:password@localhost/osc_finops"
export CORS_ORIGINS="https://app.example.com"
```

See `production.env.example` for complete configuration template.

## Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest --timeout=30

# Run with coverage (target: 80%)
pytest --cov=backend --cov-report=html --cov-report=term-missing

# Run only unit tests (no credentials needed)
pytest tests/unit/ --timeout=30

# Run integration tests (requires live server and credentials)
export OSC_ACCESS_KEY="your_key"
export OSC_SECRET_KEY="your_secret"
export OSC_REGION="eu-west-2"
pytest tests/integration/ --timeout=30

# Run tests with live credentials and server
bash tests/run_tests.sh
```

**Test Coverage**: Current coverage is 80.17% (exceeds industry standard of 80%)

## Production Deployment

OSC-FinOps supports multiple deployment options for production:

### Docker Deployment

```bash
# Build Docker image
docker build -t osc-finops:latest .

# Run with docker-compose
docker-compose up -d

# Or run directly
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e FLASK_ENV=production \
  -v $(pwd)/logs:/app/logs \
  osc-finops:latest
```

### Systemd Service Deployment

```bash
# Install systemd service
sudo ./install-service.sh

# Copy application files to /opt/osc-finops
sudo cp -r . /opt/osc-finops/
sudo chown -R osc-finops:osc-finops /opt/osc-finops

# Configure environment
sudo nano /etc/osc-finops/production.env

# Start and enable service
sudo systemctl start osc-finops
sudo systemctl enable osc-finops

# Check status
sudo systemctl status osc-finops
```

### Manual Production Deployment

```bash
# Install dependencies (includes gunicorn)
pip install -r requirements.txt

# Set production environment variables
export FLASK_ENV=production
export SECRET_KEY="your-secret-key"
# ... other production settings

# Start production server
./start_prod.sh
```

For detailed deployment instructions, see `docs/DEPLOYMENT.md` (if available).

## Documentation

- **Architecture**: `docs/ARCHITECTURE.md`
- **Product Requirements**: `docs/PRD.md`
- **Test Scenarios**: `docs/TEST_SCENARIOS.md`
- **Testing Guide**: `tests/TESTING.md`
- **Production Deployment**: See `production.env.example` and deployment scripts

## Security Notes

- **Never commit credentials to the repository**
- **SECRET_KEY is required in production** - application will fail to start without it
- Credentials are stored in session (in-memory or database) - not in environment variables
- Sessions expire after 30 minutes of inactivity (configurable via `SESSION_TIMEOUT`)
- **HTTPS required in production environments** - set `SESSION_COOKIE_SECURE=true`
- Region selection is mandatory when providing credentials
- Use PostgreSQL for production (not SQLite) for better security and performance
- Set `CORS_ORIGINS` to specific domains in production (not `*`)
- Review `production.env.example` for all security-related configuration options

## Support

For issues, questions, or contributions, please contact the development team.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
