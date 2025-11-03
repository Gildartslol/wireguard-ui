#!/usr/bin/env python3
"""
Debug script to show what database configuration is being used
"""
import os
from app import create_app

print("=" * 60)
print("ENVIRONMENT VARIABLES:")
print("=" * 60)
print(f"WG_MOCK_MODE: {os.getenv('WG_MOCK_MODE', 'NOT SET')}")
print(f"WG_MOCK_SCENARIO: {os.getenv('WG_MOCK_SCENARIO', 'NOT SET')}")
print(f"DATABASE_URI: {os.getenv('DATABASE_URI', 'NOT SET')}")
print()

print("=" * 60)
print("FLASK APP CONFIG:")
print("=" * 60)
app = create_app()
print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"Instance path: {app.instance_path}")
print()

# Determine expected database file
if 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']:
    db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if not db_file.startswith('/'):
        import pathlib
        full_path = pathlib.Path(app.instance_path) / db_file
        print(f"Database file path: {full_path}")
        print(f"Database exists: {full_path.exists()}")
        if full_path.exists():
            import os as os_stat
            stat_info = os_stat.stat(full_path)
            print(f"Database size: {stat_info.st_size} bytes")
            from datetime import datetime
            print(f"Last modified: {datetime.fromtimestamp(stat_info.st_mtime)}")
