# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A production-ready web-based administration interface for managing WireGuard VPN connections. Built to monitor Teltonika routers at client sites that connect via WireGuard tunnels. The system uses subprocess calls to the `wg` command-line tool for WireGuard management.

## Technology Stack

**Backend**:
- Flask 3.x with Flask-Login, Flask-SQLAlchemy, Flask-CORS
- SQLite database (PostgreSQL compatible)
- subprocess integration with `wg` command-line tool
- Werkzeug password hashing

**Frontend**:
- Vue.js 3 with Composition API
- Vite build tool
- Tailwind CSS + DaisyUI
- Vue Router, Axios, Chart.js

**Requirements**:
- Linux server with WireGuard kernel module
- Python 3.9+
- Node.js 18+
- Dedicated `wireguard` system user with sudo access to `wg` commands

## Development Commands

### First-Time Setup

**Backend**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your WireGuard settings

# Setup wireguard system user and sudo permissions
sudo bash ../deployment/setup_wireguard_user.sh

# Initialize database
python -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all()"

# Create admin user
python create_admin.py
```

**Frontend**:
```bash
cd frontend
npm install
```

### Development

**Backend** (terminal 1):
```bash
cd backend
source venv/bin/activate
python app.py
# Runs on http://localhost:5000
```

**Frontend** (terminal 2):
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173, proxies API to :5000
```

### Mock Mode (Development without WireGuard)

Run the application without WireGuard installed using mock data:

**Option 1: Direct Python (Development)**
```bash
cd backend
source venv/bin/activate
export WG_MOCK_MODE=true
export WG_MOCK_SCENARIO=mixed  # Options: empty, connected, mixed, disconnected
python app.py
```

**Option 2: Via .env file (Recommended for Systemd)**

Edit `backend/.env` and add:
```
WG_MOCK_MODE=true
WG_MOCK_SCENARIO=mixed
```

Then run normally:
```bash
# Direct Python
python app.py

# Or via systemd service
sudo systemctl restart wg-dashboard
```

**IMPORTANT**: If using systemd service, you **must** use the `.env` file method. Environment variables exported in your shell do not persist to systemd services.

**Available Scenarios**:
- `empty` - No peers configured
- `connected` - All peers actively connected
- `mixed` - Some connected, some disconnected (default)
- `disconnected` - All peers configured but disconnected

Mock data files: `backend/tests/mock_data/`

### Production Build

```bash
cd frontend
npm run build
# Outputs to frontend/dist/

cd ../backend
source venv/bin/activate
python app.py
# Flask serves frontend/dist/ static files at root
```

### Testing

```bash
# Backend tests
cd backend
source venv/bin/activate
python -m pytest tests/

# Frontend tests
cd frontend
npm run test
```

### Production Deployment

```bash
# Automated setup script (Ubuntu only)
sudo bash deployment/setup.sh

# Manual systemd setup
sudo cp deployment/wg-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wg-dashboard
sudo systemctl start wg-dashboard
sudo systemctl status wg-dashboard

# View logs
sudo journalctl -u wg-dashboard -f
```

## Architecture

### WireGuard Integration (wg_manager.py)

Uses subprocess calls to the `wg` command-line tool for WireGuard management. **Critical**: Requires sudo access configured via `/etc/sudoers.d/wireguard-ui`.

**Key Methods**:
- `get_active_peers()`: Parses `wg show <interface> dump` output for real-time peer data
- `add_peer(public_key, allowed_ips, endpoint=None, preshared_key=None)`: Executes `sudo wg set` to add peer
- `remove_peer(public_key)`: Executes `sudo wg set <interface> peer <key> remove`
- `update_peer(public_key, allowed_ips=None, endpoint=None)`: Executes `sudo wg set` to update peer
- `generate_keypair()`: Calls `wg genkey` and `wg pubkey` to generate keys
- `generate_peer_config(...)`: Generate client .conf file (string formatting)
- `get_stats()`: Aggregate statistics from parsed peer data
- `get_interface_info()`: Parses `wg show <interface>` for interface metadata

**Implementation Notes**:
- Uses `wg show <interface> dump` for machine-readable tab-separated output
- Parses dump format: `public-key preshared-key endpoint allowed-ips handshake-sec rx-bytes tx-bytes keepalive`
- Peer is considered "connected" if handshake occurred within last 3 minutes (backend/wg_manager.py:118-130)
- Validates public keys (44 char base64 with trailing =)
- All subprocess calls have 10-second timeout
- Uses `sudo -n` (non-interactive) to ensure no password prompts
- All exceptions are logged and re-raised for route handlers to catch

### Database Models (models.py)

