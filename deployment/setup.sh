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
echo "6. Initializing database..."
python -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all()"

echo ""
echo "7. Creating admin user..."
python create_admin.py

echo ""
echo "8. Building frontend..."
cd ../frontend
npm install
npm run build

echo ""
echo "9. Setting up WireGuard system user and sudo permissions..."
bash $INSTALL_DIR/deployment/setup_wireguard_user.sh

echo ""
echo "9b. Setting ownership of application files..."
cd $INSTALL_DIR
chown -R wireguard:wireguard .

echo ""
echo "10. Installing systemd service..."
cp $INSTALL_DIR/deployment/wg-dashboard.service /etc/systemd/system/
sed -i "s|/opt/wireguard-ui|$INSTALL_DIR|g" /etc/systemd/system/wg-dashboard.service
systemctl daemon-reload
systemctl enable wg-dashboard
systemctl start wg-dashboard

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
echo "Service status:"
systemctl status wg-dashboard --no-pager
echo ""
echo "The WireGuard UI is now running on http://localhost:5000"
echo ""
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/backend/.env with your WireGuard configuration"
echo "2. Configure nginx if needed for external access"
echo "3. Access the UI and log in with the admin account you created"
echo ""
echo "Logs: journalctl -u wg-dashboard -f"
echo ""
