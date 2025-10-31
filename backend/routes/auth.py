from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from auth import authenticate_user, change_password
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and create session

    Request JSON:
        {
            "username": "admin",
            "password": "password"
        }

    Returns:
        200: Login successful
        400: Missing credentials
        401: Invalid credentials
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        # Authenticate user
        user = authenticate_user(username, password)

        # Create session
        login_user(user, remember=True)

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout current user and destroy session

    Returns:
        200: Logout successful
    """
    try:
        username = current_user.username
        logout_user()
        logger.info(f"User logged out: {username}")

        return jsonify({'message': 'Logout successful'}), 200

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """
    Check if user is authenticated

    Returns:
        200: User info if authenticated
        401: Not authenticated
    """
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 401


@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get current user profile

    Returns:
        200: User profile data
    """
    return jsonify(current_user.to_dict()), 200


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_user_password():
    """
    Change current user's password

    Request JSON:
        {
            "old_password": "current_password",
            "new_password": "new_password"
        }

    Returns:
        200: Password changed successfully
        400: Missing data
        401: Invalid old password
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords required'}), 400

        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400

        # Change password
        change_password(current_user, old_password, new_password)

        return jsonify({'message': 'Password changed successfully'}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