**User**:
- `id`, `username`, `password_hash`, `created_at`, `last_login`
- Password hashing via Werkzeug

**Peer**:
- `id`, `public_key` (unique, 44 chars), `name`, `allowed_ips`, `description`, `created_at`
- Stored in database, synchronized with WireGuard kernel state

**ConnectionHistory**:
- `id`, `peer_id` (FK), `timestamp`, `event_type` (connected/disconnected), `endpoint`, `latest_handshake`, `transfer_rx`, `transfer_tx`
- Used for historical tracking and bandwidth visualization

### API Routes

**Authentication** (routes/auth.py):
- `POST /api/auth/login`: Session-based auth, returns user info
- `POST /api/auth/logout`: Destroy session
- `GET /api/auth/check`: Verify session validity

**Dashboard** (routes/dashboard.py):
- `GET /api/dashboard/stats`: Aggregate stats (total peers, connected, bandwidth)
- `GET /api/dashboard/peers`: Real-time peer list with status
- `GET /api/dashboard/history?timerange={hour|day|week}`: Historical connection data

**Peers** (routes/peers.py):
- `GET /api/peers`: List all configured peers (DB + WireGuard state merge)
- `POST /api/peers`: Add peer (creates in DB, adds to WireGuard)
- `DELETE /api/peers/<public_key>`: Remove peer (removes from both)
- `GET /api/peers/<public_key>/config`: Download .conf file
- `POST /api/peers/generate`: Generate new keypair

All routes except `/api/auth/login` require `@login_required` decorator.

### Frontend Architecture

**Views**:
- `Login.vue`: Authentication form
- `Dashboard.vue`: Real-time overview, auto-refreshes every 10 seconds
- `Peers.vue`: Peer management (add, remove, configure)
- `History.vue`: Connection history with time range filter

**Components**:
- `PeerCard.vue`: Individual peer status display
- `ConfigGenerator.vue`: Generate and download peer configs

**Services**:
- `api.js`: Axios wrapper for all API calls, handles auth errors

**Router** (router/index.js):
- Vue Router with navigation guards
- Redirects unauthenticated users to `/login`
- Route guards check session validity via `/api/auth/check`

### Configuration

