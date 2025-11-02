#!/usr/bin/env python3
"""
Seed database with mock peer data for testing

This script populates the database with peers matching the mock WireGuard data.
Run this in mock mode to have peers visible in the Peers management page.

Usage:
    WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 seed_mock_data.py
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import app, db
from models import User, Peer
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_mock_dump(scenario='mixed'):
    """
    Parse mock dump file and extract peer data

    Args:
        scenario: Mock scenario name (mixed, connected, disconnected, empty)

    Returns:
        List of peer dictionaries
    """
    mock_file = backend_dir / "tests" / "mock_data" / f"wg_dump_{scenario}.txt"

    if not mock_file.exists():
        logger.error(f"Mock file not found: {mock_file}")
        return []

    peers = []
    with open(mock_file, 'r') as f:
        lines = f.readlines()

    # Skip first line (interface info) and parse peer lines
    for i, line in enumerate(lines[1:], start=1):
        line = line.strip()
        if not line:
            continue

        parts = line.split('\t')
        if len(parts) < 8:
            continue

        public_key = parts[0]
        # preshared_key = parts[1]
        endpoint = parts[2] if parts[2] != "(none)" else None
        allowed_ips_str = parts[3]
        # handshake_seconds = parts[4]
        # transfer_rx = parts[5]
        # transfer_tx = parts[6]
        # persistent_keepalive = parts[7]

        peer = {
            'public_key': public_key,
            'name': f'Mock Peer {i}',  # Default name
            'allowed_ips': allowed_ips_str,
            'endpoint': endpoint,
            'description': f'Mock peer from {scenario} scenario'
        }

        peers.append(peer)

    return peers


def seed_database():
    """Seed database with mock peers"""

    # Check if mock mode is enabled
    mock_mode = os.getenv('WG_MOCK_MODE', 'false').lower() == 'true'
    if not mock_mode:
        logger.warning("WG_MOCK_MODE is not enabled. This script is intended for mock mode testing.")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            logger.info("Aborted.")
            return

    scenario = os.getenv('WG_MOCK_SCENARIO', 'mixed')

    logger.info(f"Seeding database with mock data (scenario: {scenario})")

    with app.app_context():
        # Check if admin user exists, create if not
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            logger.info("Creating admin user (username: admin, password: admin)")
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created")

        # Parse mock peers
        mock_peers = parse_mock_dump(scenario)

        if not mock_peers:
            logger.warning(f"No peers found in mock scenario: {scenario}")
            return

        logger.info(f"Found {len(mock_peers)} peers in mock data")

        # Add peers to database
        added_count = 0
        skipped_count = 0

        for peer_data in mock_peers:
            # Check if peer already exists
            existing = Peer.query.filter_by(public_key=peer_data['public_key']).first()

            if existing:
                logger.debug(f"Peer already exists: {peer_data['public_key'][:12]}...")
                skipped_count += 1
                continue

            # Create new peer
            peer = Peer(
                public_key=peer_data['public_key'],
                name=peer_data['name'],
                allowed_ips=peer_data['allowed_ips'],
                endpoint=peer_data.get('endpoint'),
                description=peer_data.get('description'),
                created_by=admin.id,
                created_at=datetime.utcnow()
            )

            db.session.add(peer)
            added_count += 1
            logger.info(f"Added peer: {peer.name} ({peer.public_key[:12]}...)")

        # Commit all changes
        db.session.commit()

        logger.info(f"Database seeding complete: {added_count} added, {skipped_count} skipped")
        logger.info(f"Total peers in database: {Peer.query.count()}")


if __name__ == '__main__':
    seed_database()
