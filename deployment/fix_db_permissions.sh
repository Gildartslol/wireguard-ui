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

# Fix database files specifically
echo "2. Setting database file permissions..."
if [ -f backend/wg_dashboard.db ]; then
    chown wireguard:wireguard backend/wg_dashboard.db
    chmod 664 backend/wg_dashboard.db
    echo "   ✓ Fixed wg_dashboard.db"
else
    echo "   ⚠ wg_dashboard.db not found"
fi

if [ -f backend/wg_dashboard_mock.db ]; then
    chown wireguard:wireguard backend/wg_dashboard_mock.db
    chmod 664 backend/wg_dashboard_mock.db
    echo "   ✓ Fixed wg_dashboard_mock.db"
else
    echo "   ⚠ wg_dashboard_mock.db not found"
fi

# Fix backend directory (SQLite needs to create journal files)
echo "3. Setting backend directory permissions..."
chown wireguard:wireguard backend/
chmod 775 backend/
echo "   ✓ Fixed backend/ directory"

echo ""
echo "✓ Permissions fixed!"
echo ""
echo "Now restart the service:"
echo "  sudo systemctl restart wg-dashboard"
echo ""
