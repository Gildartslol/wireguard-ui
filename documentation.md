# WireGuard Management Dashboard - Documentation

## Project Overview

A web-based administration interface for managing WireGuard VPN connections on a pentesting jumphost. The system monitors Teltonika routers deployed at client sites that connect back via WireGuard tunnels.

**Purpose**: Centralized monitoring and management of WireGuard peer connections for pentesting infrastructure.

## Key Features

- **Real-time Connection Monitoring**: Display active WireGuard connections with status
- **Peer Management**: Add, remove, and manage WireGuard peers
- **Configuration Generator**: Create peer config files for deployment
- **Connection History**: Track peer connection/disconnection events
- **User Authentication**: Secure access with username/password
- **Modern Dashboard UI**: Clean, responsive interface with status indicators

---

## Architecture

```
┌─────────────────┐
│ Client Routers  │
│  (Teltonika)    │
└────────┬────────┘
         │ WireGuard
         │ Tunnels
         ▼
┌─────────────────────────────────────┐
│      Jumphost Server                │
│  ┌───────────────────────────────┐  │
│  │  WireGuard Interface (wg0)    │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │  Flask Backend                │  │
│  │  - Native Netlink access      │  │
│  │  - Query WireGuard devices    │  │
│  │  - Manage configurations      │  │
│  │  - Authentication             │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │  SQLite/PostgreSQL Database   │  │
│  │  - Users                      │  │
│  │  - Connection history         │  │
│  │  - Peer metadata              │  │
│  └───────────────────────────────┘  │
│                                      │
│  ┌───────────────────────────────┐  │
│  │  Web UI (Frontend)            │  │
│  │  - Dashboard view             │  │
│  │  - Peer management            │  │
│  │  - Config generator           │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐
  │   Browser    │
  │ (Local Access)│
  └──────────────┘
```

---

## Technology Stack

### Backend
- **Framework**: Flask (v3.x) - Lightweight, perfect for this use case
- **Authentication**: Flask-Login + Werkzeug (password hashing)
- **Database ORM**: SQLAlchemy
- **API**: RESTful endpoints
- **WireGuard Integration**: wireguard-tools (native Netlink API)

### Database
- **Primary Choice**: SQLite (simple, no configuration needed)
- **Alternative**: PostgreSQL (if scalability needed)

### Frontend
- **Framework**: Vue.js 3 with Vite
- **UI Library**: Tailwind CSS + DaisyUI components
- **HTTP Client**: Axios
- **Charts**: Chart.js (for connection history visualization)

### Additional Tools
- **Process Management**: systemd or supervisor
- **Reverse Proxy**: nginx (optional, for SSL/production)
- **Config Generation**: Python jinja2 templates

---

## Prerequisites

### System Requirements
- Linux server with WireGuard installed
- Python 3.9+
- Root access or NET_ADMIN capability (for Netlink/WireGuard management)
- Node.js 18+ and npm (for frontend build)
- WireGuard kernel module loaded

### WireGuard Setup
```bash
# Ensure WireGuard is installed
wg version

# Verify you can run wg commands
sudo wg show
```

### Python Packages (to be installed)
```
Flask==3.0.0
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-CORS==4.0.0
python-dotenv==1.0.0
werkzeug==3.0.1
wireguard-tools>=0.5.0
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### Peers Table
```sql
CREATE TABLE peers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_key VARCHAR(44) UNIQUE NOT NULL,
    name VARCHAR(100),
    allowed_ips TEXT,
    endpoint VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);
```

### Connection History Table
```sql
CREATE TABLE connection_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_id INTEGER REFERENCES peers(id),
    public_key VARCHAR(44) NOT NULL,
    status VARCHAR(20), -- 'connected', 'disconnected'
    endpoint VARCHAR(100),
    latest_handshake TIMESTAMP,
    transfer_rx BIGINT,
    transfer_tx BIGINT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Step-by-Step Implementation Plan

### Phase 1: Project Setup (Day 1)

#### 1.1 Create Project Structure
```bash
wireguard-ui/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication logic
│   ├── wg_manager.py       # WireGuard operations
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py         # Login/logout routes
│   │   ├── dashboard.py    # Dashboard API
│   │   └── peers.py        # Peer management API
│   ├── templates/          # Config templates
│   │   └── peer.conf.j2
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/
│       ├── views/
│       │   ├── Login.vue
│       │   ├── Dashboard.vue
│       │   ├── Peers.vue
│       │   └── History.vue
│       ├── components/
│       │   ├── PeerCard.vue
│       │   ├── ConnectionChart.vue
│       │   └── ConfigGenerator.vue
│       └── services/
│           └── api.js
├── configs/                # Generated peer configs
├── documentation.md
└── README.md
```

