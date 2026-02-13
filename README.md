<div align="center">
  <img src="logo.png" alt="UDITA Logo" width="120" height="120">
  
  # UDITA
  
  **Unified Device Interface To Automate**
  
  *Control one or more iPhones from a single web dashboard*
  
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  
</div>

---

## Quick Start

### Prerequisites
- Mac with Xcode installed
- iPhone connected via USB
- Python 3 installed

### Setup

```bash
# 1. Clone and enter directory
cd UDITA

# 2. Run setup (installs dependencies)
./setup.sh

# 3. Configure signing in Xcode
open wda/WebDriverAgent.xcodeproj
# → Select WebDriverAgentRunner target
# → Signing & Capabilities → Choose your Team
# → Change Bundle ID to something unique (e.g., com.yourname.WebDriverAgentRunner)
# → Repeat for WebDriverAgentLib target

# 4. Connect iPhone, unlock, trust computer, then:
./install-wda.sh

# 5. Start the bridge
./run.sh
```

Open **http://localhost:5050** in your browser and select your device.

---

## What is UDITA?

UDITA provides a web dashboard to remotely control iPhones using WebDriverAgent (WDA). 

**Features:**
- Interactive screen mirror - Click to tap, drag to swipe, right-click for long-press
- Multi-device support - Control multiple iPhones from one dashboard
- Auto-discovery - Automatically finds iPhones on your network
- Call control - Answer/decline FaceTime and phone calls
- Screenshots - Capture and view device screen
- Quick actions - Home, lock, notifications, control center, app switcher
- Element inspection - Find and interact with UI elements
- Full WDA API - Access all WebDriverAgent endpoints

**How it works:**
```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │◄───────►│  Mac Bridge  │◄───────►│   iPhone    │
│ localhost:  │  HTTP   │   (Python)   │  USB/   │  WDA:8100   │
│    5050     │         │              │  WiFi   │             │
└─────────────┘         └──────────────┘         └─────────────┘
```

---

## Usage

### Starting UDITA

```bash
./run.sh
```

This will:
- Install dependencies (if needed)
- Start USB relay (if device connected)
- Start the bridge server
- Scan network for devices

Then open **http://localhost:5050**

### Using the Dashboard

**Screen Interaction:**
- **Click** = Tap
- **Drag** = Swipe
- **Hold 0.5s** = Long press
- **Right-click** = Long press
- **Double-click** = Double tap
- **Scroll wheel** = Scroll
- **Ctrl+wheel** = Pinch zoom
- **Ctrl+click** = Two-finger tap
- **Alt+click** = Force touch

**Quick Actions:**
- Home button, lock/unlock, volume controls
- Open notifications, control center, app switcher
- Launch apps (Safari, Settings, FaceTime, etc.)
- Answer/decline calls
- Type text, dismiss keyboard
- Take screenshots

**Device Selection:**
- Devices appear automatically (scanned every 15s)
- Click **Scan now** to force refresh
- Use **Set** button to add device manually
- For USB: use `127.0.0.1` (relay)
- For WiFi: use device's IP (e.g., `192.168.0.100`)

---

## Detailed Setup

<details>
<summary><b>Prerequisites</b></summary>

### Mac Requirements
- **macOS** (any recent version)
- **Xcode** (from App Store) - Required for building WDA
- **Python 3** - Usually pre-installed, or: `brew install python3`
- **pip** - Check with: `python3 -m pip --version`

### iPhone Requirements
- **Any iPhone** (iOS 9.3+)
- **USB cable** (for initial setup)
- **Same WiFi network** as Mac (optional, for wireless control)
- **Developer mode enabled** (iOS 16+)

### Optional Tools
- **tidevice** - For USB relay: `pip3 install tidevice`
- **pymobiledevice3** - For advanced features: `pip3 install pymobiledevice3`
- **libimobiledevice** - Alternative USB relay: `brew install libimobiledevice`

</details>

<details>
<summary><b>Installation Steps</b></summary>

### Step 1: Install Bridge Dependencies

```bash
cd UDITA
pip3 install -r bridge/requirements.txt
```

Or use the setup script:
```bash
./setup.sh
```

### Step 2: Configure WDA Signing

WebDriverAgent must be signed with **your** Apple ID:

1. Open the project:
   ```bash
   open wda/WebDriverAgent.xcodeproj
   ```

