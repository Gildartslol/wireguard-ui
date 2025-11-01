#!/bin/bash

# WireGuard User Setup Script
# Creates a dedicated system user for WireGuard UI and configures sudo permissions

set -e

echo "=================================="
echo "WireGuard User Setup"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

# Variables
WG_USER="wireguard"
SUDOERS_FILE="/etc/sudoers.d/wireguard-ui"

echo "1. Creating system user: $WG_USER"

# Check if user already exists
if id "$WG_USER" &>/dev/null; then
    echo "   User $WG_USER already exists, skipping creation"
else
    # Create system user with no login shell and no home directory creation
    useradd --system --no-create-home --shell /usr/sbin/nologin "$WG_USER"
    echo "   User $WG_USER created successfully"
fi

echo ""
echo "2. Configuring sudo permissions for WireGuard commands"

# Create sudoers configuration file
cat > "$SUDOERS_FILE" << 'EOF'
# WireGuard UI - Allow wireguard user to run specific wg commands without password
# This file is managed by the WireGuard UI setup script

# Allow wg show commands (read WireGuard status)
wireguard ALL=(ALL) NOPASSWD: /usr/bin/wg show
wireguard ALL=(ALL) NOPASSWD: /usr/bin/wg show *

# Allow wg set commands (add/remove/update peers)
wireguard ALL=(ALL) NOPASSWD: /usr/bin/wg set *

# Note: wg genkey, wg pubkey, and wg genpsk do not require sudo
# These commands can be run directly by the wireguard user
EOF

# Set correct permissions on sudoers file
chmod 0440 "$SUDOERS_FILE"

echo "   Sudoers file created: $SUDOERS_FILE"
echo ""
echo "3. Validating sudoers configuration"

# Validate sudoers file
if visudo -c -f "$SUDOERS_FILE" &>/dev/null; then
    echo "   Sudoers configuration is valid"
else
    echo "   ERROR: Sudoers configuration is invalid"
    rm -f "$SUDOERS_FILE"
    exit 1
fi

echo ""
echo "4. Testing sudo access for $WG_USER"

# Test if the wireguard user can run wg commands
if sudo -u "$WG_USER" sudo -n wg show &>/dev/null; then
    echo "   SUCCESS: User $WG_USER can run wg commands via sudo"
elif sudo -u "$WG_USER" sudo -n wg &>/dev/null; then
    echo "   SUCCESS: User $WG_USER can run wg commands via sudo"
else
    echo "   WARNING: Could not verify sudo access (this may be normal if no WireGuard interface exists yet)"
fi

echo ""
echo "=================================="
echo "WireGuard User Setup Complete"
echo "=================================="
echo ""
echo "Summary:"
echo "  - System user created: $WG_USER"
echo "  - Sudoers file: $SUDOERS_FILE"
echo "  - Allowed commands:"
echo "      sudo wg show [interface] [dump]"
echo "      sudo wg set <interface> peer <key> ..."
echo "      wg genkey, wg pubkey, wg genpsk (no sudo required)"
echo ""
echo "The wireguard user can now manage WireGuard peers without requiring a password."
echo ""
