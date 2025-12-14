#!/bin/bash
# Uninstallation script for OSC-FinOps systemd service
# Run with sudo: sudo ./uninstall-service.sh

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

SERVICE_NAME="osc-finops"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Uninstalling OSC-FinOps systemd service..."

# Stop and disable service if running
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "Stopping service..."
    systemctl stop "$SERVICE_NAME"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "Disabling service..."
    systemctl disable "$SERVICE_NAME"
fi

# Remove service file
if [ -f "$SERVICE_FILE" ]; then
    echo "Removing service file: $SERVICE_FILE"
    rm "$SERVICE_FILE"
    systemctl daemon-reload
fi

echo ""
echo "Service uninstalled."
echo ""
echo "Note: Application files and environment configuration are not removed."
echo "To remove them:"
echo "  - Application: rm -rf /opt/osc-finops"
echo "  - Environment: rm -rf /etc/${SERVICE_NAME}"
echo "  - Logs: rm -rf /var/log/${SERVICE_NAME}"
echo "  - User: userdel osc-finops (if not used elsewhere)"
echo ""