**Backend .env**:
```env
FLASK_ENV=production
SECRET_KEY=<secrets.token_urlsafe(32)>
DATABASE_URI=sqlite:///wg_dashboard.db
WG_INTERFACE=wg0
WG_SERVER_ADDRESS=10.0.0.1/24
WG_SERVER_PORT=51820
WG_SERVER_PUBLIC_KEY=<your-server-public-key>
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

**Frontend** (vite.config.js):
- Dev server on port 5173
- Proxies `/api/*` to `http://localhost:5000` in development
- Production build outputs to `frontend/dist/`

## Security Critical Points

1. **Dedicated System User**: Application runs as `wireguard` system user (not root) with limited sudo permissions

2. **Sudoers Configuration**: Only specific WireGuard commands allowed via `/etc/sudoers.d/wireguard-ui`:
   - `sudo wg show [interface] [dump]` - Read WireGuard state
   - `sudo wg set <interface> peer ...` - Modify peers
   - `wg genkey`, `wg pubkey`, `wg genpsk` - Key generation (no sudo needed)

3. **Command Injection Prevention**: All subprocess calls use list-based arguments (not shell=True). Public keys and IPs validated before passing to `wg` commands.

4. **Public key validation**: All peer public keys validated against regex `^[A-Za-z0-9+/]{43}=$` before WireGuard operations (backend/wg_manager.py:408-418)

5. **Authentication**: Flask-Login sessions with httpOnly cookies. Passwords hashed with Werkzeug.

6. **CORS**: Configured for localhost:5173 in development. Update `config.py` for production origins.

7. **Production**: Bind Flask to `0.0.0.0:5000`, use nginx reverse proxy with HTTPS for external access.

## Common Development Scenarios

**Adding a peer property**:
1. Update `Peer` model in `models.py`, add column
2. Create migration or recreate database (dev: delete `wg_dashboard.db`, run `db.create_all()`)
3. Update peer creation in `routes/peers.py` POST endpoint
4. Update frontend form in `Peers.vue` and display in `PeerCard.vue`

**Debugging WireGuard connection**:
1. Check WireGuard is running: `sudo wg show wg0`
2. Verify wireguard user can run wg commands: `sudo -u wireguard sudo -n wg show`
3. Test subprocess access directly:
   ```bash
   cd backend
   source venv/bin/activate
   python -c "from wg_manager import WireGuardManager; wg = WireGuardManager('wg0'); print(wg.get_active_peers())"
   ```
4. Check backend logs: `sudo journalctl -u wg-dashboard -f`
5. Verify sudoers file: `sudo visudo -c -f /etc/sudoers.d/wireguard-ui`

**Handling wg show output parsing**:
- Uses `wg show dump` format: tab-separated values with predictable column order
- Handles `(none)` values for missing endpoint/preshared-key
- Handshake time is seconds since last handshake (0 = never)
- Transfer values are cumulative bytes (not human-readable format)

**Adding a new dashboard statistic**:
1. Update `get_stats()` in `wg_manager.py` or compute in `routes/dashboard.py`
2. Return new stat in `/api/dashboard/stats` response
3. Update `Dashboard.vue` to fetch and display

## Critical Implementation Notes

- WireGuard public keys are 44 characters, base64-encoded, ending with `=`
- Peer is "connected" if handshake within last 3 minutes (configurable in `wg_manager.py:109`)
- Transfer RX/TX are cumulative bytes since peer was added (kernel tracks this)
- Latest handshake timestamp is UTC datetime from kernel
- Generated peer configs must include Interface (PrivateKey, Address, DNS) and Peer (PublicKey, Endpoint, AllowedIPs) sections
- Connection history should be populated by background task/cron (not yet implemented)

## Mock Mode Architecture

The WireGuard manager supports a mock mode for development and testing without WireGuard:

- **Activation**: Set `WG_MOCK_MODE=true` environment variable
- **Mock Data**: Reads from `backend/tests/mock_data/wg_dump_<scenario>.txt`
- **Command Routing**: `_execute_command()` method routes to mock or real subprocess
- **Parsing**: Uses same parsing logic as production (tests the full flow)
- **Key Generation**: Generates valid base64-encoded mock keys in mock mode

**Use Cases**:
- Frontend development on non-Linux machines
- Testing UI without affecting real WireGuard config
- CI/CD testing without system dependencies
- Demonstrating the application

## Troubleshooting

**"Permission denied" or "sudo: a password is required"**:
- Ensure wireguard user exists: `id wireguard`
- Check sudoers file: `sudo cat /etc/sudoers.d/wireguard-ui`
- Validate sudoers syntax: `sudo visudo -c -f /etc/sudoers.d/wireguard-ui`
- Test sudo access: `sudo -u wireguard sudo -n wg show`
- Systemd service runs as `wireguard` user (see deployment/wg-dashboard.service)

**Peers not showing in dashboard**:
- Verify `WG_INTERFACE=wg0` in `.env` matches actual interface (`sudo wg show`)
- Check backend logs for subprocess errors: `sudo journalctl -u wg-dashboard -f`
- Test wg command access: `sudo -u wireguard sudo -n wg show wg0 dump`
- Verify wireguard user has correct permissions

**Frontend can't connect to backend**:
- Backend running: `sudo systemctl status wg-dashboard` or check http://localhost:5000/api/health
- CORS: Check `config.py` allows frontend origin (localhost:5173 for dev)
- Browser console: Check for auth redirects or CORS errors

**Database locked errors**:
- SQLite doesn't handle concurrent writes well
- Use PostgreSQL in production: change `DATABASE_URI` in `.env`
- Ensure only one Flask process is running

**Infinite redirect loop on auth**:
- Fixed in commit 7cb33dd
- Ensure `/api/auth/check` endpoint returns correct session status
- Check browser isn't blocking cookies

**File permission errors**:
- Ensure wireguard user owns application files: `sudo chown -R wireguard:wireguard /opt/wireguard-ui`
- Check database file permissions: `ls -la backend/wg_dashboard.db`

**Mock mode not working**:
- **If using systemd**: Verify variables are in `.env` file, not just exported in shell
- Check `.env` file: `cat backend/.env | grep WG_MOCK`
- Check mock data files exist: `ls backend/tests/mock_data/`
- Check logs for "MOCK MODE" message: `sudo journalctl -u wg-dashboard -n 20 | grep MOCK`
- Verify scenario file exists: `backend/tests/mock_data/wg_dump_<scenario>.txt`
- Remember: Shell exports don't work with systemd - use `.env` file

## Recent Changes

- **Mock mode**: Development mode using mock WireGuard data for testing without WireGuard installed
- **Subprocess integration**: Uses `wg show` command parsing instead of Python library for better reliability
- **Dedicated system user**: Application runs as `wireguard` user with limited sudo privileges
- **Sudoers configuration**: Automated setup script creates `/etc/sudoers.d/wireguard-ui` with minimal permissions
- **Auth fix**: Resolved infinite redirect issue (commit 7cb33dd)
- **Production ready**: Systemd service, automated deployment script, secure user isolation
