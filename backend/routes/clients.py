from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import Client, db
import logging

logger = logging.getLogger(__name__)

clients_bp = Blueprint('clients', __name__, url_prefix='/api/clients')


@clients_bp.route('', methods=['GET'])
@login_required
def list_clients():
    """
    List all clients

    Returns:
        200: List of clients (active first, then by name)
        500: Error listing clients
    """
    try:
        clients = Client.query.order_by(Client.is_active.desc(), Client.name).all()
        return jsonify([c.to_dict() for c in clients]), 200

    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        return jsonify({'error': str(e)}), 500


@clients_bp.route('', methods=['POST'])
@login_required
def create_client():
    """
    Create new client

    Request JSON:
        {
            "name": "Client Name",
            "subnet_range": "10.200.0.0/24",
            "location": "City, State",
            "description": "Description",
            "is_active": true
        }

    Returns:
        201: Client created successfully
        400: Invalid data
        409: Client already exists
        500: Error creating client
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validation
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Name is required'}), 400

        # Check duplicate
        existing = Client.query.filter_by(name=name).first()
        if existing:
            return jsonify({'error': 'Client with this name already exists'}), 409

        client = Client(
            name=name,
            subnet_range=data.get('subnet_range'),
            location=data.get('location'),
            description=data.get('description'),
            is_active=data.get('is_active', True),
            created_by=current_user.id
        )

        db.session.add(client)
        db.session.commit()

        logger.info(f"Created client: {name} by user {current_user.username}")
        return jsonify(client.to_dict()), 201

    except Exception as e:
        logger.error(f"Error creating client: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    """
    Get client details

    Args:
        client_id: Client UUID

    Returns:
        200: Client data
        404: Client not found
        500: Error getting client
    """
    try:
        client = Client.query.filter_by(id=client_id).first()

        if not client:
            return jsonify({'error': 'Client not found'}), 404

        return jsonify(client.to_dict()), 200

    except Exception as e:
        logger.error(f"Error getting client: {e}")
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>', methods=['PUT'])
@login_required
def update_client(client_id):
    """
    Update client

    Args:
        client_id: Client UUID

    Request JSON:
        {
            "name": "Updated Name",
            "subnet_range": "10.200.1.0/24",
            "location": "New Location",
            "description": "Updated description",
            "is_active": false
        }

    Returns:
        200: Client updated successfully
        404: Client not found
        400: Invalid data
        500: Error updating client
    """
    try:
        client = Client.query.filter_by(id=client_id).first()

        if not client:
            return jsonify({'error': 'Client not found'}), 404

        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update fields
        if 'name' in data:
            client.name = data['name']
        if 'subnet_range' in data:
            client.subnet_range = data['subnet_range']
        if 'location' in data:
            client.location = data['location']
        if 'description' in data:
            client.description = data['description']
        if 'is_active' in data:
            client.is_active = data['is_active']

        db.session.commit()

        logger.info(f"Updated client: {client.name} (UUID: {client_id[:8]}...)")
        return jsonify(client.to_dict()), 200

    except Exception as e:
        logger.error(f"Error updating client: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>', methods=['DELETE'])
@login_required
def delete_client(client_id):
    """
    Delete client

    Args:
        client_id: Client UUID

    Note: Due to ondelete='SET NULL', associated peers will be orphaned (not deleted)

    Returns:
        200: Client deleted successfully
        404: Client not found
        500: Error deleting client
    """
    try:
        client = Client.query.filter_by(id=client_id).first()

        if not client:
            return jsonify({'error': 'Client not found'}), 404

        # Foreign key constraint with SET NULL will orphan peers
        db.session.delete(client)
        db.session.commit()

        logger.info(f"Deleted client: {client.name} (UUID: {client_id[:8]}...)")
        return jsonify({'message': 'Client deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Error deleting client: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
