# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A web-based administration interface for managing WireGuard VPN connections on a pentesting jumphost. The system monitors Teltonika routers deployed at client sites that connect back via WireGuard tunnels.

**Current Status**: This is a planning/documentation phase. The codebase structure has not yet been implemented. See `documentation.md` for the complete specification.

## Technology Stack

**Backend**:
- Flask 3.x with Flask-Login, Flask-SQLAlchemy, Flask-CORS
- SQLite database (or PostgreSQL for scalability)
- Python subprocess module for WireGuard integration
- Authentication via Werkzeug password hashing

**Frontend**:
- Vue.js 3 with Vite
- Tailwind CSS + DaisyUI components
- Axios for HTTP, Chart.js for visualizations

**System Requirements**:
- Linux server with WireGuard installed
- Python 3.9+
- Node.js 18+
- Root/sudo access for WireGuard management

## Project Structure

When implementing, use this structure:

```
wireguard-ui/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration management
│   ├── models.py           # SQLAlchemy database models
│   ├── auth.py             # Authentication logic
│   ├── wg_manager.py       # WireGuard command interface
│   ├── routes/
│   │   ├── auth.py         # Login/logout endpoints
│   │   ├── dashboard.py    # Dashboard API
│   │   └── peers.py        # Peer management API
│   ├── templates/
│   │   └── peer.conf.j2    # Jinja2 config template
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── views/          # Login, Dashboard, Peers, History
│   │   ├── components/     # PeerCard, ConnectionChart, ConfigGenerator
│   │   └── services/
│   │       └── api.js      # Axios API client
│   ├── package.json
│   └── vite.config.js
└── configs/                # Generated peer configurations
```

## Development Commands

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Backend Development
```bash
cd backend
source venv/bin/activate
python app.py              # Run development server
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Frontend Development
```bash
cd frontend
npm run dev               # Start Vite dev server
npm run build             # Build for production
npm run preview           # Preview production build
```

### Testing WireGuard Integration
```bash
sudo wg show              # Verify WireGuard is accessible
sudo wg show wg0          # Show specific interface
```

## Core Architecture Patterns

### WireGuard Manager (wg_manager.py)

The WireGuard manager is the critical integration layer. Key functions:

- `parse_wg_show()`: Parse output from `wg show` command into structured data
- `get_active_peers()`: Return list of currently connected peers with handshake info
- `add_peer(public_key, allowed_ips)`: Add peer to WireGuard interface
- `remove_peer(public_key)`: Remove peer from WireGuard interface
- `generate_keypair()`: Create new WireGuard public/private key pair
- `generate_peer_config(...)`: Generate peer .conf file using Jinja2 template

**Security Critical**: Always use `subprocess.run()` with `shell=False` and validate all inputs before passing to WireGuard commands. Never expose raw command execution to API endpoints.

### Database Models (models.py)

Three core models:

1. **User**: Authentication (username, password_hash, last_login)
2. **Peer**: WireGuard peer metadata (public_key, name, allowed_ips, description)
3. **ConnectionHistory**: Historical tracking (peer_id, status, endpoint, latest_handshake, transfer stats)

Use SQLAlchemy ORM for all database operations to prevent SQL injection.

### API Endpoints

**Authentication** (`routes/auth.py`):
- `POST /api/auth/login`: Authenticate user
- `POST /api/auth/logout`: End session
- `GET /api/auth/check`: Verify session status

**Dashboard** (`routes/dashboard.py`):
- `GET /api/dashboard/stats`: Overview statistics
- `GET /api/dashboard/peers`: Active connections with real-time data
- `GET /api/dashboard/history`: Connection history logs

**Peer Management** (`routes/peers.py`):
- `GET /api/peers`: List all configured peers
- `POST /api/peers`: Add new peer
- `DELETE /api/peers/<public_key>`: Remove peer
- `GET /api/peers/<public_key>/config`: Download peer config file
- `POST /api/peers/generate`: Generate new keypair

All routes except `/api/auth/login` require `@login_required` decorator.

### Frontend State Management

Use Vue 3 Composition API with reactive state:

- `api.js` service layer abstracts all backend calls
- Auto-refresh dashboard every 10 seconds for real-time updates
- Handle authentication state globally (store token/session)
- Implement route guards to redirect unauthenticated users to login

## Security Requirements

1. **Command Injection Prevention**: Validate all inputs before subprocess calls. Use allowlist for WireGuard commands.

2. **Authentication**:
   - Hash passwords with Werkzeug's `generate_password_hash`
   - Use Flask sessions with secure, httpOnly cookies
   - Implement rate limiting on login attempts

3. **Authorization**: All WireGuard operations require authenticated session

4. **Sudo Configuration**: Configure sudoers to allow Flask user to run specific WireGuard commands without password:
   ```
   flask-user ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/wg-quick
   ```

5. **Network**: Bind Flask to 127.0.0.1, use nginx reverse proxy for external access with HTTPS

6. **Logging**: Log all authentication attempts, peer additions/removals, and WireGuard config changes with timestamps and user attribution

## Configuration

Backend `.env` file:
```
FLASK_ENV=production
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
DATABASE_URI=sqlite:///wg_dashboard.db
WG_INTERFACE=wg0
WG_CONFIG_PATH=/etc/wireguard/wg0.conf
```

Frontend API configuration (src/services/api.js):
```javascript
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:5000/api'
```

## Deployment

### Production Build
```bash
# Build frontend
cd frontend
npm run build

# Flask will serve frontend/dist/ static files
```

### Systemd Service
Create `/etc/systemd/system/wg-dashboard.service` to run Flask app as daemon. Service must run as root or user with sudo access to WireGuard commands.

```bash
sudo systemctl enable wg-dashboard
sudo systemctl start wg-dashboard
sudo systemctl status wg-dashboard
```

## Common Development Scenarios

**Adding a new peer property**:
1. Update `Peer` model in `models.py`
2. Create database migration (or drop/recreate in development)
3. Update peer creation in `routes/peers.py`
4. Update frontend form in `Peers.vue`
5. Update peer display in `PeerCard.vue` component

**Changing WireGuard parsing logic**:
1. Test changes against `wg show` output manually first
2. Update `parse_wg_show()` in `wg_manager.py`
3. Verify dashboard still displays peer data correctly
4. Add error handling for malformed output

**Adding new dashboard statistic**:
1. Add calculation in `routes/dashboard.py` stats endpoint
2. Update frontend `Dashboard.vue` to display new stat
3. Update auto-refresh logic if real-time updates needed

## Important Implementation Notes

- WireGuard public keys are 44 characters (base64 encoded)
- Latest handshake timestamp indicates connection freshness (>2 minutes = likely disconnected)
- Transfer RX/TX are cumulative bytes since peer was added
- `wg show` output format is consistent but should be parsed defensively
- Generated peer configs must include: Interface section (PrivateKey, Address) and Peer section (PublicKey, Endpoint, AllowedIPs)
- Connection history recording should run as background task or cron job every 5 minutes

## Troubleshooting

**"Permission denied" on wg commands**: Verify sudo configuration allows Flask user to run `/usr/bin/wg` without password

**Peers not showing in dashboard**: Check that `WG_INTERFACE` environment variable matches actual interface name (run `sudo wg show` to verify)

**Frontend can't connect to backend**: Verify CORS configuration in Flask includes frontend origin, check that backend is running and accessible

**Database locked errors**: SQLite doesn't handle concurrent writes well; consider PostgreSQL for production if seeing lock errors
