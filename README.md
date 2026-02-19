# UDITA - iPhone Remote Control

Control your iPhone from your Mac using WebDriverAgent.

## Quick Start

```bash
./udita
```

**That's it!** One script, one command:
- ✓ Interactive menu with color-coded interface
- ✓ Auto-installs ALL dependencies (Python, pip, tidevice, Flask, etc.)
- ✓ Auto-detects your Apple Developer Team ID
- ✓ Auto-configures and builds WebDriverAgent
- ✓ Auto-detects connection (USB or Wi-Fi)
- ✓ Starts dashboard at http://localhost:5050

**First time only:** Trust certificate on iPhone
- Settings → General → VPN & Device Management → Trust

## Interactive Menu

Run `./udita` to launch the interactive menu:

```
╔════════════════════════════════════════╗
║     🚀 UDITA - iPhone Control         ║
╚════════════════════════════════════════╝

✓ Setup complete
  Team ID: 5U6B53ATF5
  Device: 00008120...

Commands:
  1) Start UDITA
  2) Stop UDITA
  3) Check Status
  4) Setup/Reconfigure
  q) Quit

Select option [1-4, q]:
```

## Direct Commands

```bash
./udita         # Interactive menu (default)
./udita start   # Start UDITA directly
./udita stop    # Stop all services
./udita status  # Check if running
./udita setup   # Run setup
```

## Features

- **Live screen mirror** - See iPhone screen in real-time
- **Touch control** - Click=tap, drag=swipe, hold=long-press
- **Gestures** - Pinch, rotate, force touch, multi-finger
- **Device control** - Home, volume, lock/unlock
- **Apps** - Launch, terminate, switch
- **Calls** - Answer/decline programmatically
- **Keyboard** - Type text, dismiss
- **Clipboard** - Get/set clipboard
- **Siri** - Trigger commands
- **Location** - Simulated GPS
- **Screenshots** - Capture and download
- **Elements** - Find by name, xpath, etc.

## Connection

Auto-detects best method:
1. **USB** (preferred) - Reliable, no config
2. **Wi-Fi** (fallback) - Same network required

## API Examples

```bash
# Status
curl http://localhost:5050/api/status

# Tap
curl -X POST http://localhost:5050/api/tap \
  -d '{"x": 195, "y": 426}' -H "Content-Type: application/json"

# Swipe
curl -X POST http://localhost:5050/api/swipe \
  -d '{"from": {"x": 195, "y": 600}, "to": {"x": 195, "y": 200}}' \
  -H "Content-Type: application/json"

# Launch app
curl -X POST http://localhost:5050/api/launch \
  -d '{"bundle_id": "com.apple.mobilesafari"}' \
  -H "Content-Type: application/json"

# Screenshot
curl http://localhost:5050/api/screenshot.png -o screenshot.png
```

Full API docs: http://localhost:5050 (Raw API section)

## Troubleshooting

### "No iPhone found"
- USB: Connect, unlock, trust this Mac
- Wi-Fi: Same network required

### "Device management settings" error
Settings → General → Device Management → Trust certificate

### Port in use
```bash
./udita stop
./udita
```

### WDA keeps stopping
Don't close WebDriverAgentRunner app on iPhone

## Requirements

**Minimum:**
- macOS with Xcode (from App Store)
- iPhone with Developer Mode enabled
  - iOS 16+: Settings → Privacy & Security → Developer Mode → ON
  - Connect via USB, unlock, and trust this Mac

**Everything else auto-installs:**
- ✓ Homebrew (if missing)
- ✓ Python 3 (if missing)
- ✓ pip3 (if missing)
- ✓ tidevice or libimobiledevice (USB tools)
- ✓ Flask, Flask-CORS, requests (Python packages)

Zero manual installation needed!

## Project Structure

```
UDITA/
├── udita              # ONE script - everything in here!
├── README.md          
├── wda/               # WebDriverAgent
└── bridge/
    ├── server.py      # API server
    └── dashboard.html # Web UI
```

## Configuration

```bash
# Custom port
PORT=8080 ./udita

# Force Wi-Fi IP
./udita 192.168.1.40
```

## Advanced

### Running from Xcode
1. Open `wda/WebDriverAgent.xcodeproj`
2. Select **WebDriverAgentRunner** scheme
3. Select your iPhone
4. Cmd+U to run
5. Run `./udita` (skips build, starts bridge)

### Manual Build
```bash
cd wda
xcodebuild build-for-testing \
  -project WebDriverAgent.xcodeproj \
  -scheme WebDriverAgentRunner \
  -destination "id=YOUR_UDID"
```

## Known Issues

### macOS Sonoma+ CoreDevice Errors
System Settings → Privacy & Security → Full Disk Access → Add Xcode

### iOS 17+ Developer Mode
Settings → Privacy & Security → Developer Mode → Enable

## Credits

WebDriverAgent by Facebook (Meta)

## License

MIT
