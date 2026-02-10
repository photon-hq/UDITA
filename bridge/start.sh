#!/bin/bash
# Start bridge. If no device IP given and WDA not at 127.0.0.1, try to start USB relay automatically.
# Usage: ./start.sh [IP]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IPHONE_IP="${1:-}"
UDITA_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo " UDITA"
echo "======================================"
echo ""

# 1. Tunneld (optional)
if curl -s --connect-timeout 2 http://127.0.0.1:49151/ > /dev/null 2>&1; then
    echo "[OK] tunneld is running"
else
    echo "[..] tunneld not running (optional; needed for app launch when not on USB)"
fi

# 2. WDA reachability; if no IP and not reachable at 127.0.0.1, try to start relay automatically
WDA_HOST="${IPHONE_IP:-127.0.0.1}"
if curl -s --connect-timeout 2 "http://${WDA_HOST}:8100/status" 2>/dev/null | grep -q '"ready"'; then
    echo "[OK] WDA at ${WDA_HOST}:8100"
else
    if [ -z "$IPHONE_IP" ]; then
        # No IP given: try to start USB relay so 127.0.0.1 works
        RELAY_PID=""
        if command -v tidevice &>/dev/null; then
            if tidevice list 2>/dev/null | grep -q .; then
                echo "[..] Starting USB relay (tidevice)..."
                tidevice relay 8100 8100 &
                RELAY_PID=$!
                sleep 2
                if curl -s --connect-timeout 2 "http://127.0.0.1:8100/status" 2>/dev/null | grep -q '"ready"'; then
                    echo "[OK] Relay running; WDA at 127.0.0.1:8100"
                    IPHONE_IP="127.0.0.1"
                fi
            fi
        fi
        if [ -z "$IPHONE_IP" ] && command -v iproxy &>/dev/null; then
            if idevice_id -l &>/dev/null && [ -n "$(idevice_id -l 2>/dev/null)" ]; then
                echo "[..] Starting USB relay (iproxy)..."
                iproxy 8100 8100 &
                RELAY_PID=$!
                sleep 2
                if curl -s --connect-timeout 2 "http://127.0.0.1:8100/status" 2>/dev/null | grep -q '"ready"'; then
                    echo "[OK] Relay running; WDA at 127.0.0.1:8100"
                    IPHONE_IP="127.0.0.1"
                fi
            fi
        fi
        if [ -z "$IPHONE_IP" ]; then
            echo "[..] No WDA at 127.0.0.1. Run ./install-wda.sh with iPhone connected, or open the dashboard and pick a device."
        fi
    else
        echo "[..] No WDA at ${IPHONE_IP}:8100. Open the dashboard and pick a device."
    fi
fi

# 3. Start bridge
echo ""
echo "Starting bridge..."
echo ""

if [ -n "$IPHONE_IP" ]; then
    python3 "$SCRIPT_DIR/server.py" --ip "$IPHONE_IP"
else
    python3 "$SCRIPT_DIR/server.py"
fi
