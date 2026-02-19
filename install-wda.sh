#!/bin/bash
# DEPRECATED: Use ./start.sh instead
# This script is kept for backwards compatibility

echo "======================================"
echo " NOTICE"
echo "======================================"
echo ""
echo "This script is deprecated. Please use:"
echo ""
echo "  ./start.sh"
echo ""
echo "Running start.sh now..."
echo ""

UDITA_ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$UDITA_ROOT/start.sh"
