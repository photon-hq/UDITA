#!/bin/bash
# UDITA - Universal Device Interface for Test Automation
# Usage: ./start.sh [stop]

set -e

UDITA_ROOT="$(cd "$(dirname "$0")" && pwd)"
WDA="$UDITA_ROOT/wda"
BRIDGE="$UDITA_ROOT/bridge"
SETUP_DONE="$UDITA_ROOT/.setup_done"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# STOP FUNCTION
# ============================================================================
stop_services() {
    echo "Stopping UDITA..."
    [ -f "$UDITA_ROOT/.wda.pid" ] && kill -9 $(cat "$UDITA_ROOT/.wda.pid") 2>/dev/null || true
    [ -f "$UDITA_ROOT/.relay.pid" ] && kill -9 $(cat "$UDITA_ROOT/.relay.pid") 2>/dev/null || true
    [ -f "$UDITA_ROOT/.bridge.pid" ] && kill -9 $(cat "$UDITA_ROOT/.bridge.pid") 2>/dev/null || true
    pkill -f "xcodebuild.*WebDriverAgent" 2>/dev/null || true
    pkill -f "tidevice relay" 2>/dev/null || true
    pkill -f "iproxy 8100" 2>/dev/null || true
    lsof -t -i :8100 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -t -i :5050 2>/dev/null | xargs kill -9 2>/dev/null || true
    rm -f "$UDITA_ROOT"/.*.pid
    echo "Stopped."
    exit 0
}

[ "$1" = "stop" ] && stop_services

# ============================================================================
# AUTO-DETECT TEAM ID FROM XCODE
# ============================================================================
auto_detect_team_id() {
    echo -e "${BLUE}[..] Auto-detecting Apple Developer Team ID...${NC}"
    
    # Try multiple methods to find Team ID
    local team_id=""
    
    # Method 1: From Xcode preferences
    if [ -f ~/Library/Preferences/com.apple.dt.Xcode.plist ]; then
        team_id=$(defaults read com.apple.dt.Xcode 2>/dev/null | grep -A 1 "teamID" | tail -1 | sed 's/[^A-Z0-9]//g' | head -1)
    fi
    
    # Method 2: From DerivedData (previous builds)
    if [ -z "$team_id" ]; then
        team_id=$(find ~/Library/Developer/Xcode/DerivedData -name "*.xcactivitylog" -exec strings {} \; 2>/dev/null | grep -o "DEVELOPMENT_TEAM = [A-Z0-9]*" | head -1 | awk '{print $3}')
    fi
    
    # Method 3: From security keychain (iPhone Developer certificates)
    if [ -z "$team_id" ]; then
        team_id=$(security find-identity -v -p codesigning 2>/dev/null | grep "iPhone Developer" | head -1 | grep -o "([A-Z0-9]\{10\})" | tr -d "()")
    fi
    
    # Method 4: From any existing provisioning profile
    if [ -z "$team_id" ]; then
        local profile=$(find ~/Library/MobileDevice/Provisioning\ Profiles -name "*.mobileprovision" -print0 2>/dev/null | xargs -0 ls -t | head -1)
        if [ -n "$profile" ]; then
            team_id=$(security cms -D -i "$profile" 2>/dev/null | grep -A 1 "TeamIdentifier" | tail -1 | sed 's/[^A-Z0-9]//g')
        fi
    fi
    
    echo "$team_id"
}