2. Select **WebDriverAgentRunner** target
3. Go to **Signing & Capabilities** tab
4. Enable **Automatically manage signing**
5. Select your **Team** (your Apple ID)
6. Change **Bundle Identifier** to something unique:
   - Example: `com.yourname.WebDriverAgentRunner`

7. **Repeat for WebDriverAgentLib target** (same team, same bundle ID pattern)

### Step 3: Install WDA on iPhone

1. Connect iPhone via USB
2. Unlock device and tap **Trust** when prompted
3. Run the installer:
   ```bash
   ./install-wda.sh
   ```

This builds and runs WDA on your iPhone. First time may prompt for Apple ID password.

### Step 4: Start the Bridge

```bash
./run.sh
```

The bridge will:
- Start USB relay automatically (if device connected)
- Start Flask server on port 5050
- Begin scanning network for devices

</details>

<details>
<summary><b>iPhone App Setup (Detailed)</b></summary>

### Overview

WebDriverAgent (WDA) is an XCUITest-based test runner that acts as a server on your iPhone. This section provides detailed, step-by-step instructions for building and installing it.

### Step 1: Prepare Your iPhone

1. **Connect iPhone to Mac via USB cable**
   - Use the original Lightning/USB-C cable for best results
   - Wait for the device to appear in Finder sidebar

2. **Unlock your iPhone**
   - Enter your passcode to unlock the device
   - Keep the screen on during setup

3. **Trust this computer**
   - A popup will appear on iPhone: "Trust This Computer?"
   - Tap **Trust**
   - Enter your iPhone passcode when prompted
   - On Mac, you should now see the device in Finder

4. **Enable Developer Mode (iOS 16+ only)**
   - Go to iPhone **Settings** → **Privacy & Security** → **Developer Mode**
   - Toggle **Developer Mode** ON
   - Tap **Restart** when prompted
   - After restart, confirm by tapping **Turn On** in the alert

### Step 2: Open WDA Project in Xcode

1. **Open Terminal and navigate to UDITA folder**
   ```bash
   cd /path/to/UDITA
   ```

2. **Open the Xcode project**
   ```bash
   open wda/WebDriverAgent.xcodeproj
   ```
   
   Xcode will launch and load the WebDriverAgent project.

### Step 3: Configure Signing for WebDriverAgentRunner

1. **Select the WebDriverAgentRunner target**
   - In the left sidebar (Project Navigator), click on the blue **WebDriverAgent** project icon at the top
   - In the center pane, under **TARGETS**, select **WebDriverAgentRunner**

2. **Go to Signing & Capabilities tab**
   - Click the **Signing & Capabilities** tab at the top of the center pane

3. **Enable automatic signing**
   - Check the box: **☑ Automatically manage signing**

4. **Select your Team**
   - Click the **Team** dropdown
   - If you see your Apple ID, select it
   - If not, click **Add an Account...** and sign in with your Apple ID
   - After signing in, select your account from the Team dropdown

5. **Change the Bundle Identifier**
   - Find the **Bundle Identifier** field (usually shows `com.facebook.WebDriverAgentRunner`)
   - Change it to something unique, for example:
     - `com.yourname.WebDriverAgentRunner`
     - `com.mycompany.wda.runner`
     - `dev.test.WebDriverAgentRunner`
   - **Important:** Make it unique to avoid conflicts

6. **Verify signing is successful**
   - You should see a message: "Signing certificate: Apple Development: your@email.com"
   - If you see errors, try a different Bundle Identifier

### Step 4: Configure Signing for WebDriverAgentLib

1. **Select the WebDriverAgentLib target**
   - In the center pane, under **TARGETS**, select **WebDriverAgentLib**

2. **Repeat the signing steps**
   - Enable **Automatically manage signing**
   - Select the **same Team** as before
   - Change **Bundle Identifier** to match your pattern:
     - If you used `com.yourname.WebDriverAgentRunner`, use `com.yourname.WebDriverAgentLib`

3. **Verify signing is successful**
   - Check for the signing certificate message

### Step 5: Select Your iPhone as Build Target

1. **Click the device selector in Xcode toolbar**
   - At the top of Xcode, you'll see a device dropdown (next to the play/stop buttons)
   - It might say "Any iOS Device" or show a simulator

2. **Select your connected iPhone**
   - Click the dropdown
   - Under **iOS Device**, select your iPhone by name
   - Example: "Vandit's iPhone"

3. **Verify device is selected**
   - The toolbar should now show your iPhone's name

