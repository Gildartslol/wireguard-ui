# WireGuard UI - Web Administration Dashboard

A modern web-based administration interface for managing WireGuard VPN connections. Built with Flask (Python) backend and Vue.js frontend.

## Features

- **Real-time Monitoring**: View active WireGuard connections with live status updates
- **Peer Management**: Add, remove, and configure WireGuard peers through a web interface
- **Configuration Generator**: Generate peer configuration files for easy client setup
- **Connection History**: Track peer connection/disconnection events over time
- **User Authentication**: Secure access with username/password authentication
- **Modern UI**: Clean, responsive interface built with Tailwind CSS and DaisyUI

## Architecture

- **Backend**: Flask 3.x with wireguard-tools library (native Netlink API)
- **Frontend**: Vue.js 3 with Vite, Tailwind CSS, and DaisyUI
- **Database**: SQLite (PostgreSQL compatible)
- **Authentication**: Flask-Login with secure password hashing

## Prerequisites

### Ubuntu Server Requirements

- Ubuntu 20.04 LTS or newer
- Python 3.9+
- Node.js 18+
- WireGuard installed and configured
- Root access (for WireGuard management via Netlink)

### Install WireGuard

```bash
sudo apt update
sudo apt install wireguard wireguard-tools
```

## Quick Start (Automated Setup)

1. **Clone or copy this repository to your Ubuntu server**:
   ```bash
   cd /opt
   sudo git clone <repository-url> wireguard-ui
   # or copy files to /opt/wireguard-ui
   ```

2. **Run the setup script**:
   ```bash
   cd /opt/wireguard-ui
   sudo bash deployment/setup.sh
   ```

3. **Follow the prompts** to create an admin user

4. **Access the dashboard** at `http://your-server-ip:5000`

The setup script will:
- Install all dependencies
- Create Python virtual environment
- Set up the database
- Build the frontend
- Configure systemd service
- Set up NET_ADMIN capability for WireGuard access

## Manual Installation

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
nano .env  # Edit with your settings
```

### 2. Configure Environment Variables

Edit `backend/.env`:

```env
FLASK_ENV=production
SECRET_KEY=<generate-with-python-secrets.token_urlsafe(32)>
DATABASE_URI=sqlite:///wg_dashboard.db
WG_INTERFACE=wg0
WG_CONFIG_PATH=/etc/wireguard/wg0.conf
WG_SERVER_ADDRESS=10.0.0.1/24
WG_SERVER_PORT=51820
WG_SERVER_PUBLIC_KEY=<your-server-public-key>
```

### 3. Grant NET_ADMIN Capability

The application requires NET_ADMIN capability to access WireGuard via Netlink:

```bash
sudo setcap cap_net_admin+ep backend/venv/bin/python

# Verify
getcap backend/venv/bin/python
# Should output: backend/venv/bin/python cap_net_admin+ep
```

### 4. Initialize Database and Create Admin User

```bash
cd backend
source venv/bin/activate

# Initialize database
python -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all()"

# Create admin user
python create_admin.py
```

### 5. Build Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### 6. Start the Application

#### Development Mode

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python app.py

# Terminal 2 - Frontend (for development)
cd frontend
npm run dev
```

#### Production Mode with Systemd

```bash
# Copy systemd service file
sudo cp deployment/wg-dashboard.service /etc/systemd/system/

# Edit if installation path is different
sudo nano /etc/systemd/system/wg-dashboard.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable wg-dashboard
sudo systemctl start wg-dashboard

# Check status
sudo systemctl status wg-dashboard

# View logs
sudo journalctl -u wg-dashboard -f
```

## Nginx Reverse Proxy (Optional)

For external access with HTTPS:

```bash
# Copy nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/wg-dashboard

# Edit server_name and SSL settings
sudo nano /etc/nginx/sites-available/wg-dashboard

# Enable site
sudo ln -s /etc/nginx/sites-available/wg-dashboard /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Usage

### First Login

1. Navigate to `http://your-server:5000` (or configured domain)
2. Log in with the admin credentials you created
3. You'll be redirected to the Dashboard

### Dashboard

- View real-time statistics (total peers, connected, disconnected, transfer)
- Monitor active connections with status indicators
- Auto-refreshes every 10 seconds

### Managing Peers

1. Go to **Peers** page
2. Click **Add New Peer**
3. Fill in peer details:
   - Name: Friendly name for the peer
   - Public Key: Generate new keys or paste existing
   - Allowed IPs: IP addresses for the peer (e.g., `10.0.0.2/32`)
   - Description: Optional notes
4. Click **Add Peer**
5. Download the configuration file for the client

### Connection History

- View historical connection records
- Filter by time range (last hour, 24 hours, week)
- Track bandwidth usage over time

## Configuration

### WireGuard Server Setup

Ensure your WireGuard server is properly configured:

