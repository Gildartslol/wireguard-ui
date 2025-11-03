# Development Guide

This guide explains how to run the WireGuard UI in development mode vs production mode.

---

## Architecture Overview

### WireGuard as Source of Truth

The application follows a **WireGuard-first architecture** where:

- **WireGuard** is the single source of truth for:
  - Which peers are configured
  - Connection status (connected/disconnected)
  - Real-time transfer statistics (RX/TX bytes)
  - Endpoint information
  - Latest handshake timestamps

- **Database** provides enrichment metadata only:
  - Human-readable peer names
  - Client/organization grouping
  - Descriptions and notes
  - Historical tracking
  - Audit trail (who created what, when)

### How It Works

1. **All API endpoints query WireGuard first** via `wg show` commands
2. **Enrichment happens at runtime** by matching WireGuard peers with database entries by `public_key`
3. **Unknown peers are auto-created** - if a peer exists in WireGuard but not in database:
   - Automatically creates database entry with placeholder name
   - Assigns to "Unregistered Peers" system client
   - User can reassign to proper client via UI
4. **Orphaned entries are marked** - if database has peer not in WireGuard:
   - Shows with "⚠️ Not Configured" warning badge
   - Allows user to delete or investigate

### Benefits

✅ **Always accurate** - UI shows real WireGuard state, not stale database data
✅ **Flexible** - Can manually manage WireGuard via CLI if needed
✅ **Self-healing** - If database gets out of sync, still shows correct data
✅ **No dual maintenance** - WireGuard config is the only thing to manage
✅ **Future-proof** - Can migrate databases without touching WireGuard config

### Key Files

- `backend/routes/peer_utils.py` - Shared enrichment logic
- `backend/routes/peers.py` - `/api/peers` endpoint (queries WireGuard)
- `backend/routes/dashboard.py` - `/api/dashboard/peers` endpoint
- `backend/wg_manager.py` - WireGuard command wrapper

---

## Development Mode (Recommended for Development)

Use this mode when actively developing or testing changes. Provides instant hot-reload for both backend and frontend.

### Setup (One-time)

```bash
# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Running Development Mode

You need **two terminal windows**:

**Terminal 1 - Backend (Flask)**
```bash
cd backend
source venv/bin/activate

# For mock mode (no WireGuard required):
# Edit backend/.env and set:
#   WG_MOCK_MODE=true
#   WG_MOCK_SCENARIO=mixed
# Options for WG_MOCK_SCENARIO: empty, connected, mixed, disconnected

# Run Flask dev server
python3 app.py
```

**Important**: The app will display in the logs whether it's running in MOCK MODE or PRODUCTION MODE on startup. Look for:
```
🧪 MOCK MODE ENABLED
   Scenario: mixed
   Database: sqlite:///wg_dashboard_mock.db
```
or
```
🔴 PRODUCTION MODE
   Database: sqlite:///wg_dashboard.db
```

Flask will run on `http://localhost:5000` (but you won't access this directly)

**Note:** Mock mode automatically switches to `wg_dashboard_mock.db`. If the mock database doesn't exist, create it with:
```bash
# WG_MOCK_SCENARIO controls which scenario data to load (empty, connected, mixed, disconnected)
# The script always creates wg_dashboard_mock.db regardless of WG_MOCK_MODE
WG_MOCK_SCENARIO=mixed python3 create_mock_db.py
```

**Mock Database Credentials:**
- Username: `admin`
- Password: `admin`

(These are hardcoded in the mock database for easy testing)

**Terminal 2 - Frontend (Vite)**
```bash
cd frontend
npm run dev
```

Vite dev server will run on `http://localhost:5173`

### Access the Application

Open your browser to: **http://localhost:5173**

The frontend (Vite) will proxy API requests to the backend (Flask) automatically.

### Making Changes

- **Backend changes** (Python files): Flask auto-reloads, just refresh browser
- **Frontend changes** (Vue files): Vite hot-reloads automatically, no refresh needed
- **No build or restart required!**

---

## Production Mode (Systemd Service)

Use this mode for deployment on a server. The application runs as a single systemd service.

### How It Works

- Flask serves both the API **and** the pre-built frontend static files
- Runs as background service under the `wireguard` user
- No separate frontend dev server

### Running Production Mode

```bash
# Start the service
sudo systemctl start wg-dashboard

# Check status
sudo systemctl status wg-dashboard

# View logs
sudo journalctl -u wg-dashboard -f

# Stop the service
sudo systemctl stop wg-dashboard

# Restart after changes
sudo systemctl restart wg-dashboard
```

### Making Changes in Production Mode

**Backend changes (Python files):**
```bash
# Edit your Python files, then:
sudo systemctl restart wg-dashboard
```

