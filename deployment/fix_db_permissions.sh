#!/bin/bash

# Fix database permissions for WireGuard UI
# Run this if you get "readonly database" errors

set -e

echo "===================================="
echo "WireGuard UI - Fix DB Permissions"
echo "===================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

INSTALL_DIR="/opt/wireguard-ui"

if [ ! -d "$INSTALL_DIR" ]; then
    echo "ERROR: Installation directory not found at $INSTALL_DIR"
    exit 1
fi

echo "Fixing permissions for $INSTALL_DIR/backend..."

cd $INSTALL_DIR

# Fix ownership of all files
echo "1. Setting ownership to wireguard:wireguard..."
chown -R wireguard:wireguard .

# Fix instance directory (Flask stores databases here)
echo "2. Setting instance directory permissions..."
mkdir -p backend/instance
chown wireguard:wireguard backend/instance
chmod 775 backend/instance
echo "   ✓ Fixed backend/instance/ directory"

# Fix database files specifically
echo "3. Setting database file permissions..."
if [ -f backend/instance/wg_dashboard.db ]; then
    chown wireguard:wireguard backend/instance/wg_dashboard.db
    chmod 664 backend/instance/wg_dashboard.db
    echo "   ✓ Fixed wg_dashboard.db"
else
    echo "   ⚠ wg_dashboard.db not found at backend/instance/"
fi

if [ -f backend/instance/wg_dashboard_mock.db ]; then
    chown wireguard:wireguard backend/instance/wg_dashboard_mock.db
    chmod 664 backend/instance/wg_dashboard_mock.db
    echo "   ✓ Fixed wg_dashboard_mock.db"
else
    echo "   ⚠ wg_dashboard_mock.db not found at backend/instance/"
fi

echo ""
echo "✓ Permissions fixed!"
echo ""
echo "Now restart the service:"
echo "  sudo systemctl restart wg-dashboard"
echo ""