### Step 6: Build and Run WDA on iPhone

1. **Run the test**
   - Click **Product** menu → **Test** (or press **⌘ + U**)
   - Alternatively, click and hold the Play button, then select **Test**

2. **Wait for build to complete**
   - Xcode will compile the project (may take 1-2 minutes first time)
   - Watch the progress bar at the top of Xcode

3. **First-time installation: Trust developer on iPhone**
   - After build completes, check your iPhone
   - You may see: "Untrusted Developer"
   - Go to iPhone **Settings** → **General** → **VPN & Device Management**
   - Tap your Apple ID under **Developer App**
   - Tap **Trust "your@email.com"**
   - Tap **Trust** in the confirmation dialog
   - Return to Xcode and run the test again (**⌘ + U**)

4. **Wait for tests to start**
   - Xcode will show "Running tests..."
   - On your iPhone, you'll see the WebDriverAgentRunner app launch briefly
   - In Xcode's console (bottom pane), you should see:
     ```
     ServerURLHere->http://[IP]:8100<-ServerURLHere
     ```
   - **Do NOT stop the test!** Keep it running.

5. **Verify WDA is running**
   - Open Safari on your Mac
   - Go to: `http://localhost:8100/status`
   - If you see JSON output with device info, WDA is working!

### Step 7: Alternative - Use Install Script

Instead of steps 5-6, you can use the automated installer:

```bash
./install-wda.sh
```

This script will:
- Build WebDriverAgent
- Install it on the connected iPhone
- Start the WDA server

**Note:** You still need to complete signing configuration (Steps 3-4) before running this script.

### Step 8: Keep WDA Running

**Important:** WDA must keep running on your iPhone for UDITA to work.

**Option A: Keep Xcode test running**
- Leave Xcode open with the test running
- Don't press the Stop button
- WDA will stay active

**Option B: Run WDA without Xcode (WiFi only)**
- Once WDA is installed via Xcode, it can run independently
- Tap the **WebDriverAgentRunner** app icon on your iPhone
- The app will launch and start the server
- You can now close Xcode

**Option C: Use tidevice to start WDA**
```bash
tidevice wdaproxy -B com.yourname.WebDriverAgentRunner
```

### Troubleshooting iPhone Setup

**Problem: "Failed to create provisioning profile"**
- Solution: Change Bundle Identifier to something more unique
- Try adding random numbers: `com.yourname.wda123.runner`

**Problem: "Your session has expired. Please log in."**
- Solution: Go to Xcode → Preferences → Accounts
- Select your Apple ID → Click "Download Manual Profiles"
- Try building again

**Problem: "Could not launch WebDriverAgentRunner"**
- Solution: Check iPhone Settings → General → VPN & Device Management
- Trust your developer certificate
- Try running the test again

**Problem: "Device is busy"**
- Solution: Disconnect and reconnect iPhone
- Restart Xcode
- Unlock iPhone and try again

**Problem: Build succeeds but WDA doesn't start**
- Solution: Check iPhone screen - there may be a popup to allow
- Make sure iPhone is unlocked
- Check Xcode console for error messages

**Problem: "Address already in use" (port 8100)**
- Solution: WDA is already running - this is good!
- You can proceed to start the bridge

### Verification Checklist

Before proceeding to use UDITA, verify:

- [ ] iPhone is connected via USB (or on same WiFi)
- [ ] iPhone is unlocked
- [ ] Developer Mode is enabled (iOS 16+)
- [ ] Computer is trusted on iPhone
- [ ] Developer certificate is trusted on iPhone
- [ ] WDA test is running in Xcode (or WDA app is running on iPhone)
- [ ] `http://localhost:8100/status` returns JSON (for USB)
- [ ] OR `http://[iPhone-IP]:8100/status` returns JSON (for WiFi)

Once all items are checked, you're ready to start the UDITA bridge!

</details>

<details>
<summary><b>Network Configuration</b></summary>

### USB Connection (Recommended for single device)

When iPhone is connected via USB, use the relay:

```bash
# Relay is started automatically by ./run.sh
# Or start manually:
tidevice relay 8100 8100
# Or with libimobiledevice:
iproxy 8100 8100
```

Then use **127.0.0.1** as the device IP in the dashboard.

### WiFi Connection (For multiple devices or wireless)

1. Connect iPhone and Mac to **same WiFi network**
2. Find iPhone's IP address:
   - Settings → WiFi → (i) → IP Address
   - Example: `192.168.0.100`