#### 1.2 Initialize Backend
```bash
cd wireguard-ui
mkdir -p backend/routes backend/templates
cd backend
python3 -m venv venv
source venv/bin/activate
pip install Flask Flask-Login Flask-SQLAlchemy Flask-CORS python-dotenv werkzeug wireguard-tools
pip freeze > requirements.txt
```

#### 1.3 Initialize Frontend
```bash
cd ../frontend
npm create vite@latest . -- --template vue
npm install
npm install vue-router axios tailwindcss daisyui chart.js vue-chartjs
npx tailwindcss init
```

#### 1.4 Setup Development Permissions
```bash
# For development, grant NET_ADMIN capability to Python virtualenv
cd backend
sudo setcap cap_net_admin+ep venv/bin/python

# Verify it's set correctly
getcap venv/bin/python
# Should output: venv/bin/python cap_net_admin+ep

# Now you can run Flask without sudo:
source venv/bin/activate
python app.py

# Alternative: Run with sudo (simpler but less secure)
# sudo venv/bin/python app.py
```

### Phase 2: Backend Development (Days 2-4)

#### 2.1 Database Models (models.py)
- Create User model with password hashing
- Create Peer model for WireGuard peer metadata
- Create ConnectionHistory model for tracking connections
- Initialize SQLAlchemy with SQLite

#### 2.2 WireGuard Manager (wg_manager.py)
```python
from wireguard_tools import WireguardDevice, WireguardKey, WireguardConfig
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class WireGuardManager:
    def __init__(self, interface="wg0"):
        self.interface = interface

    def get_active_peers(self) -> List[Dict]:
        """Get list of currently connected peers with real-time data"""
        device = WireguardDevice.get(self.interface)
        config = device.get_config()

        peers = []
        for peer in config.peers:
            peer_data = {
                'public_key': peer.public_key,
                'endpoint': f"{peer.endpoint_host}:{peer.endpoint_port}" if peer.endpoint_host else None,
                'allowed_ips': [str(ip) for ip in peer.allowed_ips],
                'latest_handshake': peer.last_handshake_time,
                'transfer_rx': peer.receive_bytes,
                'transfer_tx': peer.transmit_bytes,
                'persistent_keepalive': peer.persistent_keepalive,
                'connected': self._is_connected(peer.last_handshake_time)
            }
            peers.append(peer_data)

        return peers

    def _is_connected(self, handshake_time: Optional[datetime]) -> bool:
        """Consider connected if handshake within 3 minutes"""
        if not handshake_time:
            return False
        return datetime.now() - handshake_time < timedelta(minutes=3)

    def add_peer(self, public_key: str, allowed_ips: List[str],
                 endpoint: Optional[str] = None,
                 preshared_key: Optional[str] = None):
        """Add new peer to WireGuard interface"""
        device = WireguardDevice.get(self.interface)
        config = device.get_config()

        # Create new peer configuration
        from wireguard_tools import WireguardPeer
        new_peer = WireguardPeer(
            public_key=public_key,
            allowed_ips=allowed_ips,
            preshared_key=preshared_key
        )

        config.peers.append(new_peer)
        device.set_config(config)

    def remove_peer(self, public_key: str):
        """Remove peer from WireGuard interface"""
        device = WireguardDevice.get(self.interface)
        config = device.get_config()

        config.peers = [p for p in config.peers if p.public_key != public_key]
        device.set_config(config)

    def generate_keypair(self) -> Dict[str, str]:
        """Generate new WireGuard key pair"""
        private_key = WireguardKey.generate()
        public_key = private_key.public_key()

        return {
            'private_key': str(private_key),
            'public_key': str(public_key)
        }

    def generate_peer_config(self, peer_name: str, private_key: str,
                           server_public_key: str, endpoint: str,
                           allowed_ips: List[str], address: str) -> str:
        """Generate peer .conf file content"""
        config = f"""[Interface]
PrivateKey = {private_key}
Address = {address}
DNS = 1.1.1.1

[Peer]
PublicKey = {server_public_key}
Endpoint = {endpoint}
AllowedIPs = {', '.join(allowed_ips)}
PersistentKeepalive = 25
"""
        return config
```

Key implementation details:
- Uses **wireguard-tools** library for native Netlink API access
- Direct kernel communication (no subprocess overhead)
- Type-safe Python objects for WireGuard entities
- Automatic timestamp parsing and connection status detection
- Handle errors gracefully (device not found, permission denied)
- Log all WireGuard operations
- **Requires root/sudo** to access Netlink interface

