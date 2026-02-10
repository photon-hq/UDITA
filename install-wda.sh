#!/bin/bash
# Build and run WebDriverAgent on the first USB-connected iPhone.
# One-time: open wda/WebDriverAgent.xcodeproj in Xcode and set Signing (Team + Bundle ID) for both targets.
# Then run: ./install-wda.sh

set -e

UDITA_ROOT="$(cd "$(dirname "$0")" && pwd)"
WDA="$UDITA_ROOT/wda"
PROJECT="$WDA/WebDriverAgent.xcodeproj"

if [ ! -d "$PROJECT" ]; then
    echo "[FAIL] WDA project not found at wda/WebDriverAgent.xcodeproj"
    exit 1
fi

# Get first connected physical iPhone UDID
UDID=""
if command -v python3 &>/dev/null; then
    UDID=$(python3 -c "
try:
    from pymobiledevice3.usbmux import list_devices
    devs = list_devices()
    if devs: print(devs[0].serial)
except Exception: pass
" 2>/dev/null)
fi
if [ -z "$UDID" ] && command -v idevice_id &>/dev/null; then
    UDID=$(idevice_id -l 2>/dev/null | head -1)
fi
if [ -z "$UDID" ]; then
    # instruments -s devices: "iPhone (12.4) (UDID)"
    UDID=$(instruments -s devices 2>/dev/null | grep -i iphone | grep -v Simulator | head -1 | sed -n 's/.*(\([0-9A-F\-]\{25,\}\)).*/\1/p')
fi

if [ -z "$UDID" ]; then
    echo "[FAIL] No iPhone found. Connect the device via USB, unlock it, and trust this Mac."
    exit 1
fi

echo "[OK] Device: $UDID"
echo "Building and running WDA (first time may prompt for signing)..."
echo ""

cd "$WDA"
xcodebuild test-without-building \
  -project WebDriverAgent.xcodeproj \
  -scheme WebDriverAgentRunner \
  -destination "id=$UDID" \
  -allowProvisioningUpdates

echo ""
echo "[OK] WDA is running on the device. Start the relay (./start.sh will try automatically) or use Wi‑Fi IP in the dashboard."