**Frontend changes (Vue files):**
```bash
# Rebuild the frontend
cd frontend
npm run build

# Restart the service to serve new files
sudo systemctl restart wg-dashboard
```

### Enabling Mock Mode in Production

Edit `backend/.env`:
```
WG_MOCK_MODE=true
WG_MOCK_SCENARIO=mixed
```

Then restart:
```bash
sudo systemctl restart wg-dashboard
sudo journalctl -u wg-dashboard -f  # Verify "MOCK MODE" appears in logs
```

**Important:** Environment variables exported in your shell (like `export WG_MOCK_MODE=true`) do **not** work with systemd services. You must use the `.env` file.

---

## Quick Reference

| Task | Development Mode | Production Mode |
|------|------------------|-----------------|
| **Start** | Terminal 1: `python3 app.py`<br>Terminal 2: `npm run dev` | `sudo systemctl start wg-dashboard` |
| **Access** | http://localhost:5173 | http://localhost:5000 or server IP |
| **Backend changes** | Auto-reloads | Restart: `sudo systemctl restart wg-dashboard` |
| **Frontend changes** | Auto-reloads | Rebuild: `npm run build`<br>Restart: `sudo systemctl restart wg-dashboard` |
| **View logs** | Visible in terminals | `sudo journalctl -u wg-dashboard -f` |
| **Stop** | Ctrl+C in both terminals | `sudo systemctl stop wg-dashboard` |
| **Mock mode** | `export WG_MOCK_MODE=true` | Edit `backend/.env` |

---

## Mock Mode Details

Mock mode allows you to develop and test the WireGuard UI without requiring an actual WireGuard installation or sudo permissions.

### How Mock Mode Works

- **Separate Database:** Mock mode uses `wg_dashboard_mock.db` instead of `wg_dashboard.db`
- **Pre-populated Data:** The mock database contains test clients, peers, and connection data
- **Simulated WireGuard:** The WireGuard manager reads from the database and simulates WireGuard command output
- **No File Dependencies:** Mock data comes from the database, not text files

### Mock Scenarios

Four scenarios are available via `WG_MOCK_SCENARIO`:

| Scenario | Description | Peers | Connection State |
|----------|-------------|-------|------------------|
| `empty` | No peers configured | 0 | N/A |
| `connected` | All peers actively connected | 4 | All connected (recent handshakes) |
| `disconnected` | Peers configured but offline | 4 | All disconnected (no handshakes) |
| `mixed` | Mix of states (default) | 5 | 2 connected, 3 disconnected |

### Creating/Recreating Mock Database

```bash
cd backend

# Create mock database for a specific scenario
# The script always creates wg_dashboard_mock.db - WG_MOCK_MODE not needed
WG_MOCK_SCENARIO=mixed python3 create_mock_db.py

# Try different scenarios
WG_MOCK_SCENARIO=connected python3 create_mock_db.py
WG_MOCK_SCENARIO=empty python3 create_mock_db.py
WG_MOCK_SCENARIO=disconnected python3 create_mock_db.py
```

**Note:** Creating a mock database will drop all existing data in that database. The script creates:
- **1 admin user** (username: `admin`, password: `admin`)
- **3 mock clients** (Acme Corp, TechStart Inc, Legacy Systems Ltd)
- **Peers** with appropriate client assignments and router flags (count depends on scenario)

**Important:** The admin credentials are hardcoded in mock mode for convenience:
- Username: `admin`
- Password: `admin`

Production database has separate admin credentials that you create during deployment.

### Mock Database Location

Flask stores SQLite databases in the `instance/` folder:

- Production database: `backend/instance/wg_dashboard.db`
- Mock database: `backend/instance/wg_dashboard_mock.db`

Both databases have the same schema. The instance folder is automatically created by Flask.

**On production server:**
```bash
ls -lh /opt/wireguard-ui/backend/instance/
```

---

## Troubleshooting

### Development Mode

**"Connection refused" or API errors:**
- Ensure backend is running on port 5000: `curl http://localhost:5000/api/auth/check`
- Check Vite proxy configuration in `frontend/vite.config.js`

**Frontend not hot-reloading:**
- Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+F5 (Windows)
- Restart Vite dev server: Ctrl+C then `npm run dev`

**Backend not auto-reloading:**
- Ensure `FLASK_ENV=development` in `backend/.env` or environment
- Check for Python syntax errors in terminal

### Production Mode

**Changes not visible:**
- Frontend: Did you run `npm run build`?
- Backend: Did you restart with `sudo systemctl restart wg-dashboard`?

**Service won't start:**
```bash
# Check detailed logs
sudo journalctl -u wg-dashboard -n 50 --no-pager

# Check service status
sudo systemctl status wg-dashboard

# Verify file permissions
ls -la /opt/wireguard-ui/
```

