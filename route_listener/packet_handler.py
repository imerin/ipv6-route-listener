"""Packet handler module for ICMPv6 Router Advertisements."""

from scapy.all import IPv6, ICMPv6ND_RA, ICMPv6NDOptPrefixInfo, ICMPv6NDOptRouteInfo
from .route_configurator import RouteConfigurator, Route
from .logger import Logger

class PacketHandler:
    """Handles ICMPv6 Router Advertisement packets."""

    def __init__(self, configurator: RouteConfigurator, logger: Logger, interface: str):
        """Initialize the packet handler."""
        self.configurator = configurator
        self.logger = logger
        self.interface = interface

    def handle(self, packet) -> None:
        """Handle an incoming packet."""
        if not packet.haslayer(ICMPv6ND_RA):
            return

        ra = packet[ICMPv6ND_RA]
        src = packet[IPv6].src
        self.logger.info(f"🔔 Router Advertisement from {src}")

        # Track prefixes and routes from this RA
        prefixes = []
        routes = []

        for opt in ra.iterpayloads():
            if isinstance(opt, ICMPv6NDOptPrefixInfo):
                prefix = opt.prefix
                self.logger.info(f"📡 Prefix: {prefix}", "  ")
                prefixes.append(prefix)
            elif isinstance(opt, ICMPv6NDOptRouteInfo):
                route = opt.prefix
                self.logger.info(f"📍 Route: {route}", "  ")
                routes.append(route)

        # Configure routes for each prefix
        for prefix in prefixes:
            self.configurator.configure(Route(prefix, src, self.interface))

        # Configure routes for each route
        for route in routes:
            self.configurator.configure(Route(route, src, self.interface)) 