3. Use this IP in the dashboard

**Note:** WiFi requires WDA to be started via Xcode at least once over USB.

### Multiple Devices

Pre-configure device list:

```bash
export DEVICES=127.0.0.1,192.168.0.108,192.168.0.109
./run.sh
```

Or add devices in the dashboard using the **Set** button.

</details>

<details>
<summary><b>Configuration Options</b></summary>

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IP` | (none) | Default device IP |
| `PORT` | `5050` | Bridge server port |
| `WDA_PORT` | `8100` | WDA port on device |
| `DEVICES` | (none) | Comma-separated device IPs |
| `SCREEN_WIDTH` | `393` | Fallback screen width |
| `SCREEN_HEIGHT` | `852` | Fallback screen height |

### Examples

```bash
# Use specific device by default
./run.sh 127.0.0.1

# Change bridge port
PORT=8080 ./run.sh

# Pre-fill device list
export DEVICES=192.168.0.107,192.168.0.108
./run.sh

# Custom WDA port
WDA_PORT=8200 ./run.sh
```

### Command Line Arguments

```bash
# Specify device IP
./run.sh 192.168.0.100

# Change port
./run.sh --port 8080

# Specify device IP and port
./run.sh --ip 192.168.0.100 --port 8080
```

</details>

<details>
<summary><b>Troubleshooting</b></summary>

### "Device not ready" error

**Cause:** USB relay has no device connected, but you're using 127.0.0.1

**Solution:** 
- If iPhone is unplugged: Use WiFi IP instead (e.g., `192.168.0.100`)
- If iPhone is plugged in: Check USB connection, unlock device, restart relay

### "WDA not reachable"

**Cause:** WDA is not running on the iPhone

**Solution:**
1. Open Xcode: `open wda/WebDriverAgent.xcodeproj`
2. Select your iPhone in toolbar
3. Product → Test (Cmd+U)
4. Wait for test to start running (don't stop it)

### "Session expired"

**Cause:** WDA session timed out or was interrupted

**Solution:** Refresh the dashboard (F5). A new session will be created automatically.

### "No devices found"

**Cause:** Network scan didn't find any devices

**Solution:**
- Ensure iPhone and Mac are on same WiFi
- Ensure WDA is running on iPhone
- Click **Scan now** button
- Or add device IP manually with **Set** button

### Xcode signing errors

**Cause:** Bundle ID already in use or team not selected

**Solution:**
1. Change Bundle ID to something unique
2. Ensure team is selected in both targets
3. Try: Xcode → Preferences → Accounts → Download Manual Profiles

### Port already in use

**Cause:** Another process is using port 5050 or 8100

**Solution:**
```bash
# Use different port
PORT=5051 ./run.sh

