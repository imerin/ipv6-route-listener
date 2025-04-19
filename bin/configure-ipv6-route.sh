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

# First, try to remove the exact route if it exists
ip -6 route del "$PREFIX" via "$ROUTER" dev "$IFACE" 2>/dev/null || true

# Then, try to remove any routes with prefix length notation
# Extract the prefix without any length notation
BASE_PREFIX=$(echo "$PREFIX" | sed 's/\/.*$//')
# Try common prefix lengths
for LENGTH in 64 48 32 16; do
    ip -6 route del "$BASE_PREFIX/$LENGTH" 2>/dev/null || true
done

# Add the new route
echo "➕ Adding route to $PREFIX via $ROUTER on $IFACE"
ip -6 route add "$PREFIX" via "$ROUTER" dev "$IFACE" && echo "✅ Added" 