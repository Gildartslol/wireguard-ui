from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from wg_manager import WireGuardManager
from models import Peer, db
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

peers_bp = Blueprint('peers', __name__, url_prefix='/api/peers')


@peers_bp.route('', methods=['GET'])
@login_required
def list_peers():
    """
    List all configured peers

    In mock mode: Returns peers from mock WireGuard data
    In live mode: Returns peers from database

    Returns:
        200: List of peers
        500: Error listing peers
    """
    try:
        import os
        mock_mode = os.getenv('WG_MOCK_MODE', 'false').lower() == 'true'

        if mock_mode:
            # Mock mode: read from WireGuard manager (returns mock data)
            wg_interface = current_app.config.get('WG_INTERFACE', 'wg0')
            wg_manager = WireGuardManager(wg_interface)

            # Get active peers from mock data
            active_peers = wg_manager.get_active_peers()

            # Enrich with database metadata if available
            enriched_peers = []
            for idx, peer in enumerate(active_peers):
                peer_db = Peer.query.filter_by(public_key=peer['public_key']).first()

                # Generate consistent UUID for mock peers (based on index for consistency)
                import uuid
                mock_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, peer['public_key']))

                peer_data = {
                    'id': peer_db.id if peer_db else mock_uuid,
                    'public_key': peer['public_key'],
                    'name': peer_db.name if peer_db else f"Mock Peer {idx + 1}",
                    'allowed_ips': peer['allowed_ips'],
                    'endpoint': peer.get('endpoint'),
                    'description': peer_db.description if peer_db else 'Mock peer from test data',
                    'created_at': peer_db.created_at.isoformat() if peer_db and peer_db.created_at else None,
                    'created_by': peer_db.created_by if peer_db else None,
                    'client_id': peer_db.client_id if peer_db else None,
                    'client': {
                        'id': peer_db.client.id,
                        'name': peer_db.client.name,
                        'subnet_range': peer_db.client.subnet_range,
                        'is_active': peer_db.client.is_active
                    } if peer_db and peer_db.client else None,
                    'is_router': peer_db.is_router if peer_db else False
                }

                enriched_peers.append(peer_data)

            return jsonify(enriched_peers), 200
        else:
            # Live mode: read from database
            peers = Peer.query.order_by(Peer.created_at.desc()).all()
            peers_data = [peer.to_dict() for peer in peers]

            return jsonify(peers_data), 200

    except Exception as e:
        logger.error(f"Error listing peers: {e}")
        return jsonify({'error': str(e)}), 500


@peers_bp.route('', methods=['POST'])
@login_required
def create_peer():
    """
    Create new peer and add to WireGuard

    Request JSON:
        {
            "name": "Client 1",
            "public_key": "peer_public_key",
            "allowed_ips": "10.0.0.2/32",
            "description": "Description",
            "preshared_key": "optional_preshared_key"
        }

    Returns:
        201: Peer created successfully
        400: Invalid data
        409: Peer already exists
        500: Error creating peer
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        name = data.get('name')
        public_key = data.get('public_key')
        allowed_ips = data.get('allowed_ips')

        if not all([name, public_key, allowed_ips]):
            return jsonify({'error': 'Name, public_key, and allowed_ips are required'}), 400

        # Check if peer already exists
        existing_peer = Peer.query.filter_by(public_key=public_key).first()
        if existing_peer:
            return jsonify({'error': 'Peer with this public key already exists'}), 409

        # Validate client_id if provided
        client_id = data.get('client_id')
        if client_id:
            from models import Client
            client = Client.query.filter_by(id=client_id).first()
            if not client:
                return jsonify({'error': f'Client not found: {client_id}'}), 404

        # Convert allowed_ips to list if it's a string
        if isinstance(allowed_ips, str):
            allowed_ips_list = [ip.strip() for ip in allowed_ips.split(',')]
        else:
            allowed_ips_list = allowed_ips

        # Add peer to WireGuard
        wg_interface = current_app.config.get('WG_INTERFACE', 'wg0')
        wg_manager = WireGuardManager(wg_interface)

        wg_manager.add_peer(
            public_key=public_key,
            allowed_ips=allowed_ips_list,
            preshared_key=data.get('preshared_key')
        )

        # Save peer to database
        peer = Peer(
            public_key=public_key,
            name=name,
            allowed_ips=','.join(allowed_ips_list),
            endpoint=data.get('endpoint'),
            description=data.get('description'),
            preshared_key=data.get('preshared_key'),
            created_by=current_user.id,
            client_id=data.get('client_id'),
            is_router=data.get('is_router', False)
        )

        db.session.add(peer)
        db.session.commit()

        logger.info(f"Created peer: {name} ({public_key[:12]}...) by user {current_user.username}")

        return jsonify(peer.to_dict()), 201

    except ValueError as e:
        logger.error(f"Validation error creating peer: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating peer: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@peers_bp.route('/<peer_id>', methods=['GET'])
@login_required
def get_peer(peer_id):
    """
    Get peer details

    Args:
        peer_id: Peer UUID

    Returns:
        200: Peer data
        404: Peer not found
        500: Error getting peer
    """
    try:
        peer = Peer.query.filter_by(id=peer_id).first()

        if not peer:
            return jsonify({'error': 'Peer not found'}), 404

        return jsonify(peer.to_dict()), 200

    except Exception as e:
        logger.error(f"Error getting peer: {e}")
        return jsonify({'error': str(e)}), 500


@peers_bp.route('/<peer_id>', methods=['DELETE'])
@login_required
def delete_peer(peer_id):
    """
    Delete peer from WireGuard and database

    Args:
        peer_id: Peer UUID

    Returns:
        200: Peer deleted successfully
        404: Peer not found
        500: Error deleting peer
    """
    try:
        # Get peer from database
        peer = Peer.query.filter_by(id=peer_id).first()

        if not peer:
            return jsonify({'error': 'Peer not found'}), 404

        # Remove from WireGuard (use peer's public_key)
        wg_interface = current_app.config.get('WG_INTERFACE', 'wg0')
        wg_manager = WireGuardManager(wg_interface)

        try:
            wg_manager.remove_peer(peer.public_key)
        except Exception as wg_error:
            logger.warning(f"WireGuard removal failed (peer may not exist in WG): {wg_error}")

        # Delete from database
        db.session.delete(peer)
        db.session.commit()

        logger.info(f"Deleted peer: {peer.name} (UUID: {peer_id[:8]}..., pubkey: {peer.public_key[:12]}...) by user {current_user.username}")

        return jsonify({'message': 'Peer deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Error deleting peer: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@peers_bp.route('/generate-keys', methods=['POST'])
@login_required
def generate_keys():
    """
    Generate new WireGuard key pair

    Returns:
        200: Generated keys
        500: Error generating keys
    """
    try:
        keys = WireGuardManager.generate_keypair()

        return jsonify(keys), 200

    except Exception as e:
        logger.error(f"Error generating keys: {e}")
        return jsonify({'error': str(e)}), 500


@peers_bp.route('/<peer_id>/config', methods=['GET'])
@login_required
def get_peer_config(peer_id):
    """
    Generate and download peer configuration file

    Args:
        peer_id: Peer UUID

    Query Parameters:
        private_key: Peer's private key (required)

    Returns:
        200: Configuration file
        400: Missing private key
        404: Peer not found
        500: Error generating config
    """
    try:
        # Get private key from query params
        private_key = request.args.get('private_key')

        if not private_key:
            return jsonify({'error': 'private_key query parameter required'}), 400

        # Get peer from database
        peer = Peer.query.filter_by(id=peer_id).first()

        if not peer:
            return jsonify({'error': 'Peer not found'}), 404

        # Get server configuration
        server_public_key = current_app.config.get('WG_SERVER_PUBLIC_KEY')
        server_address = current_app.config.get('WG_SERVER_ADDRESS', '').split('/')[0]  # Get IP without CIDR
        server_port = current_app.config.get('WG_SERVER_PORT', 51820)

        if not server_public_key:
            return jsonify({'error': 'Server public key not configured'}), 500

        # Determine server endpoint (could be from env or auto-detected)
        # For now, use a placeholder that the admin should configure
        endpoint = f"{server_address}:{server_port}"

        # Get peer's IP address from allowed_ips (first IP)
        allowed_ips = peer.allowed_ips.split(',')
        peer_address = allowed_ips[0] if allowed_ips else "10.0.0.2/32"

        # Generate config
        config_content = WireGuardManager.generate_peer_config(
            peer_name=peer.name,
            private_key=private_key,
            server_public_key=server_public_key,
            endpoint=endpoint,
            allowed_ips=['0.0.0.0/0', '::/0'],  # Route all traffic through VPN
            address=peer_address,
            dns="1.1.1.1"
        )

        # Create file in memory
        config_file = BytesIO(config_content.encode('utf-8'))
        config_file.seek(0)

        # Return as downloadable file
        return send_file(
            config_file,
            as_attachment=True,
            download_name=f"{peer.name.replace(' ', '_')}.conf",
            mimetype='text/plain'
        )

    except Exception as e:
        logger.error(f"Error generating config: {e}")
        return jsonify({'error': str(e)}), 500


@peers_bp.route('/<peer_id>', methods=['PUT'])
@login_required
def update_peer(peer_id):
    """
    Update peer information

    Args:
        peer_id: Peer UUID

    Request JSON:
        {
            "name": "Updated Name",
            "allowed_ips": "10.0.0.2/32,10.0.1.0/24",
            "description": "Updated description"
        }

    Returns:
        200: Peer updated successfully
        404: Peer not found
        400: Invalid data
        500: Error updating peer
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Get peer from database
        peer = Peer.query.filter_by(id=peer_id).first()

        if not peer:
            return jsonify({'error': 'Peer not found'}), 404

        # Update database fields
        if 'name' in data:
            peer.name = data['name']
        if 'description' in data:
            peer.description = data['description']
        if 'client_id' in data:
            client_id = data['client_id']
            if client_id:  # Validate if not NULL
                from models import Client
                client = Client.query.filter_by(id=client_id).first()
                if not client:
                    return jsonify({'error': f'Client not found: {client_id}'}), 404
            peer.client_id = client_id
        if 'is_router' in data:
            peer.is_router = data['is_router']
        if 'allowed_ips' in data:
            # Convert to list if string
            if isinstance(data['allowed_ips'], str):
                allowed_ips_list = [ip.strip() for ip in data['allowed_ips'].split(',')]
            else:
                allowed_ips_list = data['allowed_ips']

            # Update WireGuard (use peer's public_key)
            wg_interface = current_app.config.get('WG_INTERFACE', 'wg0')
            wg_manager = WireGuardManager(wg_interface)
            wg_manager.update_peer(peer.public_key, allowed_ips=allowed_ips_list)

            # Update database
            peer.allowed_ips = ','.join(allowed_ips_list)

        db.session.commit()

        logger.info(f"Updated peer: {peer.name} (UUID: {peer_id[:8]}..., pubkey: {peer.public_key[:12]}...) by user {current_user.username}")

        return jsonify(peer.to_dict()), 200

    except ValueError as e:
        logger.error(f"Validation error updating peer: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating peer: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
