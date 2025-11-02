from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Peer(db.Model):
    """WireGuard peer metadata"""
    __tablename__ = 'peers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_key = db.Column(db.String(44), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    allowed_ips = db.Column(db.Text, nullable=False)
    endpoint = db.Column(db.String(100))
    description = db.Column(db.Text)
    preshared_key = db.Column(db.String(44))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationship to user
    creator = db.relationship('User', backref='created_peers')

    def to_dict(self):
        """Convert peer to dictionary"""
        return {
            'id': self.id,
            'public_key': self.public_key,
            'name': self.name,
            'allowed_ips': self.allowed_ips.split(',') if self.allowed_ips else [],
            'endpoint': self.endpoint,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }

    def __repr__(self):
        return f'<Peer {self.name} ({self.public_key[:12]}...)>'


class ConnectionHistory(db.Model):
    """Historical tracking of peer connections"""
    __tablename__ = 'connection_history'

    id = db.Column(db.Integer, primary_key=True)
    peer_id = db.Column(db.String(36), db.ForeignKey('peers.id'))
    public_key = db.Column(db.String(44), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)  # 'connected', 'disconnected'
    endpoint = db.Column(db.String(100))
    latest_handshake = db.Column(db.DateTime)
    transfer_rx = db.Column(db.BigInteger, default=0)
    transfer_tx = db.Column(db.BigInteger, default=0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationship to peer
    peer = db.relationship('Peer', backref='connection_history')

    def to_dict(self):
        """Convert connection history to dictionary"""
        return {
            'id': self.id,
            'peer_id': self.peer_id,
            'public_key': self.public_key,
            'status': self.status,
            'endpoint': self.endpoint,
            'latest_handshake': self.latest_handshake.isoformat() if self.latest_handshake else None,
            'transfer_rx': self.transfer_rx,
            'transfer_tx': self.transfer_tx,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }

    def __repr__(self):
        return f'<ConnectionHistory {self.public_key[:12]}... {self.status} @ {self.recorded_at}>'
