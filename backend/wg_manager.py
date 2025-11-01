import subprocess
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WireGuardManager:
    """Manager class for WireGuard operations using subprocess and wg command"""

    def __init__(self, interface="wg0"):
        self.interface = interface
        self.sudo_prefix = ["sudo", "-n"]  # -n means non-interactive (will fail if password required)

    def get_active_peers(self) -> List[Dict]:
        """
        Get list of currently connected peers with real-time data

        Uses 'wg show <interface> dump' for machine-readable output

        Returns:
            List of peer dictionaries with connection information
        """
        try:
            cmd = self.sudo_prefix + ["wg", "show", self.interface, "dump"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            lines = result.stdout.strip().split('\n')
            if not lines or len(lines) < 1:
                return []

            # First line is interface info: private-key public-key listen-port fwmark
            # Skip it and process peer lines
            peers = []
            for line in lines[1:]:
                if not line.strip():
                    continue

                peer_data = self._parse_dump_line(line)
                if peer_data:
                    peers.append(peer_data)

            return peers

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running wg show: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error getting active peers: {e}")
            raise

    def _parse_dump_line(self, line: str) -> Optional[Dict]:
        """
        Parse a peer line from 'wg show dump' output

        Format: public-key preshared-key endpoint allowed-ips latest-handshake-sec rx-bytes tx-bytes persistent-keepalive

        Args:
            line: Line from wg show dump output

        Returns:
            Dictionary with peer data or None if invalid
        """
        try:
            parts = line.split('\t')
            if len(parts) < 8:
                return None

            public_key = parts[0]
            # preshared_key = parts[1]  # (none) if not set
            endpoint = parts[2] if parts[2] != "(none)" else None
            allowed_ips_str = parts[3]
            handshake_seconds = parts[4]
            transfer_rx = int(parts[5]) if parts[5] else 0
            transfer_tx = int(parts[6]) if parts[6] else 0
            persistent_keepalive = parts[7] if parts[7] != "off" else None

            # Parse allowed IPs
            allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]

            # Parse handshake time
            latest_handshake = None
            handshake_dt = None
            try:
                handshake_sec = int(handshake_seconds)
                if handshake_sec > 0:
                    handshake_dt = datetime.now() - timedelta(seconds=handshake_sec)
                    latest_handshake = handshake_dt.isoformat()
            except (ValueError, TypeError):
                pass

            # Determine if connected (handshake within last 3 minutes)
            connected = self._is_connected(handshake_dt)

            return {
                'public_key': public_key,
                'endpoint': endpoint,
                'allowed_ips': allowed_ips,
                'latest_handshake': latest_handshake,
                'transfer_rx': transfer_rx,
                'transfer_tx': transfer_tx,
                'persistent_keepalive': persistent_keepalive,
                'connected': connected
            }

        except Exception as e:
            logger.error(f"Error parsing dump line: {e}")
            return None

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
            endpoint: Optional endpoint address (host:port)
            preshared_key: Optional preshared key

        Returns:
            True if successful
        """
        try:
            # Validate public key format
            if not self._validate_public_key(public_key):
                raise ValueError(f"Invalid public key format: {public_key}")

            # Build command: sudo wg set wg0 peer <key> allowed-ips <ips> [endpoint <endpoint>] [preshared-key <psk>]
            cmd = self.sudo_prefix + ["wg", "set", self.interface, "peer", public_key]

            # Add allowed IPs
            cmd.extend(["allowed-ips", ",".join(allowed_ips)])

            # Add endpoint if provided
            if endpoint:
                cmd.extend(["endpoint", endpoint])

            # Add preshared key if provided
            if preshared_key:
                cmd.extend(["preshared-key", preshared_key])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            logger.info(f"Added peer: {public_key[:12]}...")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error adding peer: {e.stderr}")
            raise
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
            cmd = self.sudo_prefix + ["wg", "set", self.interface, "peer", public_key, "remove"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            logger.info(f"Removed peer: {public_key[:12]}...")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error removing peer: {e.stderr}")
            raise
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
            cmd = self.sudo_prefix + ["wg", "set", self.interface, "peer", public_key]

            # Add allowed IPs if provided
            if allowed_ips is not None:
                cmd.extend(["allowed-ips", ",".join(allowed_ips)])

            # Add endpoint if provided
            if endpoint:
                cmd.extend(["endpoint", endpoint])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            logger.info(f"Updated peer: {public_key[:12]}...")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating peer: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error updating peer: {e}")
            raise

    @staticmethod
    def generate_keypair() -> Dict[str, str]:
        """
        Generate new WireGuard key pair using wg genkey and wg pubkey

        Returns:
            Dictionary with 'private_key' and 'public_key'
        """
        try:
            # Generate private key
            genkey_result = subprocess.run(
                ["wg", "genkey"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            private_key = genkey_result.stdout.strip()

            # Generate public key from private key
            pubkey_result = subprocess.run(
                ["wg", "pubkey"],
                input=private_key,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            public_key = pubkey_result.stdout.strip()

            return {
                'private_key': private_key,
                'public_key': public_key
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Error generating keypair: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error generating keypair: {e}")
            raise

    @staticmethod
    def generate_preshared_key() -> str:
        """
        Generate new preshared key using wg genpsk

        Returns:
            Preshared key string
        """
        try:
            result = subprocess.run(
                ["wg", "genpsk"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            logger.error(f"Error generating preshared key: {e.stderr}")
            raise
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
            # Get interface info using 'wg show wg0'
            cmd = self.sudo_prefix + ["wg", "show", self.interface]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            output = result.stdout

            # Parse interface information
            public_key = None
            listen_port = None

            for line in output.split('\n'):
                if 'public key:' in line:
                    public_key = line.split('public key:')[1].strip()
                elif 'listening port:' in line:
                    listen_port = int(line.split('listening port:')[1].strip())

            peers = self.get_active_peers()

            return {
                'interface': self.interface,
                'public_key': public_key,
                'listen_port': listen_port,
                'peer_count': len(peers),
                'peers': peers
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting interface info: {e.stderr}")
            raise
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
