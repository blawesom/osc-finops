#!/bin/bash
# Installation script for OSC-FinOps systemd service
# Run with sudo: sudo ./install-service.sh

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Configuration
SERVICE_NAME="osc-finops"
APP_USER="osc-finops"
APP_GROUP="osc-finops"
APP_DIR="/opt/osc-finops"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_FILE="/etc/${SERVICE_NAME}/production.env"
LOG_DIR="/var/log/${SERVICE_NAME}"

echo "Installing OSC-FinOps systemd service..."

# Create application user and group
if ! id "$APP_USER" &>/dev/null; then
    echo "Creating user: $APP_USER"
    useradd --system --no-create-home --shell /bin/false "$APP_USER"
fi

# Create application directory
if [ ! -d "$APP_DIR" ]; then
    echo "Creating application directory: $APP_DIR"
    mkdir -p "$APP_DIR"
fi

# Create log directory
echo "Creating log directory: $LOG_DIR"
mkdir -p "$LOG_DIR"
chown "$APP_USER:$APP_GROUP" "$LOG_DIR"

# Create environment file directory
mkdir -p "/etc/${SERVICE_NAME}"

# Copy service file
echo "Installing service file: $SERVICE_FILE"
cp "$(dirname "$0")/${SERVICE_NAME}.service" "$SERVICE_FILE"

# Create environment file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating environment file: $ENV_FILE"
    if [ -f "$(dirname "$0")/production.env.example" ]; then
        cp "$(dirname "$0")/production.env.example" "$ENV_FILE"
        echo ""
        echo "IMPORTANT: Edit $ENV_FILE and set your production configuration:"
        echo "  - SECRET_KEY (required)"
        echo "  - DATABASE_URL (if using PostgreSQL)"
        echo "  - CORS_ORIGINS (for security)"
        echo ""
    else
        touch "$ENV_FILE"
        echo "# OSC-FinOps Production Environment" > "$ENV_FILE"
        echo "# Set your production configuration here" >> "$ENV_FILE"
    fi
    chmod 600 "$ENV_FILE"
    chown root:root "$ENV_FILE"
fi

# Set ownership of application directory
echo "Setting ownership of $APP_DIR to $APP_USER:$APP_GROUP"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Copy your application files to $APP_DIR"
echo "2. Create virtual environment: python3 -m venv $APP_DIR/venv"
echo "3. Install dependencies: $APP_DIR/venv/bin/pip install -r requirements.txt"
echo "4. Edit environment file: $ENV_FILE"
echo "5. Initialize database: $APP_DIR/venv/bin/python -c 'from backend.database import init_db; init_db()'"
echo "6. Start service: sudo systemctl start $SERVICE_NAME"
echo "7. Enable on boot: sudo systemctl enable $SERVICE_NAME"
echo "8. Check status: sudo systemctl status $SERVICE_NAME"
echo ""
