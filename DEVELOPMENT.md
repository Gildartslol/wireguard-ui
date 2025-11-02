# Development Guide

This guide explains how to run the WireGuard UI in development mode vs production mode.

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
# Mock mode uses a separate database (wg_dashboard_mock.db) pre-populated with test data
export WG_MOCK_MODE=true
export WG_MOCK_SCENARIO=mixed  # Options: empty, connected, mixed, disconnected

# Run Flask dev server
python3 app.py
```

Flask will run on `http://localhost:5000` (but you won't access this directly)

**Note:** Mock mode automatically switches to `wg_dashboard_mock.db`. If the mock database doesn't exist, create it with:
```bash
WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 create_mock_db.py
```

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
WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 create_mock_db.py

# Try different scenarios
WG_MOCK_MODE=true WG_MOCK_SCENARIO=connected python3 create_mock_db.py
WG_MOCK_MODE=true WG_MOCK_SCENARIO=empty python3 create_mock_db.py
```

**Note:** Creating a mock database will drop all existing data in that database. The script creates:
- 1 admin user (username: admin, password: admin)
- 3 mock clients (Acme Corp, TechStart Inc, Legacy Systems Ltd)
- Peers with appropriate client assignments and router flags

### Mock Database Location

- Production database: `backend/wg_dashboard.db`
- Mock database: `backend/wg_dashboard_mock.db`

Both databases have the same schema and are version controlled (mock DB only).

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
- Check logs show "MOCK MODE": `sudo journalctl -u wg-dashboard -f`
- Remember: shell exports don't work with systemd, must use `.env`
- Ensure mock database exists: `ls -lh backend/wg_dashboard_mock.db`
- If missing, create it: `WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 backend/create_mock_db.py`

**No peers showing in mock mode:**
- Check that mock database was created: `ls -lh backend/wg_dashboard_mock.db`
- Verify scenario has peers: `empty` scenario has 0 peers, try `mixed` instead
- Recreate mock database with desired scenario

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
