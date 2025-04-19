"""Packet handler module for ICMPv6 Router Advertisements."""

from scapy.all import sniff, IP, IPv6, ICMPv6ND_RA, ICMPv6ND_RS, ICMPv6NDOptPrefixInfo, send, conf, Raw
from .route_configurator import RouteConfigurator
from .logger import Logger
import logging
import threading
import time
import socket

class PacketHandler:
    """Handles ICMPv6 Router Advertisements packets."""
    
    def __init__(self, interface: str, route_configurator: RouteConfigurator, logger: Logger):
        self.interface = interface
        self.route_configurator = route_configurator
        self.logger = logger
        self.running = True
        self.last_processed = {}  # Track last processed RA from each source
        
    def start(self):
        """Start listening for Router Advertisements."""
        self.logger.info(f"📡 Listening for Router Advertisements on interface '{self.interface}'...")
        self.logger.info("Press Ctrl+C to stop")
        
        # Configure Scapy for IPv6
        conf.iface = self.interface
        conf.use_pcap = True  # Use libpcap for better performance
        
        # Start Router Solicitation thread
        rs_thread = threading.Thread(target=self._send_router_solicitations)
        rs_thread.daemon = True
        rs_thread.start()
        
        # Start packet capture with a more specific filter
        sniff(iface=self.interface, 
              prn=self._handle_packet, 
              filter="icmp6 and ip6[40] = 134",  # Only Router Advertisements
              store=0)
        
    def _send_router_solicitations(self):
        """Periodically send Router Solicitation messages."""
        while self.running:
            try:
                self.logger.debug("🔔 Sending Router Solicitation...")
                # Create Router Solicitation with proper IPv6 layer
                rs = IPv6(dst="ff02::2")/ICMPv6ND_RS()
                send(rs, iface=self.interface, verbose=False)
                time.sleep(5)  # Send every 5 seconds
            except Exception as e:
                self.logger.error(f"❌ Error sending Router Solicitation: {str(e)}")
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f"Error type: {type(e).__name__}")
                    self.logger.debug(f"Error details: {str(e)}")
        
    def _handle_packet(self, packet):
        """Handle received packets."""
        try:
            # Ensure we have an IPv6 packet
            if not IPv6 in packet:
                self.logger.debug("❌ Not an IPv6 packet")
                return
                
            # Check if it's a Router Advertisement
            if not ICMPv6ND_RA in packet:
                self.logger.debug("❌ Not a Router Advertisement")
                return
                
            src_addr = packet[IPv6].src
            
            # Check for duplicate RAs (within 1 second)
            current_time = time.time()
            if src_addr in self.last_processed:
                last_time = self.last_processed[src_addr]
                if current_time - last_time < 1:
                    self.logger.debug(f"⏭️  Skipping duplicate RA from {src_addr}")
                    return
            self.last_processed[src_addr] = current_time
            
            self.logger.info(f"🔔 Router Advertisement from {src_addr}")
            
            # Process the Router Advertisement
            self._process_router_advertisement(packet)
            
        except Exception as e:
            self.logger.error(f"❌ Error handling packet: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Error type: {type(e).__name__}")
                self.logger.debug(f"Error details: {str(e)}")
            
    def _process_router_advertisement(self, packet):
        """Process a Router Advertisement packet."""
        try:
            self.logger.debug("🔍 Processing Router Advertisement packet...")
            
            # Get the Router Advertisement layer
            ra = packet[ICMPv6ND_RA]
            
            # Check if the packet has the expected structure
            if not hasattr(ra, 'payload'):
                self.logger.debug("❌ Router Advertisement has no payload")
                return
                
            # Extract prefix information from ICMPv6NDOptPrefixInfo options
            prefix_options = []
            self.logger.debug("🔍 Looking for prefix options in payload...")
            
            # Process each option in the payload
            for opt in ra.payload:
                if isinstance(opt, ICMPv6NDOptPrefixInfo):
                    self.logger.debug(f"Found prefix option: {opt.prefix}/{opt.prefixlen}")
                    prefix_options.append(opt)
                    
            if not prefix_options:
                self.logger.debug("❌ No prefix options found in Router Advertisement")
                return
                
            # Process each prefix option
            for opt in prefix_options:
                prefix_str = str(opt.prefix)
                prefix_len = opt.prefixlen
                
                if prefix_str.startswith("fd"):
                    self.logger.info(f"🔍 Found ULA prefix: {prefix_str}/{prefix_len}")
                    self.route_configurator.configure(prefix_str, prefix_len)
                else:
                    self.logger.debug(f"⏭️  Ignoring non-ULA prefix: {prefix_str}/{prefix_len}")
        except Exception as e:
            self.logger.error(f"❌ Error processing Router Advertisement: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Error type: {type(e).__name__}")
                self.logger.debug(f"Error details: {str(e)}")
                
    def stop(self):
        """Stop the packet handler."""
        self.running = False 