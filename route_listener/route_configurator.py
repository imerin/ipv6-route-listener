"""Route configuration module for IPv6 routes."""

import os
import subprocess
import re
from typing import Optional, Dict, Set
from dataclasses import dataclass
from .logger import Logger

@dataclass
class Route:
    """Represents an IPv6 route."""
    prefix: str
    router: str
    interface: str

    def __str__(self) -> str:
        return f"{self.prefix} via {self.router}"

    def is_ula(self) -> bool:
        """Check if this is a ULA prefix (starts with 'fd')."""
        return self.prefix.startswith("fd")
    
    def get_route_key(self) -> str:
        """Get a unique key for this route."""
        return f"{self.prefix}|{self.router}"

class RouteConfigurator:
    """Handles the configuration of IPv6 routes."""

    def __init__(self, logger: Logger):
        """Initialize the route configurator."""
        self.logger = logger
        self.seen_routes: Dict[str, str] = {}  # prefix -> router mapping
        self._configure_script()

    def _configure_script(self):
        """Configure the route configuration script."""
        # Get the script path relative to this file
        self.script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "bin",
            "configure-ipv6-route.sh"
        )
        # Make sure the script is executable
        if os.path.exists(self.script_path):
            os.chmod(self.script_path, 0o755)

    def configure(self, route: Route) -> bool:
        """Configure a route on the host system."""
        if not route.prefix or not route.router:
            return False

        # Check if this is a ULA prefix
        if not route.is_ula():
            self.logger.ignored(f"⏭️  Ignoring non-ULA prefix: {route}")
            self.logger.ignored(f"   ℹ️  Only ULA prefixes (starting with 'fd') are configured for Matter/Thread device communication")
            self.logger.ignored(f"   ℹ️  ULA prefixes are used for local network communication and are not routable on the public internet")
            return False

        # Check if we've already processed this exact route
        route_key = route.get_route_key()
        if route_key in self.seen_routes:
            self.logger.info(f"⏭️  Route already configured: {route}")
            return True

        # Check if we've seen this prefix before with a different router
        if route.prefix in self.seen_routes:
            previous_router = self.seen_routes[route.prefix]
            self.logger.info(f"🔄 Updating route: {route} (previous: {previous_router})")
            
            # The script will handle removing the previous route
        else:
            self.logger.info(f"🔧 Configuring new route: {route}")

        try:
            # Run the script with the route parameters
            result = subprocess.run(
                [self.script_path],
                env={
                    "PREFIX": route.prefix,
                    "ROUTER": route.router,
                    "IFACE": route.interface,
                    **os.environ
                },
                capture_output=True,
                text=True,
                check=True
            )

            self.logger.info(f"✅ Route configuration output:\n{result.stdout}")

            # Update seen routes - store both the full route key and just the prefix
            self.seen_routes[route_key] = route.router
            self.seen_routes[route.prefix] = route.router
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Error configuring route: {e}")
            self.logger.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            return False 