#### 2.3 Authentication System (auth.py)
- Implement Flask-Login user loader
- Create login/logout functions
- Password hashing with Werkzeug
- Session management
- @login_required decorator for protected routes

#### 2.4 API Routes

**auth.py routes:**
- POST `/api/auth/login` - Authenticate user
- POST `/api/auth/logout` - End session
- GET `/api/auth/check` - Check authentication status

**dashboard.py routes:**
- GET `/api/dashboard/stats` - Get overview statistics
- GET `/api/dashboard/peers` - Get active peer connections
- GET `/api/dashboard/history` - Get connection history

**peers.py routes:**
- GET `/api/peers` - List all peers
- POST `/api/peers` - Add new peer
- GET `/api/peers/<peer_id>` - Get peer details (peer_id is UUID)
- PUT `/api/peers/<peer_id>` - Update peer
- DELETE `/api/peers/<peer_id>` - Remove peer (peer_id is UUID)
- GET `/api/peers/<peer_id>/config` - Generate config file (peer_id is UUID)
- POST `/api/peers/generate-keys` - Generate new keypair

#### 2.5 Configuration Management (config.py)
```python
# Settings to configure:
- SECRET_KEY (Flask sessions)
- DATABASE_URI
- WG_INTERFACE (default: wg0)
- WG_CONFIG_PATH
- SUDO_PASSWORD (if needed)
- POLLING_INTERVAL (for connection monitoring)
```

#### 2.6 Main Application (app.py)
- Initialize Flask app
- Setup CORS for frontend
- Register blueprints (auth, dashboard, peers)
- Initialize database
- Create default admin user on first run
- Background task to record connection history

### Phase 3: Frontend Development (Days 5-7)

#### 3.1 Setup Router and Layout
- Configure Vue Router with routes:
  - `/login` - Login page
  - `/dashboard` - Main dashboard (protected)
  - `/peers` - Peer management (protected)
  - `/history` - Connection history (protected)
- Create auth guard for protected routes
- Design main layout with navigation

#### 3.2 Authentication (Login.vue)
- Login form (username/password)
- API integration with backend
- Store JWT/session token
- Redirect to dashboard on success
- Error handling for failed login

#### 3.3 Dashboard View (Dashboard.vue)
Components to build:
- Stats cards (total peers, active connections, total traffic)
- Active connections table with:
  - Peer name/public key
  - Endpoint IP
  - Last handshake time
  - Transfer stats (RX/TX)
  - Status indicator (online/offline)
- Auto-refresh every 10 seconds
- Real-time updates using polling

#### 3.4 Peer Management (Peers.vue)
Features:
- List all configured peers
- Add peer form:
  - Name/description
  - Allowed IPs
  - Optional: pre-shared key
- Generate keypair button
- Remove peer with confirmation
- Download config file button
- Search/filter peers

#### 3.5 Config Generator Component
- Form to input peer details
- Generate QR code for mobile devices
- Download .conf file
- Copy to clipboard functionality
- Preview generated config

#### 3.6 Connection History (History.vue)
- Table view of historical connections
- Filters:
  - Date range
  - Peer
  - Status (connected/disconnected)
- Chart showing connections over time
- Export to CSV functionality

#### 3.7 UI/UX Polish
- Responsive design (mobile-friendly)
- Loading states and spinners
- Toast notifications for actions
- Error messages
- Confirm dialogs for destructive actions
- Dark mode support (optional)

### Phase 4: Integration & Testing (Day 8)

#### 4.1 API Integration Testing
- Test all frontend-backend API calls
- Handle error responses gracefully
- Test authentication flow
- Test CORS configuration

#### 4.2 WireGuard Integration Testing
- Test with real WireGuard interface
- Verify `wg show` parsing accuracy
- Test peer addition/removal
- Test config generation
- Verify sudo permissions work correctly

#### 4.3 Database Testing
- Test user creation and authentication
- Test peer CRUD operations
- Test connection history recording
- Test database migrations (if applicable)

#### 4.4 Security Testing
- Test authentication bypass attempts
- Verify password hashing
- Test SQL injection (should be prevented by SQLAlchemy)
- Test CSRF protection
- Review sudo command execution security

### Phase 5: Deployment Preparation (Day 9)

#### 5.1 Build Frontend for Production
```bash
cd frontend
npm run build
# This creates frontend/dist/ with optimized files
```

#### 5.2 Configure Flask to Serve Frontend
```python
# In app.py, serve Vue build:
@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend/dist', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend/dist', path)
```

