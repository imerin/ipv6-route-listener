"""Packet filtering logic for Router Advertisements."""

from scapy.all import (
    ICMPv6ND_RA,
    ICMPv6NDOptPrefixInfo,
    ICMPv6NDOptRouteInfo,
)

class PacketFilter:
    """Handles filtering logic for Router Advertisement packets."""
    
    def __init__(self, route_configurator):
        """Initialize the packet filter.
        
        Args:
            route_configurator: The route configurator instance to check for existing routes
        """
        self.route_configurator = route_configurator
        self.initial_check_done = False
    
    def should_process_packet(self, packet, logger=None):
        """Determine if a packet should be processed.
        
        Args:
            packet: The Router Advertisement packet to check
            logger: Optional logger instance for debug output
            
        Returns:
            bool: True if the packet should be processed, False if it should be ignored
        """
        try:
            # Get the Router Advertisement layer
            ra = packet[ICMPv6ND_RA]
            
            # Check if the packet has the expected structure
            if not hasattr(ra, 'payload'):
                if logger and logger.verbose:
                    logger.debug("❌ No payload in Router Advertisement")
                return False

            # Track if we found any new routes to process
            found_new = False

            # Check for ULA prefixes or routes
            for opt in ra.payload:
                if isinstance(opt, ICMPv6NDOptPrefixInfo):
                    try:
                        prefix_str = str(opt.prefix)
                        prefix_len = opt.prefixlen
                        if prefix_str.startswith("fd"):
                            # Check if this prefix is already configured
                            if not self.route_configurator.is_configured(prefix_str, prefix_len, is_prefix=True):
                                found_new = True
                            elif not self.initial_check_done and logger:
                                logger.info(f"✓ ULA prefix already configured: {prefix_str}/{prefix_len}")
                            elif logger and logger.verbose:
                                logger.debug(f"⏭️  ULA prefix already configured: {prefix_str}/{prefix_len}")
                    except AttributeError:
                        continue
                elif isinstance(opt, ICMPv6NDOptRouteInfo):
                    try:
                        prefix_str = str(opt.prefix)
                        prefix_len = opt.plen  # Route Info uses 'plen' instead of 'prefixlen'
                        if prefix_str.startswith("fd"):
                            # Check if this route is already configured
                            if not self.route_configurator.is_configured(prefix_str, prefix_len, is_prefix=False):
                                found_new = True
                            elif not self.initial_check_done and logger:
                                logger.info(f"✓ ULA route already configured: {prefix_str}/{prefix_len}")
                            elif logger and logger.verbose:
                                logger.debug(f"⏭️  ULA route already configured: {prefix_str}/{prefix_len}")
                    except AttributeError:
                        continue

            # Mark initial check as done after first packet
            self.initial_check_done = True
                        
            # Return True if we found new routes to process
            return found_new
            
        except Exception as e:
            if logger and logger.verbose:
                logger.error(f"Error checking packet: {str(e)}")
            return False 