```bash
# Generate server keys if needed
wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key

# Example wg0.conf
cat > /etc/wireguard/wg0.conf <<EOF
[Interface]
PrivateKey = <server-private-key>
Address = 10.0.0.1/24
ListenPort = 51820
SaveConfig = false
EOF

# Start WireGuard
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0
```

### Firewall Configuration

```bash
# Allow WireGuard port
sudo ufw allow 51820/udp

# Allow web interface (if needed)
sudo ufw allow 5000/tcp  # or 80/443 for nginx
```

## Troubleshooting

### Permission Denied Errors

**Symptom**: "Permission denied" when accessing WireGuard

**Solution**:
```bash
# Ensure capability is set
sudo setcap cap_net_admin+ep /opt/wireguard-ui/backend/venv/bin/python

# Or run service as root (already configured in systemd)
```

### Dashboard Not Showing Peers

**Checks**:
1. Verify WireGuard is running: `sudo wg show`
2. Check WG_INTERFACE in `.env` matches your interface name
3. View application logs: `sudo journalctl -u wg-dashboard -f`
4. Test Netlink access:
   ```bash
   cd /opt/wireguard-ui/backend
   source venv/bin/activate
   python -c "from wireguard_tools import WireguardDevice; print(WireguardDevice.get('wg0'))"
   ```

### Can't Add/Remove Peers

**Checks**:
1. Ensure Flask process has NET_ADMIN capability
2. Check WireGuard kernel module is loaded: `lsmod | grep wireguard`
3. Verify no SELinux/AppArmor restrictions

### Frontend Can't Connect to Backend

**Checks**:
1. Backend is running: `sudo systemctl status wg-dashboard`
2. Port 5000 is accessible
3. Check CORS settings in `backend/config.py`
4. View browser console for errors

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
FLASK_ENV=development python app.py
```

### Frontend Development

```bash
cd frontend

# Start dev server (with hot reload)
npm run dev

# Frontend will proxy API calls to localhost:5000
```

### Mock Mode (Development without WireGuard)

For development on machines without WireGuard installed:

```bash
cd backend
source venv/bin/activate

# Enable mock mode
export WG_MOCK_MODE=true
export WG_MOCK_SCENARIO=mixed  # Options: empty, connected, mixed, disconnected

# Run backend
python app.py
```

Or add to `backend/.env`:
```
WG_MOCK_MODE=true
WG_MOCK_SCENARIO=mixed
```

**Available Scenarios**:
- `empty` - No peers configured
- `connected` - All peers actively connected
- `mixed` - Some connected, some disconnected (default)
- `disconnected` - All peers configured but disconnected

Mock data files are in `backend/tests/mock_data/`. This allows full frontend development and UI testing without WireGuard.

### Running Tests

```bash
# Backend tests
cd backend
source venv/bin/activate
python -m pytest tests/

# Frontend tests
cd frontend
npm run test
```

## Project Structure

```
wireguard-ui/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration management
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication logic
│   ├── wg_manager.py       # WireGuard manager (Netlink API)
│   ├── routes/
│   │   ├── auth.py         # Auth endpoints
│   │   ├── dashboard.py    # Dashboard API
│   │   └── peers.py        # Peer management API
│   ├── templates/
│   │   └── peer.conf.j2    # Peer config template
│   ├── requirements.txt
│   ├── .env.example
│   └── create_admin.py
├── frontend/
│   ├── src/
│   │   ├── views/          # Login, Dashboard, Peers, History
│   │   ├── components/     # PeerCard, ConfigGenerator
│   │   ├── services/
│   │   │   └── api.js      # API client
│   │   ├── router/
│   │   │   └── index.js    # Vue Router configuration
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── deployment/
│   ├── wg-dashboard.service # Systemd service
│   ├── nginx.conf           # Nginx configuration
│   └── setup.sh             # Automated setup script
├── documentation.md         # Detailed implementation docs
└── README.md               # This file
```

## Security Considerations

1. **Authentication**: Always use strong passwords for admin accounts
2. **HTTPS**: Use nginx with SSL/TLS in production environments
3. **Firewall**: Restrict access to the web interface to trusted networks
4. **Updates**: Keep dependencies up to date for security patches
5. **Backups**: Regularly backup the SQLite database
6. **NET_ADMIN**: The application requires NET_ADMIN capability - ensure only trusted users can access the server

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for managing WireGuard VPN infrastructure.

## Support

For issues, questions, or feature requests:
- Check the documentation.md file for detailed implementation information
- Review the troubleshooting section above
- Check application logs: `sudo journalctl -u wg-dashboard -f`

## Changelog

### Version 1.0.0
- Initial release
- Real-time peer monitoring
- Peer management (add, remove, configure)
- Connection history tracking
- Configuration file generation
- Modern responsive UI
- Native Netlink integration via wireguard-tools
