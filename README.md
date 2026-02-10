# UDITA

*Unified Device Interface To Automate — named after my girlfriend.*

One dashboard to control one or more iPhones. Install and run **WebDriverAgent (WDA)** on each device; the bridge discovers them and you pick one to control (tap, swipe, screenshots, apps, calls, etc.).

## What it is

- **Single entrypoint:** Dashboard shows all iPhones on your list (reachable or not). Select one to control it.
- **One app per iPhone:** WebDriverAgent (WDA) only. Build from `wda/`, run on each device.
- **Mac bridge:** Python server in `bridge/` talks to WDA on each iPhone (HTTP :8100).

## Run (single entry point)

From the UDITA folder:

```bash
cd /path/to/facetime/UDITA
./run.sh
```

This installs dependencies if needed, starts the USB relay automatically when possible, and starts the bridge. Open **http://localhost:5050** and pick a device.

**First time only:**  
1. Set signing in Xcode: `open wda/WebDriverAgent.xcodeproj` → both targets → Signing & Capabilities → your Team, unique Bundle ID.  
2. Connect iPhone (USB), unlock and trust, then: `./install-wda.sh`

## Setup (from scratch, step by step)

Use any Mac and iPhone. Same Wi‑Fi or USB.

### 1. Mac — prerequisites

- **Xcode** (from App Store)
- **Python 3** (system or Homebrew)
- **pip**: `python3 -m pip --version`

### 2. Mac — install bridge deps

```bash
cd /path/to/facetime/UDITA
pip3 install -r bridge/requirements.txt
```

Optional (for app launch when iPhone is not on USB): `pip3 install pymobiledevice3`

### 3. iPhone — build and run WDA

- Connect iPhone to Mac via USB. Unlock the device, trust the computer.
- Open the WDA project in Xcode:
  ```bash
  open wda/WebDriverAgent.xcodeproj
  ```
- In Xcode:
  - Select project **WebDriverAgent** → target **WebDriverAgentRunner** → **Signing & Capabilities** → enable **Automatically manage signing**, choose your **Team**, set a unique **Bundle ID** (e.g. `com.yourname.WebDriverAgentRunner`).
  - Do the same for target **WebDriverAgentLib** (same team, auto-signing).
  - In the toolbar, select your **iPhone** (not a simulator).
  - **Product → Test** (Cmd+U). WDA installs and runs on the iPhone; it listens on port 8100 on the device.

### 4. Expose WDA to the Mac

**Option A — USB (one device):** Forward the device port to the Mac:

```bash
# If you have tidevice:
tidevice relay 8100 8100

# Or with libimobiledevice:
iproxy 8100 8100
```

Then the bridge will use **127.0.0.1** as the device IP (set in dashboard or run `./start.sh 127.0.0.1`).

**Option B — Wi‑Fi:** iPhone and Mac on the same Wi‑Fi. After running WDA via Xcode once over USB, you can sometimes reach it at the iPhone’s Wi‑Fi IP (e.g. in Settings → Wi‑Fi → (i) → IP Address). Use that IP in the dashboard. If it doesn’t work, use Option A.

### 5. Run the bridge and open the dashboard

```bash
cd bridge
./start.sh
# Or with a specific IP: ./start.sh 127.0.0.1   or   ./start.sh 192.168.0.107
```

Open **http://localhost:5050** in a browser. Pick a device from the dropdown (or add its IP with “Set”), then use the dashboard.

### Multiple devices

Set `DEVICES` before starting: `export DEVICES=127.0.0.1,192.168.0.108` or add each device’s IP in the dashboard with “Set”.

## Instructions

### First time (once per Mac / device)

1. **Mac:** Install Xcode and Python 3. From UDITA run `./setup.sh` to install bridge deps and check tools.
2. **Signing:** Open `wda/WebDriverAgent.xcodeproj` in Xcode. For **WebDriverAgentRunner** and **WebDriverAgentLib**: Signing & Capabilities → Automatically manage signing → choose your **Team** → set a unique **Bundle ID** (e.g. `com.yourname.WebDriverAgentRunner`).
3. **iPhone:** Connect via USB, unlock and tap “Trust”. Run `./install-wda.sh` to build and run WDA on the device. First run may ask for Apple ID.

### Every time you want to control a device

1. **Start:** From UDITA run `./run.sh`. Dependencies install if needed; USB relay starts automatically when possible.
2. **Dashboard:** Open **http://localhost:5050** in a browser.
3. **Device list:** The bridge scans the local subnet every 15s; the dropdown refreshes every 10s. Wi‑Fi devices appear automatically. For USB, use **127.0.0.1** (relay) or add it with **Set**.
4. **Select device:** Pick an IP from the **Device** dropdown. All actions (tap, swipe, screenshot, apps, etc.) apply to that device.
5. **Add IP:** To use an IP not in the list (e.g. USB relay), type it and click **Set**.

### Using the dashboard

- **Screen:** Click = tap, drag = swipe, hold ~0.6s = long-press, right-click = long-press, double-click = double-tap. Scroll wheel = scroll; Ctrl+wheel = pinch. Ctrl+click = two-finger tap, Alt+click = force touch.
- **Quick actions:** Home, swipe directions, Lock/Unlock, Notifications, Control Center, App Switcher, Spotlight. Use the cards for Call, Apps, Keyboard, etc.
- **Logs:** Server events and your actions appear in the Logs card. Use Raw API to send custom requests.

## Configuration

Override defaults with env or CLI so it works on any Mac/network:

| Env / CLI | Default | Purpose |
|-----------|---------|---------|
| `IP` or `--ip` | (none) | Default device IP so you don’t have to pick in the dashboard. |
| `WDA_PORT` | `8100` | Port WDA listens on on the device. |
| `PORT` or `--port` | `5050` | Port the bridge (and dashboard) listens on. Use if 5050 is taken. |
| `DEVICES` | (none) | Comma-separated IPs to show in the list at startup (e.g. `127.0.0.1,192.168.0.108`). |
| `SCREEN_WIDTH` / `SCREEN_HEIGHT` | `393` / `852` | Fallback screen size when WDA is unreachable. |

Examples:

```bash
# Default (scan + pick in dashboard)
./run.sh

# Use USB relay as default device
./run.sh 127.0.0.1

# Different bridge port
PORT=5051 ./run.sh

# Pre-fill device list
export DEVICES=192.168.0.107,192.168.0.108
./run.sh
```

## Tech

- **iPhone:** WebDriverAgent (WDA), HTTP API on port 8100
- **Mac:** Python 3, Flask, requests
- **Dashboard:** HTML/CSS/JS — device picker, screen mirror, tap/swipe/gestures, apps, logs
- **Optional:** pymobiledevice3 + tunneld for app launch when not on USB

## Why not a single package for the iPhone?

WDA is an **XCUITest test runner**, not a normal app. Apple requires it to be **built and signed on your Mac with your Apple ID** and installed via Xcode (or `install-wda.sh`). It cannot be distributed as one installable IPA or App Store app — each user must build it once with their own signing. After that, `./install-wda.sh` and `./start.sh` handle install and relay.

## Layout

| Path     | Purpose |
|----------|---------|
| **bridge/** | Mac bridge (Flask + dashboard). Multi-device. |
| **wda/**    | WebDriverAgent source. Build and run on each iPhone. |
| **run.sh** | Single entry point: installs deps if needed, starts relay + bridge. |
| **setup.sh** | Full setup (deps + checks); run once. |
| **install-wda.sh** | Builds and runs WDA on connected iPhone; run once after signing. |
| **ios/**    | Empty (legacy app removed). |