**Mock mode not working:**
- Verify `.env` file exists: `cat backend/.env | grep MOCK`
- Check logs show "🧪 MOCK MODE ENABLED": `sudo journalctl -u wg-dashboard -f`
- Verify database path shows `wg_dashboard_mock.db` in logs
- Remember: shell exports don't work with systemd, must use `.env`
- Ensure mock database exists: `ls -lh backend/instance/wg_dashboard_mock.db`
- If missing, create it: `WG_MOCK_SCENARIO=mixed python3 backend/create_mock_db.py`

**No peers showing in mock mode:**
- Check that mock database was created: `ls -lh backend/instance/wg_dashboard_mock.db`
- Verify scenario has peers: `empty` scenario has 0 peers, try `mixed` instead
- Recreate mock database: `cd backend && WG_MOCK_SCENARIO=mixed python3 create_mock_db.py`

**"readonly database" errors:**
- Check permissions: `ls -lh /opt/wireguard-ui/backend/instance/`
- Fix with: `sudo bash /opt/wireguard-ui/deployment/fix_db_permissions.sh`
- Database files need: `664` (rw-rw-r--) owned by `wireguard:wireguard`
- Instance directory needs: `775` (rwxrwxr-x) owned by `wireguard:wireguard`

---

## Recommended Workflow

1. **During development:** Use Development Mode (two terminals)
   - Fast iteration
   - Instant feedback
   - Easy debugging

2. **Before committing:** Test in Production Mode
   - Verify build works: `npm run build`
   - Test as systemd service
   - Ensure production configuration is correct

3. **On server deployment:** Use Production Mode only
   - Systemd service management
   - Nginx reverse proxy for HTTPS
   - Production environment variables

---

## Testing the New Architecture

### Testing WireGuard as Source of Truth

The new architecture can be tested in mock mode without requiring WireGuard installation.

**Scenario 1: Normal Operation**
```bash
# On your VM, pull latest changes
cd /opt/wireguard-ui
git pull

# Recreate mock database with new schema
cd backend
source venv/bin/activate
WG_MOCK_SCENARIO=mixed python3 create_mock_db.py

# Restart service
sudo systemctl restart wg-dashboard
```

You should see:
- "Unregistered Peers" system client in the clients list
- Peers grouped by client with connection status badges
- Connected/disconnected/orphaned counts per client
- Real-time data: endpoint, last handshake, transfer stats

**Scenario 2: CLI-Added Peer Simulation**

In mock mode, peers are created from the database. On a live system with WireGuard:

```bash
# Add peer directly via WireGuard CLI
sudo wg set wg0 peer <PUBLIC_KEY> allowed-ips 10.0.0.99/32

# Check UI - peer should appear under "Unregistered Peers"
# with auto-generated name like "Unknown Peer <pubkey>"
```

**Scenario 3: Orphaned Database Entry**

```bash
# In database, create a peer that doesn't exist in WireGuard
# (This would happen if you removed peer from WireGuard but not DB)

# UI should show peer with "⚠️ Not Configured" warning badge
```

### Verifying Mock Mode Behavior

1. **Check logs** for mode indicator:
   ```bash
   sudo journalctl -u wg-dashboard -f
   ```

   Should show:
   ```
   🧪 MOCK MODE ENABLED
      Scenario: mixed
      Database: sqlite:///wg_dashboard_mock.db
   ```

2. **Check database location**:
   ```bash
   ls -lh /opt/wireguard-ui/backend/instance/
   ```

   Should show both:
   - `wg_dashboard.db` (production)
   - `wg_dashboard_mock.db` (mock mode)

3. **Verify API response** includes real-time fields:
   ```bash
   # Login first, then:
   curl -b cookies.txt http://localhost:5000/api/peers | jq '.[0]'
   ```

   Should include:
   - `connected`: true/false
   - `transfer_rx`: number
   - `transfer_tx`: number
   - `latest_handshake`: ISO timestamp or null
   - `endpoint`: "IP:PORT" or null
   - `configured`: true (if in WireGuard) or false (if orphaned)

### Manual Testing Checklist

- [ ] Peers show connection status badges (✓ Connected, ✗ Disconnected)
- [ ] Client groups show connected/disconnected counts
- [ ] "Unregistered Peers" system client exists
- [ ] System clients don't appear in "Add Peer" client dropdown
- [ ] Transfer statistics display (↓ RX | ↑ TX)
- [ ] Last handshake shows relative time (e.g., "5m ago")
- [ ] Orphaned peers show "⚠️ Not Configured" badge
- [ ] Can reassign peer from "Unregistered Peers" to proper client
- [ ] Deleting peer removes from both WireGuard and database
