#!/usr/bin/env python3
"""
Test script to verify database URI is set correctly based on WG_MOCK_MODE
"""
import os
import sys

# Must set BEFORE importing app
print(f"WG_MOCK_MODE environment variable: {os.getenv('WG_MOCK_MODE', 'NOT SET')}")
print(f"WG_MOCK_SCENARIO environment variable: {os.getenv('WG_MOCK_SCENARIO', 'NOT SET')}")
print()

from app import create_app

# Test 1: Create app with current environment
app = create_app()
with app.app_context():
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Database URI from Flask app: {db_uri}")

    if 'sqlite:///' in db_uri:
        db_file = db_uri.replace('sqlite:///', '')
        print(f"Database filename: {db_file}")

        # Check if it matches expected
        mock_mode = os.getenv('WG_MOCK_MODE', 'false').lower() == 'true'
        expected = 'wg_dashboard_mock.db' if mock_mode else 'wg_dashboard.db'

        if db_file == expected:
            print(f"✓ CORRECT! Database name matches expected: {expected}")
            sys.exit(0)
        else:
            print(f"✗ ERROR! Expected {expected} but got {db_file}")
            sys.exit(1)