# Or kill existing process
lsof -ti:5050 | xargs kill
```

</details>

---

## Advanced

<details>
<summary><b>API Reference</b></summary>

The bridge exposes a REST API on port 5050:

### Device Management
- `GET /api/status` - Bridge and device status
- `GET /api/devices` - List all devices
- `POST /api/device/select` - Select device
- `POST /api/set-ip` - Set device IP
- `POST /api/scan-now` - Force network scan

### Touch & Gestures
- `POST /api/tap` - Tap at coordinates
- `POST /api/double-tap` - Double tap
- `POST /api/long-press` - Long press
- `POST /api/swipe` - Swipe gesture
- `POST /api/pinch` - Pinch zoom
- `POST /api/scroll` - Scroll
- `POST /api/two-finger-tap` - Two-finger tap
- `POST /api/force-touch` - Force touch

### Device Control
- `POST /api/home` - Press home button
- `POST /api/lock` - Lock device
- `POST /api/unlock` - Unlock device
- `POST /api/press-button` - Press hardware button
- `GET /api/orientation` - Get orientation
- `GET /api/battery` - Battery info
- `GET /api/device-info` - Device information

### Apps
- `POST /api/launch` - Launch app
- `POST /api/activate` - Activate app
- `POST /api/terminate` - Kill app
- `GET /api/app-list` - List installed apps
- `GET /api/active-app` - Get active app

### Screen & Elements
- `GET /api/screenshot` - Take screenshot
- `GET /api/source` - Get page source XML
- `GET /api/elements` - List visible elements
- `POST /api/find` - Find elements
- `POST /api/click` - Click element by name

### Keyboard & Input
- `POST /api/type` - Type text
- `POST /api/dismiss-keyboard` - Dismiss keyboard

### Call Control
- `POST /api/answer-call` - Answer incoming call
- `POST /api/decline-call` - Decline incoming call

### Full API documentation available at: `/wda/*` (direct WDA passthrough)

</details>

<details>
<summary><b>Architecture</b></summary>

### Components

**Bridge (Mac):**
- `bridge/server.py` - Flask REST API (900 lines)
- `bridge/dashboard.html` - Web UI (403 lines)
- `bridge/start.sh` - Startup script

**WebDriverAgent (iPhone):**
- `wda/WebDriverAgentRunner` - Test runner app
- `wda/WebDriverAgentLib` - Core library (HTTP server + XCTest APIs)

**Helper Scripts:**
- `run.sh` - Single entry point
- `setup.sh` - Install dependencies
- `install-wda.sh` - Build and install WDA

### Data Flow

1. User interacts with dashboard (browser)
2. Dashboard sends HTTP request to bridge (Flask)
3. Bridge forwards request to WDA on iPhone
4. WDA executes action using XCTest framework
5. WDA returns result to bridge
6. Bridge returns result to dashboard
7. Dashboard updates UI

### Tech Stack

**iPhone:**
- Objective-C (WDA)
- XCTest framework
- CocoaHTTPServer

**Mac:**
- Python 3
- Flask (web server)
- Requests (HTTP client)

**Dashboard:**
- HTML5 Canvas (screen mirror)
- Vanilla JavaScript (no frameworks)
- CSS3 (modern styling)

</details>

<details>
<summary><b>Security & Privacy</b></summary>

### What UDITA Can Do

- Control devices on your local network
- Tap, swipe, and interact with any app
- Take screenshots
- Launch and terminate apps
- Answer/decline calls
- Type text and control keyboard
- Access device information (battery, orientation, etc.)

### What UDITA Cannot Do

- Access device remotely over internet (local network only)
- Bypass device lock screen (device must be unlocked)
- Access encrypted data or keychain
- Install apps or modify system files
- Access data from other apps (sandboxed)

### Security Considerations

- **Local network only** - Bridge and WDA communicate over local network
- **No authentication** - Dashboard has no login (anyone on network can access)
- **No encryption** - HTTP traffic is unencrypted (use on trusted networks)
- **Device must be unlocked** - WDA requires device to be unlocked
- **User must build WDA** - Cannot be distributed as pre-built app

### Recommendations

- Use on **trusted networks only** (home/office WiFi)
- Don't expose bridge to internet
- Lock your Mac when not in use
- Stop bridge when not needed (`Ctrl+C`)
- Use firewall to restrict access to port 5050

</details>

<details>
<summary><b>FAQ</b></summary>

### Why can't I download WDA as an app?

WDA is an **XCUITest test runner**, not a normal app. Apple requires it to be built and signed with your own Apple ID. It cannot be distributed via App Store or as an IPA file.

### Do I need a paid Apple Developer account?

No! A **free Apple ID** is sufficient. You can sign WDA with any Apple ID.

### Can I control my iPhone remotely over the internet?

Not directly. UDITA is designed for **local network** use. You could set up a VPN to your home network, but this is not officially supported.

### Does this work with iPad?

Yes. WDA supports both iPhone and iPad. Use iPad instead of iPhone in the setup steps.

### Can I automate tasks with UDITA?

Yes! The REST API can be used for automation. You can write Python scripts to control devices programmatically.

### Will this drain my iPhone battery?

WDA uses minimal resources when idle. Battery drain is similar to having an app running in the background.

### Can I use this for app testing?

Yes. UDITA works well for manual testing, QA, and automation. It's built on the same technology used by Appium.

### Is this legal?

Yes! You're controlling your own devices with Apple's official XCTest framework. This is the same technology used by Xcode for UI testing.

</details>

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development

```bash
# Make changes to bridge/server.py or bridge/dashboard.html
# Restart bridge to see changes:
./run.sh

# Dashboard changes only (no restart needed):
# Refresh browser (F5)
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**WebDriverAgent** (in `wda/` folder) is licensed under BSD License - Copyright (c) Facebook, Inc.

---

## Acknowledgments

- [WebDriverAgent](https://github.com/appium/WebDriverAgent) - Facebook/Appium
- [Appium](http://appium.io) - Mobile automation framework
- Named after my girlfriend ❤️