# ============================================================================
# SETUP (FIRST RUN)
# ============================================================================
if [ ! -f "$SETUP_DONE" ]; then
    echo "======================================"
    echo " UDITA - First Time Setup"
    echo "======================================"
    echo ""
    
    # Check Xcode
    if ! command -v xcodebuild &>/dev/null; then
        echo -e "${RED}[FAIL] Xcode not installed${NC}"
        echo "Install from: https://apps.apple.com/app/xcode/id497799835"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &>/dev/null; then
        echo -e "${RED}[FAIL] Python 3 not installed${NC}"
        echo "Install from: https://python.org"
        exit 1
    fi
    
    # Check/Install USB tools
    echo -e "${BLUE}[1/5] Checking USB tools...${NC}"
    if ! command -v tidevice &>/dev/null && ! command -v iproxy &>/dev/null; then
        echo -e "${YELLOW}[!] No USB tool found. Installing tidevice...${NC}"
        pip3 install -q tidevice 2>/dev/null || {
            echo -e "${YELLOW}[!] Could not auto-install. Please run manually:${NC}"
            echo "    pip3 install tidevice"
            echo "    OR: brew install libimobiledevice"
            exit 1
        }
    fi
    echo -e "${GREEN}[OK] USB tools ready${NC}"
    
    # Install Python deps
    echo ""
    echo -e "${BLUE}[2/5] Installing Python dependencies...${NC}"
    pip3 install -q flask flask-cors requests 2>/dev/null || {
        echo -e "${YELLOW}[!] Installing dependencies (may take a minute)...${NC}"
        pip3 install flask flask-cors requests
    }
    echo -e "${GREEN}[OK] Dependencies installed${NC}"
    
    # Auto-detect or ask for Team ID
    echo ""
    echo -e "${BLUE}[3/5] Configuring Apple Developer Team...${NC}"
    TEAM_ID=$(auto_detect_team_id)
    
    if [ -n "$TEAM_ID" ]; then
        echo -e "${GREEN}[OK] Auto-detected Team ID: $TEAM_ID${NC}"
        read -p "Use this Team ID? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            TEAM_ID=""
        fi
    fi
    
    if [ -z "$TEAM_ID" ]; then
        echo ""
        echo "Enter your Apple Developer Team ID"
        echo "(Find in: Xcode → Settings → Accounts → Team ID)"
        echo ""
        read -p "Team ID: " TEAM_ID
        
        if [ -z "$TEAM_ID" ]; then
            echo -e "${RED}[FAIL] Team ID required${NC}"
            exit 1
        fi
    fi
    
    # Generate unique bundle IDs to avoid conflicts
    BUNDLE_SUFFIX=$(echo $TEAM_ID | md5 | cut -c1-8)
    
    # Configure WDA project
    echo ""
    echo -e "${BLUE}[4/5] Configuring WebDriverAgent...${NC}"
    cd "$WDA"
    
    # Update Team ID
    sed -i '' "s/DEVELOPMENT_TEAM = [^;]*/DEVELOPMENT_TEAM = $TEAM_ID/g" WebDriverAgent.xcodeproj/project.pbxproj
    
    # Update Bundle IDs to be unique (prevents conflicts with other devs)
    sed -i '' "s/com\.vanditkumar\./com.wda.$BUNDLE_SUFFIX./g" WebDriverAgent.xcodeproj/project.pbxproj
    sed -i '' "s/com\.facebook\./com.wda.$BUNDLE_SUFFIX./g" WebDriverAgent.xcodeproj/project.pbxproj
    
    echo -e "${GREEN}[OK] Team ID: $TEAM_ID${NC}"
    echo -e "${GREEN}[OK] Bundle ID: com.wda.$BUNDLE_SUFFIX.*${NC}"
    
    # Get device
    UDID=""
    if command -v tidevice &>/dev/null; then
        UDID=$(tidevice list 2>/dev/null | grep -v "UDID" | tail -1 | awk '{print $1}')
    elif command -v idevice_id &>/dev/null; then
        UDID=$(idevice_id -l 2>/dev/null | head -1)
    fi
    
    if [ -z "$UDID" ]; then
        echo ""
        echo -e "${RED}[FAIL] No iPhone found via USB${NC}"
        echo ""
        echo "Please:"
        echo "  1. Connect iPhone via USB cable"
        echo "  2. Unlock iPhone"
        echo "  3. Tap 'Trust' when prompted"
        echo ""
        exit 1
    fi
    
    echo -e "${GREEN}[OK] Device: $UDID${NC}"
    
    # Build WDA
    echo ""
    echo -e "${BLUE}[5/5] Building WebDriverAgent...${NC}"
    echo -e "${YELLOW}(First build takes ~2 minutes)${NC}"
    echo ""
    
    xcodebuild build-for-testing \
      -project WebDriverAgent.xcodeproj \
      -scheme WebDriverAgentRunner \
      -destination "id=$UDID" \
      -allowProvisioningUpdates 2>&1 | grep -E "(Building|Signing|Finished|error|warning)" || true
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo ""
        echo -e "${RED}[FAIL] Build failed${NC}"
        echo ""
        echo "Common fixes:"
        echo "  1. Open Xcode → Settings → Accounts → Sign in with Apple ID"
        echo "  2. Enable Developer Mode on iPhone: Settings → Privacy & Security → Developer Mode"
        echo "  3. Give Xcode Full Disk Access: System Settings → Privacy & Security → Full Disk Access"
        echo ""
        exit 1
    fi
    
    touch "$SETUP_DONE"
    
    echo ""
    echo -e "${GREEN}[OK] Build complete!${NC}"
    echo ""
    echo "======================================"
    echo " IMPORTANT: Trust Certificate"
    echo "======================================"
    echo ""
    echo "On your iPhone:"
    echo "  1. Go to: Settings → General"
    echo "  2. Scroll to: VPN & Device Management"
    echo "  3. Tap your developer certificate"
    echo "  4. Tap 'Trust' and confirm"
    echo ""
    read -p "Press Enter after trusting certificate..."
    echo ""
fi

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
get_device_udid() {
    local udid=""
    if command -v tidevice &>/dev/null; then
        udid=$(tidevice list 2>/dev/null | grep -v "UDID" | tail -1 | awk '{print $1}')
    elif command -v idevice_id &>/dev/null; then
        udid=$(idevice_id -l 2>/dev/null | head -1)
    else
        udid=$(instruments -s devices 2>/dev/null | grep -i iphone | grep -v Simulator | head -1 | sed -n 's/.*(\([0-9A-F\-]\{25,\}\)).*/\1/p')
    fi
    echo "$udid"
}

