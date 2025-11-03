# Backend Tools

This directory contains testing, debugging, and development utility scripts.

## Scripts

### debug_config.py
Shows the current database configuration and environment variables.

**Usage:**
```bash
cd backend
WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 tools/debug_config.py
```

**Output:**
- Environment variables (WG_MOCK_MODE, WG_MOCK_SCENARIO, DATABASE_URI)
- Flask app configuration (SQLALCHEMY_DATABASE_URI)
- Database file location and status

### test_db_uri.py
Tests that database URI is set correctly based on WG_MOCK_MODE.

**Usage:**
```bash
cd backend
WG_MOCK_MODE=true python3 tools/test_db_uri.py
```

**Returns:**
- Exit code 0 if database URI matches expected value
- Exit code 1 if there's a mismatch

### test_mode_logging.sh
Tests mode logging functionality by running the app with different configurations.

**Usage:**
```bash
cd backend
source venv/bin/activate
./tools/test_mode_logging.sh
```

**Tests:**
- Production mode (no WG_MOCK_MODE set)
- Mock mode with mixed scenario
- Mock mode with empty scenario

## When to Use These Tools

- **Before deployment**: Run tests to verify configuration
- **Debugging**: Use debug_config.py to check what database is being used
- **Testing changes**: Verify mock mode switches databases correctly
- **CI/CD**: Include test_db_uri.py in automated tests
