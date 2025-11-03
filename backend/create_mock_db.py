#!/usr/bin/env python3
"""
Create and populate mock database for testing

This script creates a pre-populated SQLite database for mock mode testing.
Supports multiple scenarios: empty, connected, mixed, disconnected.

Usage:
    WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 create_mock_db.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from models import db, User, Client, Peer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mock peer public keys (consistent across scenarios)
MOCK_PEERS = [
    {
        'public_key': 'mock1aPeer1PublicKeyBase64EncodedString==',
        'allowed_ips': '10.0.0.10/32',
        'endpoint': '203.0.113.1:51820'
    },
    {
        'public_key': 'mock2bPeer2PublicKeyBase64EncodedString==',
        'allowed_ips': '10.0.0.11/32',
        'endpoint': '203.0.113.2:51820'
    },
    {
        'public_key': 'mock3cPeer3PublicKeyBase64EncodedString==',
        'allowed_ips': '10.0.0.12/32',
        'endpoint': '203.0.113.3:51820'
    },
    {
        'public_key': 'mock4dPeer4PublicKeyBase64EncodedString==',
        'allowed_ips': '10.0.0.13/32',
        'endpoint': '203.0.113.4:51820'
    },
    {
        'public_key': 'mock5ePeer5PublicKeyBase64EncodedString==',
        'allowed_ips': '10.0.0.14/32',
        'endpoint': '203.0.113.5:51820'
    }
]


def create_admin_user():
    """Create admin user if not exists"""
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
    return admin


def create_mock_clients(admin_id):
    """Create mock client organizations"""
    clients_data = [
        {
            'name': 'Acme Corp',
            'subnet_range': '10.200.0.0/24',
            'location': 'New York Office',
            'description': 'Primary office network',
            'is_active': True
        },
        {
            'name': 'TechStart Inc',
            'subnet_range': '10.200.1.0/24',
            'location': 'San Francisco HQ',
            'description': 'Development environment',
            'is_active': True
        },
        {
            'name': 'Legacy Systems Ltd',
            'subnet_range': '10.200.2.0/24',
            'location': 'London Branch',
            'description': 'Legacy infrastructure (archived)',
            'is_active': False
        }
    ]

    clients = []
    for client_data in clients_data:
        existing = Client.query.filter_by(name=client_data['name']).first()
        if existing:
            clients.append(existing)
        else:
            client = Client(
                name=client_data['name'],
                subnet_range=client_data['subnet_range'],
                location=client_data['location'],
                description=client_data['description'],
                is_active=client_data['is_active'],
                created_by=admin_id,
                created_at=datetime.utcnow()
            )
            db.session.add(client)
            clients.append(client)
            logger.info(f"Created client: {client.name}")

    db.session.commit()
    return clients


def seed_scenario_empty(admin_id, clients):
    """Scenario: Empty - no peers configured"""
    logger.info("Scenario 'empty': No peers will be created")
    # No peers to create
    return 0


def seed_scenario_connected(admin_id, clients):
    """Scenario: Connected - 4 peers, all actively connected"""
    logger.info("Scenario 'connected': Creating 4 actively connected peers")

    peer_configs = [
        {
            'name': 'Acme Router',
            'client_id': clients[0].id,
            'is_router': True,
            'description': 'Acme Corp main gateway - actively connected'
        },
        {
            'name': 'Acme Workstation',
            'client_id': clients[0].id,
            'is_router': False,
            'description': 'Acme Corp workstation - actively connected'
        },
        {
            'name': 'TechStart Router',
            'client_id': clients[1].id,
            'is_router': True,
            'description': 'TechStart Inc gateway - actively connected'
        },
        {
            'name': 'TechStart Dev Server',
            'client_id': clients[1].id,
            'is_router': False,
            'description': 'TechStart development server - actively connected'
        }
    ]

    created = 0
    for idx, config in enumerate(peer_configs):
        peer = Peer(
            public_key=MOCK_PEERS[idx]['public_key'],
            name=config['name'],
            allowed_ips=MOCK_PEERS[idx]['allowed_ips'],
            endpoint=MOCK_PEERS[idx]['endpoint'],
            description=config['description'],
            created_by=admin_id,
            created_at=datetime.utcnow() - timedelta(days=7),
            client_id=config['client_id'],
            is_router=config['is_router']
        )
        db.session.add(peer)
        created += 1

    db.session.commit()
    return created


def seed_scenario_disconnected(admin_id, clients):
    """Scenario: Disconnected - 4 peers, all configured but not connected"""
    logger.info("Scenario 'disconnected': Creating 4 disconnected peers")

    peer_configs = [
        {
            'name': 'Acme Router (Offline)',
            'client_id': clients[0].id,
            'is_router': True,
            'description': 'Acme Corp main gateway - offline'
        },
        {
            'name': 'Acme Workstation (Offline)',
            'client_id': clients[0].id,
            'is_router': False,
            'description': 'Acme Corp workstation - offline'
        },
        {
            'name': 'TechStart Router (Offline)',
            'client_id': clients[1].id,
            'is_router': True,
            'description': 'TechStart Inc gateway - offline'
        },
        {
            'name': 'TechStart Dev Server (Offline)',
            'client_id': clients[1].id,
            'is_router': False,
            'description': 'TechStart development server - offline'
        }
    ]

    created = 0
    for idx, config in enumerate(peer_configs):
        peer = Peer(
            public_key=MOCK_PEERS[idx]['public_key'],
            name=config['name'],
            allowed_ips=MOCK_PEERS[idx]['allowed_ips'],
            endpoint=MOCK_PEERS[idx]['endpoint'],
            description=config['description'],
            created_by=admin_id,
            created_at=datetime.utcnow() - timedelta(days=7),
            client_id=config['client_id'],
            is_router=config['is_router']
        )
        db.session.add(peer)
        created += 1

    db.session.commit()
    return created


def seed_scenario_mixed(admin_id, clients):
    """Scenario: Mixed - 5 peers with varied connection states"""
    logger.info("Scenario 'mixed': Creating 5 peers with mixed connection states")

    peer_configs = [
        {
            'name': 'Acme Router',
            'client_id': clients[0].id,
            'is_router': True,
            'description': 'Acme Corp main gateway - connected'
        },
        {
            'name': 'Acme Workstation',
            'client_id': clients[0].id,
            'is_router': False,
            'description': 'Acme Corp workstation - disconnected'
        },
        {
            'name': 'TechStart Router',
            'client_id': clients[1].id,
            'is_router': True,
            'description': 'TechStart Inc gateway - connected'
        },
        {
            'name': 'TechStart Dev Server',
            'client_id': clients[1].id,
            'is_router': False,
            'description': 'TechStart development server - recently connected'
        },
        {
            'name': 'Legacy Router (Inactive)',
            'client_id': clients[2].id,
            'is_router': True,
            'description': 'Legacy Systems gateway - inactive client'
        }
    ]

    created = 0
    for idx, config in enumerate(peer_configs):
        peer = Peer(
            public_key=MOCK_PEERS[idx]['public_key'],
            name=config['name'],
            allowed_ips=MOCK_PEERS[idx]['allowed_ips'],
            endpoint=MOCK_PEERS[idx]['endpoint'],
            description=config['description'],
            created_by=admin_id,
            created_at=datetime.utcnow() - timedelta(days=7),
            client_id=config['client_id'],
            is_router=config['is_router']
        )
        db.session.add(peer)
        created += 1

    db.session.commit()
    return created


def create_mock_database():
    """Main function to create and populate mock database"""

    # Verify mock mode is enabled
    mock_mode = os.getenv('WG_MOCK_MODE', 'false').lower() == 'true'
    if not mock_mode:
        logger.error("WG_MOCK_MODE must be set to 'true' to create mock database")
        logger.error("Usage: WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed python3 create_mock_db.py")
        sys.exit(1)

    scenario = os.getenv('WG_MOCK_SCENARIO', 'mixed')
    logger.info(f"Creating mock database for scenario: {scenario}")

    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Show where database will be created
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        logger.info(f"Database URI: {db_uri}")

        # Extract path from URI for display
        if 'sqlite:///' in db_uri:
            db_path = db_uri.replace('sqlite:///', '')
            if not db_path.startswith('/'):
                # Relative path - show full path
                import pathlib
                full_path = pathlib.Path(app.instance_path) / db_path
                logger.info(f"Database location: {full_path}")
        # Drop all tables and recreate (fresh start)
        logger.info("Dropping existing tables...")
        db.drop_all()
        logger.info("Creating database tables...")
        db.create_all()

        # Create admin user
        admin = create_admin_user()

        # Create mock clients
        clients = create_mock_clients(admin.id)

        # Seed based on scenario
        scenario_funcs = {
            'empty': seed_scenario_empty,
            'connected': seed_scenario_connected,
            'disconnected': seed_scenario_disconnected,
            'mixed': seed_scenario_mixed
        }

        if scenario not in scenario_funcs:
            logger.error(f"Unknown scenario: {scenario}")
            logger.error(f"Valid scenarios: {', '.join(scenario_funcs.keys())}")
            sys.exit(1)

        peers_created = scenario_funcs[scenario](admin.id, clients)

        logger.info(f"✓ Mock database created successfully")
        logger.info(f"  - Scenario: {scenario}")
        logger.info(f"  - Clients: {len(clients)}")
        logger.info(f"  - Peers: {peers_created}")

        # Show database location again
        if 'sqlite:///' in db_uri:
            db_path = db_uri.replace('sqlite:///', '')
            if not db_path.startswith('/'):
                import pathlib
                full_path = pathlib.Path(app.instance_path) / db_path
                logger.info(f"  - Location: {full_path}")
            else:
                logger.info(f"  - Location: {db_path}")
        else:
            logger.info(f"  - Database: wg_dashboard_mock.db")


if __name__ == '__main__':
    create_mock_database()
