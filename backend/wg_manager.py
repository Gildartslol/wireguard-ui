from wireguard_tools import WireguardDevice, WireguardKey, WireguardConfig, WireguardPeer
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)


class WireGuardManager:
    """Manager class for WireGuard operations using wireguard-tools"""

    def __init__(self, interface="wg0"):
        self.interface = interface

    def get_active_peers(self) -> List[Dict]:
        """
        Get list of currently connected peers with real-time data

        Returns:
            List of peer dictionaries with connection information
        """
        try:
            device = WireguardDevice.get(self.interface)
            config = device.get_config()

            peers = []
            for peer in self._iter_peers(config.peers):
                endpoint_host = getattr(peer, 'endpoint_host', None)
                endpoint_port = getattr(peer, 'endpoint_port', None)

                # Newer versions expose a nested endpoint object instead of host/port attrs
                if (not endpoint_host or not endpoint_port) and hasattr(peer, 'endpoint'):
                    endpoint_obj = getattr(peer, 'endpoint')
                    if endpoint_obj:
                        endpoint_host = getattr(endpoint_obj, 'host', endpoint_host)
                        endpoint_port = getattr(endpoint_obj, 'port', endpoint_port)

                endpoint = None
                if endpoint_host and endpoint_port:
                    endpoint = f"{endpoint_host}:{endpoint_port}"

                public_key_obj = getattr(peer, 'public_key', None)
                if public_key_obj is None:
                    public_key_obj = getattr(peer, 'key', None)
                if public_key_obj is None:
                    public_key_obj = peer

                allowed_ips_raw = getattr(peer, 'allowed_ips', None)
                allowed_ips = []
                if allowed_ips_raw:
                    allowed_ips = [str(ip) for ip in allowed_ips_raw]

                last_handshake = getattr(peer, 'last_handshake_time', None)
                transfer_rx = getattr(peer, 'receive_bytes', 0) or 0
                transfer_tx = getattr(peer, 'transmit_bytes', 0) or 0

                if last_handshake is None:
                    stats_obj = getattr(peer, 'statistics', None) or getattr(peer, 'stats', None)
                    if stats_obj:
                        last_handshake = getattr(stats_obj, 'last_handshake', last_handshake)
                        if not last_handshake:
                            last_handshake = getattr(stats_obj, 'latest_handshake', last_handshake)
                        transfer_rx = getattr(stats_obj, 'rx_bytes', transfer_rx) or 0
                        transfer_tx = getattr(stats_obj, 'tx_bytes', transfer_tx) or 0

                if hasattr(last_handshake, 'timestamp'):  # handle datetime wrappers
                    last_handshake = last_handshake.timestamp()

                peer_data = {
                    'public_key': str(public_key_obj),
                    'endpoint': endpoint,
                    'allowed_ips': allowed_ips,
                    'latest_handshake': last_handshake.isoformat() if hasattr(last_handshake, 'isoformat') else None,
                    'transfer_rx': transfer_rx,
                    'transfer_tx': transfer_tx,
                    'persistent_keepalive': getattr(peer, 'persistent_keepalive', None),
                    'connected': self._is_connected(last_handshake)
                }
                peers.append(peer_data)

            return peers

        except Exception as e:
            logger.error(f"Error getting active peers: {e}")
            raise

    @staticmethod
    def _iter_peers(peers):
        """Handle API changes where peers can be list or dict."""
        if peers is None:
            return []
        if isinstance(peers, dict):
            return peers.values()
        return peers

    def _is_connected(self, handshake_time: Optional[datetime]) -> bool:
        """
        Consider peer connected if handshake occurred within last 3 minutes

        Args:
            handshake_time: Last handshake datetime

        Returns:
            True if connected, False otherwise
        """
        if not handshake_time:
            return False
        return datetime.now() - handshake_time < timedelta(minutes=3)

    def add_peer(self, public_key: str, allowed_ips: List[str],
                 endpoint: Optional[str] = None,
                 preshared_key: Optional[str] = None) -> bool:
        """
        Add new peer to WireGuard interface

        Args:
            public_key: Peer's public key
            allowed_ips: List of allowed IP addresses/ranges
            endpoint: Optional endpoint address
            preshared_key: Optional preshared key

        Returns:
            True if successful
        """
        try:
            # Validate public key format
            if not self._validate_public_key(public_key):
                raise ValueError(f"Invalid public key format: {public_key}")

            device = WireguardDevice.get(self.interface)
            config = device.get_config()

            # Check if peer already exists
            existing_peer = next((p for p in config.peers if p.public_key == public_key), None)
            if existing_peer:
                raise ValueError(f"Peer with public key {public_key} already exists")

            # Create new peer configuration
            new_peer = WireguardPeer(
                public_key=public_key,
                allowed_ips=allowed_ips,
                preshared_key=preshared_key if preshared_key else None
            )

            # Parse endpoint if provided
            if endpoint:
                host, port = self._parse_endpoint(endpoint)
                new_peer.endpoint_host = host
                new_peer.endpoint_port = port

            config.peers.append(new_peer)
            device.set_config(config)

            logger.info(f"Added peer: {public_key[:12]}...")
            return True

        except Exception as e:
            logger.error(f"Error adding peer: {e}")
            raise

    def remove_peer(self, public_key: str) -> bool:
        """
        Remove peer from WireGuard interface

        Args:
            public_key: Peer's public key to remove

        Returns:
            True if successful
        """
        try:
            device = WireguardDevice.get(self.interface)
            config = device.get_config()

            # Find and remove the peer
            initial_count = len(config.peers)
            config.peers = [p for p in config.peers if p.public_key != public_key]

            if len(config.peers) == initial_count:
                raise ValueError(f"Peer with public key {public_key} not found")

            device.set_config(config)

            logger.info(f"Removed peer: {public_key[:12]}...")
            return True

        except Exception as e:
            logger.error(f"Error removing peer: {e}")
            raise

    def update_peer(self, public_key: str, allowed_ips: Optional[List[str]] = None,
                    endpoint: Optional[str] = None) -> bool:
        """
        Update existing peer configuration

        Args:
            public_key: Peer's public key
            allowed_ips: New allowed IPs (optional)
            endpoint: New endpoint (optional)

        Returns:
            True if successful
        """
        try:
            device = WireguardDevice.get(self.interface)
            config = device.get_config()

            # Find the peer
            peer = next((p for p in config.peers if p.public_key == public_key), None)
            if not peer:
                raise ValueError(f"Peer with public key {public_key} not found")

            # Update allowed IPs if provided
            if allowed_ips is not None:
                peer.allowed_ips = allowed_ips

            # Update endpoint if provided
            if endpoint:
                host, port = self._parse_endpoint(endpoint)
                peer.endpoint_host = host
                peer.endpoint_port = port

            device.set_config(config)

            logger.info(f"Updated peer: {public_key[:12]}...")
            return True

        except Exception as e:
            logger.error(f"Error updating peer: {e}")
            raise

    @staticmethod
    def generate_keypair() -> Dict[str, str]:
        """
        Generate new WireGuard key pair

        Returns:
            Dictionary with 'private_key' and 'public_key'
        """
        try:
            private_key = WireguardKey.generate()
            public_key = private_key.public_key()

            return {
                'private_key': str(private_key),
                'public_key': str(public_key)
            }

        except Exception as e:
            logger.error(f"Error generating keypair: {e}")
            raise

    @staticmethod
    def generate_preshared_key() -> str:
        """
        Generate new preshared key

        Returns:
            Preshared key string
        """
        try:
            return str(WireguardKey.generate())
        except Exception as e:
            logger.error(f"Error generating preshared key: {e}")
            raise

    @staticmethod
    def generate_peer_config(peer_name: str, private_key: str,
                           server_public_key: str, endpoint: str,
                           allowed_ips: List[str], address: str,
                           dns: str = "1.1.1.1") -> str:
        """
        Generate peer .conf file content

        Args:
            peer_name: Name of the peer
            private_key: Peer's private key
            server_public_key: Server's public key
            endpoint: Server endpoint (host:port)
            allowed_ips: List of allowed IP ranges
            address: Peer's VPN IP address
            dns: DNS server (default: 1.1.1.1)

        Returns:
            Configuration file content as string
        """
        config = f"""# {peer_name} - WireGuard Configuration
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[Interface]
PrivateKey = {private_key}
Address = {address}
DNS = {dns}

[Peer]
PublicKey = {server_public_key}
Endpoint = {endpoint}
AllowedIPs = {', '.join(allowed_ips)}
PersistentKeepalive = 25
"""
        return config

    def get_interface_info(self) -> Dict:
        """
        Get WireGuard interface information

        Returns:
            Dictionary with interface information
        """
        try:
            device = WireguardDevice.get(self.interface)
            config = device.get_config()

            return {
                'interface': self.interface,
                'public_key': config.public_key if hasattr(config, 'public_key') else None,
                'listen_port': config.listen_port if hasattr(config, 'listen_port') else None,
                'peer_count': len(config.peers),
                'peers': self.get_active_peers()
            }

        except Exception as e:
            logger.error(f"Error getting interface info: {e}")
            raise

    @staticmethod
    def _validate_public_key(key: str) -> bool:
        """
        Validate public key format (base64, 44 characters)

        Args:
            key: Public key string

        Returns:
            True if valid
        """
        return bool(re.match(r'^[A-Za-z0-9+/]{43}=$', key))

    @staticmethod
    def _parse_endpoint(endpoint: str) -> tuple:
        """
        Parse endpoint string into host and port

        Args:
            endpoint: Endpoint string (host:port)

        Returns:
            Tuple of (host, port)
        """
        if ':' not in endpoint:
            raise ValueError(f"Invalid endpoint format: {endpoint}. Expected host:port")

        parts = endpoint.rsplit(':', 1)
        host = parts[0].strip('[]')  # Remove brackets for IPv6
        port = int(parts[1])

        return host, port

    def get_stats(self) -> Dict:
        """
        Get statistics about WireGuard connections

        Returns:
            Dictionary with connection statistics
        """
        try:
            peers = self.get_active_peers()
            connected_count = sum(1 for p in peers if p['connected'])
            total_rx = sum(p['transfer_rx'] for p in peers)
            total_tx = sum(p['transfer_tx'] for p in peers)

            return {
                'total_peers': len(peers),
                'connected_peers': connected_count,
                'disconnected_peers': len(peers) - connected_count,
                'total_transfer_rx': total_rx,
                'total_transfer_tx': total_tx,
                'total_transfer': total_rx + total_tx
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise
