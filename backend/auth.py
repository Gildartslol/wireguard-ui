from flask_login import LoginManager
from models import User, db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

login_manager = LoginManager()


def init_auth(app):
    """Initialize authentication with Flask app"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


def authenticate_user(username: str, password: str) -> User:
    """
    Authenticate user with username and password

    Args:
        username: Username
        password: Password

    Returns:
        User object if authentication successful

    Raises:
        ValueError: If authentication fails
    """
    user = User.query.filter_by(username=username).first()

    if not user:
        logger.warning(f"Failed login attempt for non-existent user: {username}")
        raise ValueError("Invalid username or password")

    if not user.is_active:
        logger.warning(f"Inactive user attempted login: {username}")
        raise ValueError("Account is disabled")

    if not user.check_password(password):
        logger.warning(f"Failed login attempt for user: {username}")
        raise ValueError("Invalid username or password")

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    logger.info(f"Successful login: {username}")
    return user


def create_user(username: str, password: str, email: str = None, is_admin: bool = False) -> User:
    """
    Create new user

    Args:
        username: Username
        password: Password
        email: Email address
        is_admin: Whether user is admin

    Returns:
        Created User object

    Raises:
        ValueError: If user already exists
    """
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        raise ValueError(f"User with username '{username}' already exists")

    if email:
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise ValueError(f"User with email '{email}' already exists")

    # Create new user
    user = User(
        username=username,
        email=email,
        is_admin=is_admin,
        is_active=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    logger.info(f"Created new user: {username} (admin: {is_admin})")
    return user


def change_password(user: User, old_password: str, new_password: str) -> bool:
    """
    Change user password

    Args:
        user: User object
        old_password: Current password
        new_password: New password

    Returns:
        True if successful

    Raises:
        ValueError: If old password is incorrect
    """
    if not user.check_password(old_password):
        raise ValueError("Current password is incorrect")

    user.set_password(new_password)
    db.session.commit()

    logger.info(f"Password changed for user: {user.username}")
    return True