kill_port() {
    local pids=$(lsof -t -i ":$1" 2>/dev/null || true)
    [ -n "$pids" ] && echo "$pids" | xargs kill -9 2>/dev/null || true
}

start_relay() {
    if command -v tidevice &>/dev/null; then
        nohup tidevice relay 8100 8100 >/dev/null 2>&1 &
        echo $! > "$UDITA_ROOT/.relay.pid"
        sleep 2
        return 0
    elif command -v iproxy &>/dev/null; then
        nohup iproxy 8100 8100 >/dev/null 2>&1 &
        echo $! > "$UDITA_ROOT/.relay.pid"
        sleep 2
        return 0
    fi
    return 1
}

test_wda() {
    curl -s --connect-timeout 2 "http://$1:8100/status" 2>/dev/null | grep -q '"ready"'
}

# ============================================================================
# START SERVICES
# ============================================================================
echo "======================================"
echo " UDITA"
echo "======================================"
echo ""

echo -e "${BLUE}[1/3] Finding device...${NC}"
UDID=$(get_device_udid)

if [ -z "$UDID" ]; then
    echo -e "${RED}[FAIL] No iPhone found${NC}"
    echo ""
    echo "USB: Connect iPhone, unlock, and trust this Mac"
    echo "Wi-Fi: Ensure both devices on same network"
    exit 1
fi

echo -e "${GREEN}[OK] Device: $UDID${NC}"

echo ""
echo -e "${BLUE}[2/3] Starting WebDriverAgent...${NC}"

pkill -f "xcodebuild.*WebDriverAgent" 2>/dev/null || true
kill_port 8100

cd "$WDA"
nohup xcodebuild test-without-building \
  -project WebDriverAgent.xcodeproj \
  -scheme WebDriverAgentRunner \
  -destination "id=$UDID" \
  -allowProvisioningUpdates \
  >/dev/null 2>&1 &

echo $! > "$UDITA_ROOT/.wda.pid"
sleep 5

# Try USB first
WDA_HOST=""
CONNECTION=""

if start_relay && test_wda "127.0.0.1"; then
    WDA_HOST="127.0.0.1"
    CONNECTION="USB"
    echo -e "${GREEN}[OK] Connected via USB (127.0.0.1:8100)${NC}"
else
    # Try Wi-Fi
    echo -e "${YELLOW}[..] USB unavailable, scanning Wi-Fi...${NC}"
    SUBNET=$(ifconfig | grep "inet " | grep -v "127.0.0.1" | head -1 | awk '{print $2}' | sed 's/\.[0-9]*$//')
    
    if [ -n "$SUBNET" ]; then
        for i in {1..254}; do
            ip="${SUBNET}.$i"
            if test_wda "$ip" 2>/dev/null; then
                WDA_HOST="$ip"
                CONNECTION="Wi-Fi"
                echo -e "${GREEN}[OK] Connected via Wi-Fi ($ip:8100)${NC}"
                break
            fi
        done
    fi
fi

if [ -z "$WDA_HOST" ]; then
    echo -e "${RED}[FAIL] Could not connect to WDA${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if WebDriverAgentRunner app is running on iPhone"
    echo "  2. Trust certificate: Settings → General → Device Management"
    echo "  3. Restart: ./start.sh stop && ./start.sh"
    echo ""
    exit 1
fi

echo ""
echo -e "${BLUE}[3/3] Starting bridge...${NC}"

kill_port 5050

cd "$BRIDGE"
nohup python3 server.py --ip "$WDA_HOST" --port 5050 >/dev/null 2>&1 &
echo $! > "$UDITA_ROOT/.bridge.pid"

sleep 2

if ! curl -s --connect-timeout 2 "http://127.0.0.1:5050/api/status" >/dev/null 2>&1; then
    echo -e "${RED}[FAIL] Bridge failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Bridge running (localhost:5050)${NC}"

echo ""
echo "======================================"
echo -e " ${GREEN}✓ UDITA is running!${NC}"
echo "======================================"
echo ""
echo "Connection: $CONNECTION ($WDA_HOST:8100)"
echo "Dashboard:  http://localhost:5050"
echo ""
echo "Controls:"
echo "  • Click to tap"
echo "  • Drag to swipe"
echo "  • Hold (800ms) for long-press"
echo "  • Wheel scroll: disabled (toggle in UI)"
echo ""
echo "Stop: Ctrl+C or ./start.sh stop"
echo ""

# Monitor services
trap "./start.sh stop; exit 0" INT TERM

while true; do
    sleep 5
    if ! kill -0 $(cat "$UDITA_ROOT/.wda.pid" 2>/dev/null) 2>/dev/null; then
        echo -e "${RED}[!] WDA stopped unexpectedly${NC}"
        ./start.sh stop
        exit 1
    fi
    if ! kill -0 $(cat "$UDITA_ROOT/.bridge.pid" 2>/dev/null) 2>/dev/null; then
        echo -e "${RED}[!] Bridge stopped unexpectedly${NC}"
        ./start.sh stop
        exit 1
    fi
done
