#!/bin/bash

# WireGuard UI Setup Script for Ubuntu
# This script sets up the WireGuard UI application on a fresh Ubuntu server

set -e

echo "=================================="
echo "WireGuard UI - Setup Script"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Variables
INSTALL_DIR="/opt/wireguard-ui"
VENV_DIR="$INSTALL_DIR/backend/venv"

echo "1. Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv nodejs npm wireguard wireguard-tools nginx

echo ""
echo "2. Creating installation directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Check if we're in the source directory or need to copy files
if [ -f "backend/requirements.txt" ]; then
    echo "Using existing source files..."
else
    echo "ERROR: Please run this script from the wireguard-ui directory"
    echo "  or copy files to $INSTALL_DIR first"
    exit 1
fi

echo ""
echo "3. Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

echo ""
echo "4. Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "5. Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please edit $INSTALL_DIR/backend/.env with your settings"
fi

echo ""
echo "6. Initializing production database..."
echo "   Location: $INSTALL_DIR/backend/instance/wg_dashboard.db"
python -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all()"
if [ -f backend/instance/wg_dashboard.db ]; then
    echo "   ✓ Production database created successfully"
    ls -lh backend/instance/wg_dashboard.db
else
    echo "   ⚠ WARNING: Production database not found!"
fi

echo ""
echo "6b. Creating mock database for testing..."
echo "   Location: $INSTALL_DIR/backend/instance/wg_dashboard_mock.db"
WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 create_mock_db.py
if [ -f backend/instance/wg_dashboard_mock.db ]; then
    echo "   ✓ Mock database created successfully"
    ls -lh backend/instance/wg_dashboard_mock.db
else
    echo "   ⚠ WARNING: Mock database not found!"
    echo "   You may need to create it manually later with:"
    echo "   cd $INSTALL_DIR/backend && WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 create_mock_db.py"
fi

echo ""
echo "7. Creating admin user for PRODUCTION database..."
echo "   Note: Mock database already has admin user (username: admin, password: admin)"
echo ""
echo "   Do you want to create an admin user for the production database now?"
echo "   (You can skip this and create it later if you're only using mock mode)"
read -p "   Create admin user? [Y/n]: " create_admin_choice

if [[ "$create_admin_choice" =~ ^[Nn]$ ]]; then
    echo "   Skipped. You can create an admin user later with:"
    echo "   cd $INSTALL_DIR/backend && source venv/bin/activate && python create_admin.py"
else
    python create_admin.py
fi

echo ""
echo "8. Installing frontend dependencies..."
cd ../frontend
npm install
echo "Frontend dependencies installed. Build skipped (run 'npm run build' manually when needed)"

echo ""
echo "9. Setting up WireGuard system user and sudo permissions..."
bash $INSTALL_DIR/deployment/setup_wireguard_user.sh

echo ""
echo "9b. Setting ownership of application files..."
cd $INSTALL_DIR
chown -R wireguard:wireguard .

echo ""
echo "9c. Setting database permissions..."
# Ensure instance directory exists and is writable
mkdir -p backend/instance
chown wireguard:wireguard backend/instance
chmod 775 backend/instance

# Ensure database files are writable by wireguard user
if [ -f backend/instance/wg_dashboard.db ]; then
    chown wireguard:wireguard backend/instance/wg_dashboard.db
    chmod 664 backend/instance/wg_dashboard.db
    echo "   ✓ Fixed wg_dashboard.db permissions"
fi
if [ -f backend/instance/wg_dashboard_mock.db ]; then
    chown wireguard:wireguard backend/instance/wg_dashboard_mock.db
    chmod 664 backend/instance/wg_dashboard_mock.db
    echo "   ✓ Fixed wg_dashboard_mock.db permissions"
fi

echo ""
echo "10. Installing systemd service..."
cp $INSTALL_DIR/deployment/wg-dashboard.service /etc/systemd/system/
sed -i "s|/opt/wireguard-ui|$INSTALL_DIR|g" /etc/systemd/system/wg-dashboard.service
systemctl daemon-reload
systemctl enable wg-dashboard
echo "Service configured and enabled, but NOT started automatically."
echo "To start: sudo systemctl start wg-dashboard"

echo ""
echo "11. Configuring nginx (optional)..."
if [ -f /etc/nginx/sites-available/default ]; then
    cp $INSTALL_DIR/deployment/nginx.conf /etc/nginx/sites-available/wg-dashboard
    echo "Nginx configuration created at /etc/nginx/sites-available/wg-dashboard"
    echo "To enable: ln -s /etc/nginx/sites-available/wg-dashboard /etc/nginx/sites-enabled/"
    echo "Then: systemctl reload nginx"
fi

echo ""
echo "=================================="
echo "Installation Complete!"
echo "=================================="
echo ""
echo "Database Locations:"
echo "-------------------"
if [ -f $INSTALL_DIR/backend/instance/wg_dashboard.db ]; then
    echo "✓ Production DB: $INSTALL_DIR/backend/instance/wg_dashboard.db"
else
    echo "✗ Production DB: NOT FOUND (this may be a problem)"
fi
if [ -f $INSTALL_DIR/backend/instance/wg_dashboard_mock.db ]; then
    echo "✓ Mock DB:       $INSTALL_DIR/backend/instance/wg_dashboard_mock.db"
    echo "                 Admin login: username=admin, password=admin"
else
    echo "✗ Mock DB:       NOT FOUND (create manually if needed for testing)"
fi
echo ""
echo "Mock Mode Testing:"
echo "------------------"
echo "To test in mock mode (no WireGuard required):"
echo "1. Edit $INSTALL_DIR/backend/.env and set:"
echo "   WG_MOCK_MODE=true"
echo "   WG_MOCK_SCENARIO=mixed"
echo "2. Start the service: sudo systemctl start wg-dashboard"
echo "3. Login with: username=admin, password=admin"
echo ""
echo "Configuration finished. Service is NOT running yet."
echo ""
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/backend/.env with your WireGuard configuration"
echo "2. Build the frontend: cd $INSTALL_DIR/frontend && npm run build"
echo "3. Start the service: sudo systemctl start wg-dashboard"
echo "4. Check status: sudo systemctl status wg-dashboard"
echo "5. Configure nginx if needed for external access"
echo "6. Access the UI at http://localhost:5000 or your server IP"
echo ""
echo "Useful commands:"
echo "  - View logs: journalctl -u wg-dashboard -f"
echo "  - Stop service: sudo systemctl stop wg-dashboard"
echo "  - Restart service: sudo systemctl restart wg-dashboard"
echo "  - List databases: ls -lh $INSTALL_DIR/backend/instance/"
echo ""
