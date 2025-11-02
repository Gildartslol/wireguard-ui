# Mock WireGuard Data

This directory contains mock data files for testing the WireGuard UI without a running WireGuard interface.

## Usage

**For Direct Python Execution (Development)**

Set the environment variable to enable mock mode:

```bash
export WG_MOCK_MODE=true
export WG_MOCK_SCENARIO=mixed  # Optional: specify scenario (default: mixed)
python backend/app.py
```

**For Systemd Service (Production/Testing)**

**You must use the .env file method for systemd services.**

Edit `backend/.env` and add:
```
WG_MOCK_MODE=true
WG_MOCK_SCENARIO=mixed
```

Then restart the service:
```bash
sudo systemctl restart wg-dashboard
sudo journalctl -u wg-dashboard -f  # Verify "MOCK MODE" appears in logs
```

**Why?** Environment variables exported in your shell do not persist to systemd services. The `.env` file is read by the Flask application itself via `python-dotenv`.

## Mock Mode Behavior

When mock mode is enabled:
- **All WireGuard commands** return mock data from scenario files (no real `wg` commands executed)
- **Dashboard page** displays mock peer connections
- **Peers management page** displays mock peers (reads from same mock data)
- **Database is NOT used** for peer data in mock mode

This allows full testing of the UI without WireGuard installed or running.

## Optional: Seed Database for Testing

If you want to test database functionality while in mock mode, you can optionally seed the database:

```bash
cd backend
source venv/bin/activate  # If using venv
WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 seed_mock_data.py
```

This creates:
- An admin user (username: `admin`, password: `admin`)
- Database entries for all mock peers

**Note:** This is optional - the UI works fully in mock mode without database seeding.

## Available Scenarios

- **empty** - Interface with no peers configured
- **connected** - All peers actively connected (recent handshakes)
- **mixed** - Some peers connected, some disconnected, various states
- **disconnected** - All peers configured but none connected

## File Format

### wg_dump_*.txt
Machine-readable output from `wg show wg0 dump` command.

Format (tab-separated):
- Line 1: Interface - `private-key public-key listen-port fwmark`
- Lines 2+: Peers - `public-key preshared-key endpoint allowed-ips handshake-sec rx-bytes tx-bytes keepalive`

### wg_show_interface.txt
Human-readable output from `wg show wg0` command.

Contains interface name, public key, and listening port.

## Creating Custom Scenarios

To create a custom scenario:

1. Create a new file: `wg_dump_<scenario>.txt`
2. Use tab-separated values matching the format above
3. Set `WG_MOCK_SCENARIO=<scenario>` to use it

### Example Mock Peer Line

```
aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5aB6=	(none)	192.168.1.100:51820	10.0.0.2/32	60	1048576	524288	25
```

Fields:
- Public key (44 chars base64)
- Preshared key or `(none)`
- Endpoint (IP:port) or `(none)`
- Allowed IPs (comma-separated)
- Handshake seconds ago (0 = never, <180 = connected)
- RX bytes
- TX bytes
- Keepalive interval or `off`
