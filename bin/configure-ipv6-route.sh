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

# Remove any existing routes for this prefix
# This includes both exact matches and higher-order subnets
echo "🧹 Removing any existing routes for $PREFIX and its subnets"

# Extract the base prefix without any length notation
BASE_PREFIX=$(echo "$PREFIX" | sed 's/\/.*$//')

# First, get all existing routes for this prefix
echo "   Checking for existing routes..."
ip -6 route show | grep "$BASE_PREFIX" | while read -r route; do
    if [ -n "$route" ]; then
        echo "   🗑️  Removing: $route"
        # Use eval to properly handle the route string
        eval "ip -6 route del $route" 2>/dev/null || true
    fi
done

# Try to remove any routes with specific prefix lengths
# This handles cases where the route might be specified with a prefix length
echo "   Checking for prefix length routes..."
for LENGTH in 64 48 32 16; do
    echo "   🗑️  Trying /$LENGTH routes..."
    ip -6 route del "$BASE_PREFIX/$LENGTH" 2>/dev/null || true
    ip -6 route del "$BASE_PREFIX/$LENGTH" via "$ROUTER" dev "$IFACE" 2>/dev/null || true
done

# Add the new route with /64 prefix length (standard for ULA)
echo "➕ Adding route to $BASE_PREFIX/64 via $ROUTER on $IFACE"
ip -6 route add "$BASE_PREFIX/64" via "$ROUTER" dev "$IFACE" && echo "✅ Added" 