#!/bin/bash
# UDITA setup — installs Mac deps and prints steps for iPhone (WDA).
# Run from UDITA: ./setup.sh

set -e

UDITA_ROOT="$(cd "$(dirname "$0")" && pwd)"
BRIDGE="$UDITA_ROOT/bridge"
WDA="$UDITA_ROOT/wda"

echo "======================================"
echo " UDITA setup"
echo "======================================"
echo ""

# 1. Python 3
if ! command -v python3 &>/dev/null; then
    echo "[FAIL] Python 3 not found. Install from python.org or: brew install python3"
    exit 1
fi
echo "[OK] Python 3: $(python3 --version)"

# 2. pip
if ! python3 -m pip --version &>/dev/null; then
    echo "[FAIL] pip not found. Run: python3 -m ensurepip --upgrade"
    exit 1
fi
echo "[OK] pip: $(python3 -m pip --version | head -1)"

# 3. Bridge deps
echo ""
echo "Installing bridge dependencies..."
python3 -m pip install -r "$BRIDGE/requirements.txt" -q
echo "[OK] bridge/requirements.txt installed"

# 4. Optional: pymobiledevice3 (for tunneld / app launch without USB)
if python3 -c "import pymobiledevice3" 2>/dev/null; then
    echo "[OK] pymobiledevice3 already installed"
else
    echo "[..] Optional: pymobiledevice3 (for app launch when not on USB)"
    read -p "Install pymobiledevice3? [y/N] " yn
    if [[ "$yn" =~ ^[Yy]$ ]]; then
        python3 -m pip install pymobiledevice3 -q
        echo "[OK] pymobiledevice3 installed"
    fi
fi

# 5. Xcode (for building WDA)
if ! xcode-select -p &>/dev/null; then
    echo "[!!] Xcode not found. Install Xcode from the App Store, then run: xcode-select --install"
else
    echo "[OK] Xcode: $(xcode-select -p)"
fi

# 6. WDA project present
if [ ! -d "$WDA/WebDriverAgent.xcodeproj" ]; then
    echo "[!!] WDA project not found at wda/WebDriverAgent.xcodeproj"
else
    echo "[OK] WDA project at wda/"
fi

echo ""
echo "======================================"
echo " Next steps"
echo "======================================"
echo ""
echo "1. Connect iPhone to Mac (USB). Unlock and trust the computer."
echo ""
echo "2. Open WDA in Xcode and set signing:"
echo "   open $WDA/WebDriverAgent.xcodeproj"
echo "   - Target WebDriverAgentRunner → Signing & Capabilities → your Team, unique Bundle ID"
echo "   - Same for WebDriverAgentLib"
echo "   - Select your iPhone in the toolbar, then Product → Test (Cmd+U)"
echo ""
echo "3. Connect iPhone (USB), unlock and trust. Then: ./install-wda.sh"
echo ""
echo "4. Run everything: ./run.sh   (or cd $BRIDGE && ./start.sh)"
echo "   Open http://localhost:5050 and pick a device."
echo ""
