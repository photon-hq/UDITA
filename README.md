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

**One-time setup:** Trust certificate on iPhone  
Settings → General → VPN & Device Management → Trust

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

**No iPhone found**  
Connect via USB, unlock, trust this Mac

**Device management error**  
Settings → General → Device Management → Trust certificate

**Port in use**  
```bash
./udita stop
./udita
```

## License

MIT