#### 5.3 Create Systemd Service
Create `/etc/systemd/system/wg-dashboard.service`:
```ini
[Unit]
Description=WireGuard Dashboard
After=network.target wg-quick@wg0.service

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/wireguard-ui/backend
Environment="PATH=/path/to/wireguard-ui/backend/venv/bin"
ExecStart=/path/to/wireguard-ui/backend/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wg-dashboard
sudo systemctl start wg-dashboard
```

#### 5.4 Setup Nginx Reverse Proxy (Optional)
```nginx
server {
    listen 80;
    server_name your-jumphost.local;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 5.5 SSL/TLS Configuration (Recommended)
- Generate self-signed certificate OR
- Use Let's Encrypt if publicly accessible
- Configure nginx for HTTPS

### Phase 6: Final Configuration (Day 10)

#### 6.1 Create Default Admin User
```bash
cd backend
source venv/bin/activate
python create_admin.py
# Script to create initial admin account
```

#### 6.2 Configure Netlink Access Permissions
```bash
# Option 1: Run Flask app as root (simpler, used by systemd service)
# Already configured in systemd service (User=root)

# Option 2: Use Linux capabilities (more secure for development)
# Grant NET_ADMIN capability to Python interpreter:
sudo setcap cap_net_admin+ep /path/to/wireguard-ui/backend/venv/bin/python

# Verify capability is set:
getcap /path/to/wireguard-ui/backend/venv/bin/python
# Should show: cap_net_admin+ep

# Note: wireguard-tools uses Netlink API which requires NET_ADMIN capability
# or root access to query/modify WireGuard interfaces
```

#### 6.3 Setup Connection History Cron Job
```python
# Background task in Flask or cron job:
# Every 5 minutes, run:
# - Parse wg show
# - Compare with previous state
# - Record changes in connection_history table
```

#### 6.4 Environment Variables
Create `backend/.env`:
```
FLASK_ENV=production
SECRET_KEY=<generate-random-secret>
DATABASE_URI=sqlite:///wg_dashboard.db
WG_INTERFACE=wg0
WG_CONFIG_PATH=/etc/wireguard/wg0.conf
```

#### 6.5 Final Testing Checklist
- [ ] Can log in with admin credentials
- [ ] Dashboard shows active connections
- [ ] Can add a new peer
- [ ] Generated config file is valid
- [ ] Can remove a peer
- [ ] Connection history is recording
- [ ] All API endpoints respond correctly
- [ ] Frontend handles errors gracefully
- [ ] Service starts on boot
- [ ] No permission errors in logs

---

## Security Considerations

### 1. Authentication
- Use strong passwords (enforce policy)
- Implement rate limiting on login attempts
- Use secure session cookies (httpOnly, secure flags)
- Consider implementing 2FA for production

### 2. Authorization
- All WireGuard management requires authentication
- Validate all user inputs
- Sanitize inputs before passing to shell commands
- Never expose raw `wg` command execution to frontend

### 3. Netlink Access & Permissions
```python
# IMPORTANT: wireguard-tools requires root access for Netlink API
# Flask app must run as root OR use capability-based permissions

# Option 1: Run Flask as root (simpler but less secure)
# Option 2: Use Linux capabilities (more secure):
#   sudo setcap cap_net_admin+ep /path/to/venv/bin/python

# Always validate inputs before WireGuard operations
def validate_public_key(key: str) -> bool:
    """Ensure public key is valid base64, 44 characters"""
    import re
    return bool(re.match(r'^[A-Za-z0-9+/]{43}=$', key))

# Example secure peer addition:
if not validate_public_key(public_key):
    raise ValueError("Invalid public key format")

