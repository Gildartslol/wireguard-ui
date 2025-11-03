import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database Configuration
    # NOTE: Database URI is set dynamically in init_app based on WG_MOCK_MODE
    # This allows the environment variable to be set after class definition
    SQLALCHEMY_DATABASE_URI = None  # Will be set in init_app
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('FLASK_ENV', 'development') == 'development'

    # WireGuard Configuration
    WG_INTERFACE = os.getenv('WG_INTERFACE', 'wg0')
    WG_CONFIG_PATH = os.getenv('WG_CONFIG_PATH', '/etc/wireguard/wg0.conf')
    WG_SERVER_ADDRESS = os.getenv('WG_SERVER_ADDRESS', '10.0.0.1/24')
    WG_SERVER_PORT = int(os.getenv('WG_SERVER_PORT', '51820'))
    WG_SERVER_PUBLIC_KEY = os.getenv('WG_SERVER_PUBLIC_KEY', '')

    # Server Configuration
    SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.getenv('SERVER_PORT', '5000'))

    # Monitoring Configuration
    POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '300'))  # 5 minutes

    # Session Configuration
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        # Set database URI dynamically based on current environment
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            # Check if DATABASE_URI is explicitly set
            if os.getenv('DATABASE_URI'):
                app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
            else:
                # Otherwise, determine based on mock mode
                mock_mode = os.getenv('WG_MOCK_MODE', 'false').lower() == 'true'
                db_name = 'wg_dashboard_mock.db' if mock_mode else 'wg_dashboard.db'
                app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_name}'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
