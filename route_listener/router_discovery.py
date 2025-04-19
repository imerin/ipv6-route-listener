"""Router discovery module for IPv6 networks."""

import socket
import struct
import logging
from typing import Optional
import os
import subprocess

class RouterDiscovery:
    """Handles ICMPv6 Router Discovery functionality."""
    
    def __init__(self, interface: str, logger: Optional[logging.Logger] = None):
        self.interface = interface
        self.logger = logger or logging.getLogger(__name__)
        self.socket = None
        
    def discover_routers(self) -> None:
        """Send Router Solicitation and listen for Router Advertisements."""
        try:
            # Create ICMPv6 socket
            self.logger.debug("Creating ICMPv6 socket...")
            self.socket = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
            
            # Set socket options
            self.logger.debug("Setting socket options...")
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack("ll", 5, 0))
            
            # Get interface index using ip command
            self.logger.debug(f"Getting interface index for {self.interface}...")
            try:
                result = subprocess.run(
                    ["ip", "link", "show", "dev", self.interface],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Extract interface index from output
                for line in result.stdout.splitlines():
                    if self.interface in line:
                        if_index = int(line.split(':')[0])
                        self.logger.debug(f"Found interface index: {if_index}")
                        break
                else:
                    raise ValueError(f"Interface {self.interface} not found")
            except (subprocess.CalledProcessError, ValueError) as e:
                self.logger.error(f"Error getting interface index: {str(e)}")
                return
            
            # Join the all-routers multicast group
            self.logger.debug("Joining all-routers multicast group...")
            # Use the IPv6 multicast address for all routers (ff02::2)
            mreq = socket.inet_pton(socket.AF_INET6, "ff02::2") + struct.pack("@I", if_index)
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)
            
            # Send Router Solicitation
            self.logger.debug("Sending Router Solicitation...")
            rs_packet = self._create_router_solicitation()
            self.socket.sendto(rs_packet, ("ff02::2", 0, 0, if_index))
            
            # Listen for Router Advertisement
            self.logger.debug("Listening for Router Advertisements...")
            while True:
                try:
                    data, addr = self.socket.recvfrom(65535)
                    if self._is_router_advertisement(data):
                        self.logger.info(f"Received Router Advertisement from {addr[0]}")
                        self.logger.debug(f"Packet data: {data.hex()}")
                except socket.timeout:
                    self.logger.debug("Timeout waiting for Router Advertisements")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error during router discovery: {str(e)}")
            if hasattr(self.logger, 'debug'):
                self.logger.debug(f"Error type: {type(e).__name__}")
                self.logger.debug(f"Error details: {str(e)}")
        finally:
            if self.socket:
                self.socket.close()
                
    def _create_router_solicitation(self) -> bytes:
        """Create an ICMPv6 Router Solicitation packet."""
        # ICMPv6 header for Router Solicitation
        icmpv6 = struct.pack('!BBHI',
                            133,  # Type: Router Solicitation
                            0,    # Code
                            0,    # Checksum (will be calculated)
                            0     # Reserved
        )
        
        # Source Link-Layer Address option
        sllao = struct.pack('!BB',
                           1,    # Type: Source Link-Layer Address
                           1     # Length: 1 (8 bytes)
        )
        
        return icmpv6 + sllao
        
    def _is_router_advertisement(self, data: bytes) -> bool:
        """Check if the packet is a Router Advertisement."""
        return len(data) >= 8 and data[0] == 134  # Type 134 is Router Advertisement 