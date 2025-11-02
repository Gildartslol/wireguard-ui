from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from wg_manager import WireGuardManager
from models import Peer, ConnectionHistory, db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """
    Get dashboard statistics

    Returns:
        200: Statistics data
        500: Error getting stats
    """
    try:
        wg_interface = current_app.config.get('WG_INTERFACE', 'wg0')
        wg_manager = WireGuardManager(wg_interface)

        # Get WireGuard stats
        wg_stats = wg_manager.get_stats()

        # Get database stats
        total_peers_db = Peer.query.count()
        recent_history = ConnectionHistory.query.filter(
            ConnectionHistory.recorded_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()

        stats = {
            'total_peers': wg_stats['total_peers'],
            'connected_peers': wg_stats['connected_peers'],
            'disconnected_peers': wg_stats['disconnected_peers'],
            'total_peers_configured': total_peers_db,
            'total_transfer_rx': wg_stats['total_transfer_rx'],
            'total_transfer_tx': wg_stats['total_transfer_tx'],
            'total_transfer': wg_stats['total_transfer'],
            'history_records_24h': recent_history
        }

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/peers', methods=['GET'])
@login_required
def get_active_peers():
    """
    Get active peer connections with real-time data

    Returns:
        200: List of active peers with enriched metadata
        500: Error getting peers
    """
    try:
        wg_interface = current_app.config.get('WG_INTERFACE', 'wg0')
        wg_manager = WireGuardManager(wg_interface)

        # Get active peers from WireGuard
        active_peers = wg_manager.get_active_peers()

        # Enrich with database metadata
        enriched_peers = []
        for peer in active_peers:
            # Get peer metadata from database
            peer_db = Peer.query.filter_by(public_key=peer['public_key']).first()

            # Generate consistent UUID for peers not in database (mock mode)
            import uuid
            mock_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, peer['public_key']))

            peer_data = {
                **peer,
                'id': peer_db.id if peer_db else mock_uuid,
                'name': peer_db.name if peer_db else 'Unknown',
                'description': peer_db.description if peer_db else None,
                'created_at': peer_db.created_at.isoformat() if peer_db and peer_db.created_at else None
            }

            enriched_peers.append(peer_data)

        # Sort by connection status (connected first) and then by name
        enriched_peers.sort(key=lambda x: (not x['connected'], x['name'].lower()))

        return jsonify(enriched_peers), 200

    except Exception as e:
        logger.error(f"Error getting active peers: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """
    Get connection history

    Query Parameters:
        limit: Number of records to return (default: 100)
        peer_id: Filter by peer ID
        hours: Filter records from last N hours (default: 24)

    Returns:
        200: Connection history records
        500: Error getting history
    """
    try:
        from flask import request

        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        peer_id = request.args.get('peer_id', type=int)
        hours = request.args.get('hours', 24, type=int)

        # Build query
        query = ConnectionHistory.query

        # Filter by time
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(ConnectionHistory.recorded_at >= since)

        # Filter by peer if specified
        if peer_id:
            query = query.filter_by(peer_id=peer_id)

        # Order by most recent first
        query = query.order_by(ConnectionHistory.recorded_at.desc())

        # Limit results
        query = query.limit(limit)

        # Execute query
        history_records = query.all()

        # Convert to JSON
        history_data = [record.to_dict() for record in history_records]

        return jsonify(history_data), 200

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/interface', methods=['GET'])
@login_required
def get_interface_info():
    """
    Get WireGuard interface information

    Returns:
        200: Interface information
        500: Error getting interface info
    """
    try:
        wg_interface = current_app.config.get('WG_INTERFACE', 'wg0')
        wg_manager = WireGuardManager(wg_interface)

        interface_info = wg_manager.get_interface_info()

        return jsonify(interface_info), 200

    except Exception as e:
        logger.error(f"Error getting interface info: {e}")
        return jsonify({'error': str(e)}), 500
