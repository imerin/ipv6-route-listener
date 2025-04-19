#!/bin/sh
# Configure IPv6 routes for Matter/Thread devices
# This script is used by the route listener to configure IPv6 routes
# for Matter/Thread device communication.

set -e

# Get interface, prefix, and router from environment variables
IFACE=${IFACE:-"eth0"}
PREFIX=${PREFIX:-""}
ROUTER=${ROUTER:-""}

# Check if required parameters are provided
if [ -z "$PREFIX" ] || [ -z "$ROUTER" ]; then
    echo "❌ Error: PREFIX and ROUTER environment variables must be provided"
    echo "Usage: PREFIX=<prefix> ROUTER=<router> [IFACE=<interface>] $0"
    exit 1
fi

# Configure the route
echo "🔍 Configuring route: $PREFIX via $ROUTER on interface $IFACE"

# Check if route already exists and remove it
ip -6 route show | grep -q "$PREFIX" && {
    echo "🧹 Removing existing route to $PREFIX"
    ip -6 route del "$PREFIX" 2>/dev/null || true
}

# Add the new route
echo "➕ Adding route to $PREFIX via $ROUTER on $IFACE"
ip -6 route add "$PREFIX" via "$ROUTER" dev "$IFACE" && echo "✅ Added" 