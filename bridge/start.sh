#!/bin/bash
# DEPRECATED: Use ../start.sh from project root instead
# This script is kept for backwards compatibility

echo "======================================"
echo " NOTICE"
echo "======================================"
echo ""
echo "Please run from project root:"
echo ""
echo "  cd .."
echo "  ./start.sh"
echo ""
echo "Redirecting..."
echo ""

sleep 2

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UDITA_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$UDITA_ROOT/start.sh" ]; then
    cd "$UDITA_ROOT"
    exec ./start.sh "$@"
fi

# Fallback to old behavior if new script doesn't exist
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IPHONE_IP="${1:-}"
UDITA_ROOT="$(dirname "$SCRIPT_DIR")"
PORT="${PORT:-5050}"

# Gently free a port (TERM then KILL) so we don't run two processes on it
close_port() {
    local port="$1"
    local pids
    pids=$(lsof -t -i ":$port" 2>/dev/null) || true
    if [ -n "$pids" ]; then
        echo "[..] Closing process(es) on port $port..."
        for pid in $pids; do kill -TERM "$pid" 2>/dev/null || true; done
        local w=0
        while [ $w -lt 5 ]; do
            sleep 1
            pids=$(lsof -t -i ":$port" 2>/dev/null) || true
            [ -z "$pids" ] && break
            w=$((w+1))
        done
        pids=$(lsof -t -i ":$port" 2>/dev/null) || true
        if [ -n "$pids" ]; then
            for pid in $pids; do kill -9 "$pid" 2>/dev/null || true; done
            sleep 1
        fi
        echo "[OK] Port $port free"
    fi
}

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
        # No IP given: try to start USB relay so 127.0.0.1 works (only one relay)
        RELAY_PID=""
        close_port 8100
        if command -v tidevice &>/dev/null; then
            if tidevice list 2>/dev/null | grep -q .; then
                # Only start relay if device is actually ready (avoids "Device not ready" when unplugged)
                if tidevice info 2>/dev/null | grep -q .; then
                    echo "[..] Starting USB relay (tidevice)..."
                    nohup tidevice relay 8100 8100 </dev/null >/dev/null 2>&1 &
                    RELAY_PID=$!
                    sleep 2
                    if curl -s --connect-timeout 2 "http://127.0.0.1:8100/status" 2>/dev/null | grep -q '"ready"'; then
                        echo "[OK] Relay running; WDA at 127.0.0.1:8100"
                        echo "     (When iPhone is unplugged / not charging, use its Wi-Fi IP in the dashboard instead.)"
                        IPHONE_IP="127.0.0.1"
                    fi
                else
                    echo "[..] USB device not ready (locked or unplugged). Use the device's Wi-Fi IP in the dashboard."
                fi
            fi
        fi
        if [ -z "$IPHONE_IP" ] && command -v iproxy &>/dev/null; then
            if idevice_id -l &>/dev/null && [ -n "$(idevice_id -l 2>/dev/null)" ]; then
                echo "[..] Starting USB relay (iproxy)..."
                nohup iproxy 8100 8100 </dev/null >/dev/null 2>&1 &
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

# 3. Gently free the bridge port if in use (avoid "Address already in use")
close_port "$PORT"

# 4. Start bridge
echo ""
echo "Starting bridge..."
echo ""

export PORT
if [ -n "$IPHONE_IP" ]; then
    python3 "$SCRIPT_DIR/server.py" --ip "$IPHONE_IP"
else
    python3 "$SCRIPT_DIR/server.py"
fi
