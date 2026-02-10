#!/bin/bash
# Single entry point: ensure deps, then start bridge (relay starts automatically if possible).
# Usage: ./run.sh   or   ./run.sh 127.0.0.1

set -e

UDITA_ROOT="$(cd "$(dirname "$0")" && pwd)"
BRIDGE="$UDITA_ROOT/bridge"

# Ensure deps (idempotent)
if ! python3 -c "import flask" 2>/dev/null; then
    echo "[..] Installing dependencies (first run)..."
    python3 -m pip install -r "$BRIDGE/requirements.txt" -q
fi

# Start bridge (handles relay + server)
exec "$BRIDGE/start.sh" "$@"
