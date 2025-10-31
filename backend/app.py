from flask import Flask, send_from_directory
from flask_cors import CORS
from config import config
from models import db
from auth import init_auth
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.peers import peers_bp
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """
    Application factory for creating Flask app

    Args:
        config_name: Configuration to use (development, production, testing)

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    db.init_app(app)
    init_auth(app)

    # Setup CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['http://localhost:5173']),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(peers_bp)

    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")

    # Serve frontend static files (for production)
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve frontend files"""
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        else:
            return send_from_directory(frontend_dist, 'index.html')

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return {'status': 'healthy', 'service': 'wireguard-ui'}, 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 errors"""
        return {'error': 'Unauthorized'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors"""
        return {'error': 'Forbidden'}, 403

    logger.info(f"Flask app created with config: {config_name}")

    return app


if __name__ == '__main__':
    # Get environment
    env = os.getenv('FLASK_ENV', 'development')

    # Create app
    app = create_app(env)

    # Get server configuration
    host = app.config.get('SERVER_HOST', '0.0.0.0')
    port = app.config.get('SERVER_PORT', 5000)
    debug = app.config.get('DEBUG', False)

    logger.info(f"Starting WireGuard UI on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {env}")

    # Run app
    app.run(
        host=host,
        port=port,
        debug=debug
    )
