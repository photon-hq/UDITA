# UDITA - iPhone Remote Control

Control your iPhone from your Mac using WebDriverAgent.

## Quick Start

### One Command Setup

```bash
./start.sh
```

That's it! The script will:
- ✅ Auto-install USB tools (tidevice)
- ✅ Auto-detect your Apple Developer Team ID
- ✅ Auto-configure bundle IDs
- ✅ Build WebDriverAgent
- ✅ Start all services

**First time only:** Trust certificate on iPhone
- Settings → General → VPN & Device Management → Trust

### Daily Use

```bash
./start.sh              # Start UDITA
./start.sh stop         # Stop UDITA
```

Dashboard: **http://localhost:5050**

## Features

- **Live screen mirror** - See iPhone screen in real-time
- **Touch control** - Click to tap, drag to swipe, hold for long-press
- **Gestures** - Pinch, rotate, force touch, multi-finger
- **Device control** - Home, volume, lock/unlock, orientation
- **Apps** - Launch, terminate, switch apps
- **Calls** - Answer/decline programmatically
- **Keyboard** - Type text, dismiss keyboard
- **Clipboard** - Get/set clipboard
- **Siri** - Trigger Siri commands
- **Location** - Set simulated GPS
- **Screenshots** - Capture and download
- **Elements** - Find UI elements by name, xpath, etc.

## Connection

UDITA automatically detects:
1. **USB** (preferred) - Reliable, no config needed
2. **Wi-Fi** (fallback) - Works if on same network

## API Examples

```bash
# Status
curl http://localhost:5050/api/status

# Tap
curl -X POST http://localhost:5050/api/tap \
  -H "Content-Type: application/json" \
  -d '{"x": 195, "y": 426}'

# Swipe
curl -X POST http://localhost:5050/api/swipe \
  -H "Content-Type: application/json" \
  -d '{"from": {"x": 195, "y": 600}, "to": {"x": 195, "y": 200}}'

# Launch app
curl -X POST http://localhost:5050/api/launch \
  -H "Content-Type: application/json" \
  -d '{"bundle_id": "com.apple.mobilesafari"}'

# Type text
curl -X POST http://localhost:5050/api/type \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'

# Screenshot
curl http://localhost:5050/api/screenshot.png -o screenshot.png
```

See full API in dashboard (Raw API section).

## Troubleshooting

### "No iPhone found"
- **USB:** Connect iPhone, unlock, trust this Mac
- **Wi-Fi:** Both devices must be on same network

### "Device management settings" error
1. Settings → General → VPN & Device Management
2. Tap your developer certificate
3. Tap "Trust"

### Port already in use
```bash
./start.sh stop
./start.sh
```

### WDA keeps stopping
Don't close WebDriverAgentRunner app on iPhone!

### Running from Xcode (Alternative)
If you prefer Xcode:
1. Open `wda/WebDriverAgent.xcodeproj`
2. Select **WebDriverAgentRunner** scheme (not WebDriverAgentLib!)
3. Select your iPhone as destination
4. Press Cmd+U to run tests
5. In terminal: `./start.sh` (skip build, just starts bridge)

## Configuration

```bash
# Custom port
PORT=8080 ./start.sh

# Force Wi-Fi IP
./start.sh 192.168.1.40
```

## Project Structure

```
UDITA/
├── start.sh              # Main script (setup + start + stop)
├── wda/                  # WebDriverAgent
└── bridge/
    ├── server.py         # API server
    └── dashboard.html    # Web UI
```

## Requirements

- macOS with Xcode installed
- iPhone with Developer Mode enabled (iOS 17+: Settings → Privacy & Security → Developer Mode)
- Python 3 (pre-installed on macOS)

Everything else installs automatically!

## Known Issues

### macOS Sonoma+ CoreDevice Errors
Give Xcode Full Disk Access:
- System Settings → Privacy & Security → Full Disk Access → Add Xcode

### iOS 17+ Developer Mode
Enable in: Settings → Privacy & Security → Developer Mode

## Credits

- **WebDriverAgent** - Facebook (Meta)
- **UDITA** - Built for iOS automation

## License

MIT
