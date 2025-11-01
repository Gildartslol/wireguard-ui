# Mock WireGuard Data

This directory contains mock data files for testing the WireGuard UI without a running WireGuard interface.

## Usage

Set the environment variable to enable mock mode:

```bash
export WG_MOCK_MODE=true
export WG_MOCK_SCENARIO=mixed  # Optional: specify scenario (default: mixed)
python backend/app.py
```

Or in your `.env` file:
```
WG_MOCK_MODE=true
WG_MOCK_SCENARIO=mixed
```

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
