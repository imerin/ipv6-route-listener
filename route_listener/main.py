#!/usr/bin/env python3
"""Main module for the ICMPv6 RA listener."""

import sys
import argparse
from scapy.all import sniff, conf, get_if_list

from .logger import Logger, LoggerConfig
from .route_configurator import RouteConfigurator
from .packet_handler import PacketHandler

# Banner for the application
BANNER = """
╔════════════════════════════════════════════════════════════════════════════╗
║                     🚀 ICMPv6 RA Listener v0.1.0                          ║
║                                                                          ║
║  Monitors Thread Border Routers for IPv6 Router Advertisements           ║
║  and displays ULA prefixes and routes for network configuration          ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

def main():
    """Main entry point for the RA listener."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ICMPv6 RA listener for Thread route monitoring")
    parser.add_argument("-i", "--interface", default="eth0", 
                        help="Network interface to listen on (default: eth0)")
    parser.add_argument("--log-ignored", action="store_true",
                        help="Log ignored routes (non-ULA prefixes)")
    args = parser.parse_args()

    # Initialize components
    logger = Logger(LoggerConfig(log_ignored=args.log_ignored))
    configurator = RouteConfigurator(logger)
    handler = PacketHandler(configurator, logger, args.interface)

    logger.banner(BANNER)

    # Print system information
    logger.info("🔍 System Information:")
    logger.info(f"  Python version: {sys.version}")
    logger.info(f"  Scapy version: {conf.version}")
    logger.info(f"  Log ignored routes: {'Yes' if args.log_ignored else 'No'}")

    # List available interfaces
    interfaces = get_if_list()
    logger.info(f"  Available interfaces: {', '.join(interfaces)}")

    # Check if the specified interface exists
    if not interfaces:
        logger.error("❌ No network interfaces found!")
        return 1

    if args.interface not in interfaces:
        logger.error(f"❌ Error: Interface '{args.interface}' not found!")
        logger.error("  Please specify a valid interface using the -i option.")
        logger.error(f"  Available interfaces: {', '.join(interfaces)}")
        return 1

    logger.info(f"📡 Listening for Router Advertisements on interface '{args.interface}'...")
    logger.info("Press Ctrl+C to stop")

    # Force output to be flushed immediately
    sys.stdout.flush()

    try:
        # Start sniffing
        sniff(filter="icmp6", iface=args.interface, prn=handler.handle)
    except KeyboardInterrupt:
        logger.info("👋 Stopping RA listener...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 