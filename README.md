# UDITA

Control your iPhone from your Mac.

## Quick Start

```bash
./udita
```

First run automatically:
- Installs dependencies (Python, Flask, tidevice)
- Detects your Apple Developer Team ID
- Builds WebDriverAgent
- Starts services

### ⚠️ Important: After Build Completes

**Step 1: Trust Certificate on iPhone**
1. Open **Settings** on your iPhone
2. Go to **General** → **VPN & Device Management** (or Device Management)
3. Find your Apple ID certificate: `Apple Development: <your-email>`
4. Tap **Trust** → **Trust**

**Step 2: Enable Developer Mode (iOS 16+ only)**
1. Open **Settings** on your iPhone
2. Go to **Privacy & Security** → **Developer Mode**
3. Toggle **ON** and restart your iPhone

**Step 3: Start UDITA**
```bash
./udita start
```

**Step 4: Open Dashboard**
Open http://localhost:5050 in your browser

## Commands

```bash
./udita         # Interactive menu
./udita start   # Start services
./udita stop    # Stop services
./udita status  # Check status
```

## Features

- Live screen mirror
- Touch control (tap, swipe, long-press)
- Gestures (pinch, rotate, force touch)
- Device control (home, volume, lock)
- App management (launch, terminate)
- Keyboard input
- Screenshots

## API

Dashboard: http://localhost:5050

```bash
# Tap
curl -X POST http://localhost:5050/api/tap \
  -d '{"x": 195, "y": 426}' -H "Content-Type: application/json"

# Swipe
curl -X POST http://localhost:5050/api/swipe \
  -d '{"from": {"x": 195, "y": 600}, "to": {"x": 195, "y": 200}}' \
  -H "Content-Type: application/json"

# Screenshot
curl http://localhost:5050/api/screenshot.png -o screenshot.png
```

## Requirements

- macOS with Xcode
- iPhone with Developer Mode (iOS 16+: Settings → Privacy & Security → Developer Mode)

Everything else auto-installs.

## Troubleshooting

**No iPhone found / Not running on localhost:5050**
1. **Connect iPhone via USB** - Use a working cable
2. **Unlock iPhone** - Keep it unlocked during first run
3. **Trust this Mac** - Look for "Trust This Computer?" popup on iPhone
4. **Enable Developer Mode** (iOS 16+):
   - Settings → Privacy & Security → Developer Mode → ON
5. **Verify connection**:
   ```bash
   tidevice list  # Should show your iPhone's UDID
   ```
6. **Restart UDITA**:
   ```bash
   ./udita stop
   ./udita start
   ```

**Device management error**  
Settings → General → Device Management → Trust certificate

**Port in use**  
```bash
./udita stop
./udita start
```

**Check logs for errors**
```bash
cat bridge.log  # Bridge server logs
```

## License

MIT
