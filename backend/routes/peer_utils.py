"""
Shared utility functions for peer enrichment and management
"""
from typing import List, Dict, Optional
from models import Peer, Client, db
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)


def get_or_create_unregistered_client() -> Client:
    """
    Get or create the system client for unregistered peers

    Returns:
        Client instance for "Unregistered Peers"
    """
    system_client = Client.query.filter_by(name='Unregistered Peers').first()

    if not system_client:
        logger.info("Creating 'Unregistered Peers' system client")
        system_client = Client(
            name='Unregistered Peers',
            subnet_range='0.0.0.0/0',
            location='System',
            description='Auto-generated client for peers added via WireGuard CLI',
            is_active=True,
            is_system=True,
            created_by=1  # System user (admin)
        )
        db.session.add(system_client)
        db.session.commit()
        logger.info(f"Created system client with ID: {system_client.id}")

    return system_client


def enrich_wireguard_peers(
    wg_peers: List[Dict],
    create_unknown: bool = True,
    include_orphaned: bool = False
) -> List[Dict]:
    """
    Merge WireGuard peer data with database metadata

    This function takes real-time data from WireGuard and enriches it with
    metadata from the database (names, client assignments, descriptions, etc.).

    Args:
        wg_peers: List of peer dicts from wg_manager.get_active_peers()
                  Each dict contains: public_key, endpoint, allowed_ips,
                  latest_handshake, transfer_rx, transfer_tx, connected
        create_unknown: If True, auto-create database entries for peers
                       found in WireGuard but not in database
        include_orphaned: If True, also include database peers not found
                         in WireGuard (marked with configured=False)

    Returns:
        List of enriched peer dicts combining WireGuard + database data
    """
    enriched_peers = []
    wg_public_keys = {peer['public_key'] for peer in wg_peers}

    # Process each WireGuard peer
    for wg_peer in wg_peers:
        public_key = wg_peer['public_key']

        # Try to find peer in database
        peer_db = Peer.query.filter_by(public_key=public_key).first()

        if peer_db:
            # Peer exists in database - merge WireGuard data with DB metadata
            enriched = _merge_peer_data(wg_peer, peer_db, configured=True)
            enriched_peers.append(enriched)

        elif create_unknown:
            # Peer in WireGuard but not in database - create it
            logger.warning(f"Unknown peer found in WireGuard: {public_key[:12]}... - Auto-creating database entry")

            # Get or create system client for unregistered peers
            system_client = get_or_create_unregistered_client()

            # Create database entry
            peer_db = Peer(
                public_key=public_key,
                name=f"Unknown Peer {public_key[:8]}",
                allowed_ips=','.join(wg_peer.get('allowed_ips', [])),
                endpoint=wg_peer.get('endpoint'),
                description='Auto-created from WireGuard CLI',
                created_by=current_user.id if current_user and current_user.is_authenticated else 1,
                client_id=system_client.id,
                is_router=False
            )

            db.session.add(peer_db)
            db.session.commit()
            logger.info(f"Created database entry for unknown peer: {peer_db.id}")

            # Merge and return enriched data
            enriched = _merge_peer_data(wg_peer, peer_db, configured=True)
            enriched_peers.append(enriched)

        else:
            # create_unknown=False - skip unknown peers
            logger.warning(f"Skipping unknown peer: {public_key[:12]}...")

    # Optionally include orphaned database entries
    if include_orphaned:
        db_peers = Peer.query.all()

        for peer_db in db_peers:
            if peer_db.public_key not in wg_public_keys:
                # Peer in database but not in WireGuard
                logger.warning(f"Orphaned peer in database: {peer_db.public_key[:12]}... (not configured in WireGuard)")

                # Create enriched entry with placeholder WireGuard data
                enriched = _merge_peer_data(
                    wg_peer={
                        'public_key': peer_db.public_key,
                        'endpoint': None,
                        'allowed_ips': [],
                        'latest_handshake': None,
                        'transfer_rx': 0,
                        'transfer_tx': 0,
                        'persistent_keepalive': None,
                        'connected': False
                    },
                    peer_db=peer_db,
                    configured=False
                )
                enriched_peers.append(enriched)

    return enriched_peers


def _merge_peer_data(wg_peer: Dict, peer_db: Peer, configured: bool = True) -> Dict:
    """
    Merge WireGuard data with database peer metadata

    Args:
        wg_peer: Dict from WireGuard with real-time connection data
        peer_db: Peer database model instance
        configured: True if peer exists in WireGuard, False if orphaned

    Returns:
        Dict with combined data from both sources
    """
    return {
        # WireGuard real-time data (source of truth for connection status)
        'public_key': wg_peer['public_key'],
        'endpoint': wg_peer.get('endpoint'),
        'allowed_ips': wg_peer.get('allowed_ips', []),
        'latest_handshake': wg_peer.get('latest_handshake'),
        'transfer_rx': wg_peer.get('transfer_rx', 0),
        'transfer_tx': wg_peer.get('transfer_tx', 0),
        'persistent_keepalive': wg_peer.get('persistent_keepalive'),
        'connected': wg_peer.get('connected', False),
        'configured': configured,  # True if in WireGuard, False if orphaned

        # Database metadata (names, organization, descriptions)
        'id': peer_db.id,
        'name': peer_db.name,
        'description': peer_db.description,
        'created_at': peer_db.created_at.isoformat() if peer_db.created_at else None,
        'created_by': peer_db.created_by,
        'client_id': peer_db.client_id,
        'client': {
            'id': peer_db.client.id,
            'name': peer_db.client.name,
            'subnet_range': peer_db.client.subnet_range,
            'is_active': peer_db.client.is_active,
            'is_system': peer_db.client.is_system
        } if peer_db.client else None,
        'is_router': peer_db.is_router
    }