device = WireguardDevice.get(interface)
# Netlink communication happens here, no shell execution
```

### 4. Network Security
- Bind Flask to 127.0.0.1 only (use nginx proxy)
- Implement IP allowlisting if needed
- Use HTTPS in production
- Set proper CORS origins (not '*' in production)

### 5. Database Security
- Use parameterized queries (SQLAlchemy ORM handles this)
- Regular backups of SQLite database
- Restrict file permissions on database file (600)

### 6. Logging
- Log all authentication attempts
- Log all WireGuard configuration changes
- Log all peer additions/removals
- Include timestamp and user for audit trail
- Rotate logs regularly

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Frontend built for production
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] Admin user created
- [ ] WireGuard permissions configured
- [ ] Systemd service configured

### Post-Deployment
- [ ] Service running and accessible
- [ ] Can log in via web interface
- [ ] Dashboard displays correct data
- [ ] Can perform peer operations
- [ ] Logs are being written
- [ ] Auto-restart on failure working
- [ ] Backup strategy implemented

### Monitoring
- [ ] Setup log monitoring
- [ ] Monitor service status
- [ ] Monitor disk space (logs, database)
- [ ] Monitor WireGuard interface status
- [ ] Alert on service failures

---

## Maintenance & Operations

### Regular Tasks
1. **Database Backups**
   ```bash
   # Backup SQLite database daily
   cp backend/wg_dashboard.db backups/wg_dashboard_$(date +%Y%m%d).db
   ```

2. **Log Rotation**
   ```bash
   # Configure logrotate for application logs
   /var/log/wg-dashboard/*.log {
       daily
       rotate 7
       compress
       delaycompress
   }
   ```

3. **Update Dependencies**
   ```bash
   # Monthly security updates
   cd backend
   source venv/bin/activate
   pip list --outdated
   pip install --upgrade <package>
   ```

### Troubleshooting

**Issue: Dashboard not showing peers**
- Check: `sudo wg show` works manually
- Check: Flask app has Netlink access (running as root or has cap_net_admin)
- Check: WG_INTERFACE environment variable is correct
- Check: Application logs for "Permission denied" or Netlink errors
- Test: Run `python -c "from wireguard_tools import WireguardDevice; print(WireguardDevice.get('wg0'))"` as Flask user

**Issue: Can't add/remove peers**
- Check: Flask process has NET_ADMIN capability or running as root
- Check: Netlink socket access permissions
- Check: WireGuard kernel module is loaded (`lsmod | grep wireguard`)
- Check: SELinux/AppArmor policies allow Netlink operations
- Test: Verify capability with `getcap /path/to/venv/bin/python`

**Issue: Permission denied errors**
- Most common cause: Flask not running with sufficient privileges
- Solution 1: Ensure systemd service has `User=root`
- Solution 2: Set NET_ADMIN capability on Python binary
- Solution 3: Check if development server was started with `sudo`

**Issue: Frontend not loading**
- Check: Frontend built successfully (`frontend/dist/` exists)
- Check: Flask serving static files correctly
- Check: Browser console for errors
- Check: API endpoints returning data

**Issue: Login failing**
- Check: Database file exists and is readable
- Check: Secret key is configured
- Check: Password hash is correct
- Check: Session cookies are being set

---

## Future Enhancements

### Phase 2 Features (Optional)
1. **Multi-Interface Support**: Manage multiple WireGuard interfaces
2. **Bulk Operations**: Add/remove multiple peers at once
3. **Config Templates**: Pre-defined templates for different client types
4. **Email Notifications**: Alert on new connections or errors
5. **API Keys**: For automation/integration with other tools
6. **Bandwidth Monitoring**: Track data usage per peer over time
7. **Peer Groups**: Organize peers by client/project
8. **Config Versioning**: Track changes to WireGuard configurations
9. **WebSocket Updates**: Real-time dashboard updates (no polling)
10. **Mobile App**: Native iOS/Android app for management

### Advanced Features
- **Terraform Integration**: Auto-configure new WireGuard endpoints
- **Ansible Playbooks**: Deploy configurations to multiple servers
- **Prometheus Metrics**: Export metrics for monitoring stack
- **LDAP/SSO**: Enterprise authentication integration
- **Multi-tenancy**: Support multiple teams/organizations

---

## Resources & References

### WireGuard Documentation
- [WireGuard Quick Start](https://www.wireguard.com/quickstart/)
- [wg(8) Man Page](https://git.zx2c4.com/wireguard-tools/about/src/man/wg.8)
- [wg-quick(8) Man Page](https://git.zx2c4.com/wireguard-tools/about/src/man/wg-quick.8)

### Flask Documentation
- [Flask Official Docs](https://flask.palletsprojects.com/)
- [Flask-Login](https://flask-login.readthedocs.io/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)

### Vue.js Resources
- [Vue 3 Documentation](https://vuejs.org/)
- [Vue Router](https://router.vuejs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [DaisyUI Components](https://daisyui.com/)

### Security Best Practices
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)

---

## Support & Contribution

### Getting Help
- Review logs in `/var/log/syslog` or journalctl
- Check Flask application logs
- Enable debug mode for detailed errors (development only)

### Contributing
- Follow Python PEP 8 style guide
- Add tests for new features
- Update documentation for changes
- Create feature branches for development

---

## License & Disclaimer

This is an internal tool for authorized pentesting infrastructure management. Ensure proper authorization and compliance with security policies when deploying.

**Security Note**: This tool requires root/sudo access and manages network configurations. Only deploy on trusted, secured systems with proper access controls.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Estimated Implementation Time**: 10 days (single developer)
