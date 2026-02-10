# Building WebDriverAgent for iPhone

WebDriverAgent (WDA) is a test runner that provides system-wide touch injection on iOS.
Once installed, it can tap, swipe, and interact with ANY app — including answering FaceTime calls.

## Quick Setup

### 1. Open in Xcode

```bash
open /Users/vandit/facetime/wda/WebDriverAgent.xcodeproj
```

### 2. Set Signing (for BOTH targets)

In Xcode:
- Select the project **WebDriverAgent** in the navigator
- Select target **WebDriverAgentRunner**
- Go to **Signing & Capabilities** tab
- Check **Automatically manage signing**
- Select your **Team** (same one you used for RemoteControlAPIApp)
- Change the **Bundle Identifier** to something unique, e.g.: `monstermini.WebDriverAgentRunner`

**IMPORTANT: Also do this for the `WebDriverAgentLib` target** (same team, auto-signing).

### 3. Select your iPhone as the build target

- In the top toolbar, select your iPhone (not a simulator)

### 4. Build & Run the test

- Go to **Product → Test** (or press **Cmd+U**)
- This builds and installs WDA on your iPhone
- The test will start running — WDA is now listening on the iPhone

### 5. Forward the WDA port

In terminal:
```bash
# Forward iPhone's WDA port to your Mac
tidevice relay 8100 8100
```

Or use iproxy:
```bash
iproxy 8100 8100
```

### 6. Test it!

```bash
# Health check
curl http://localhost:8100/status

# Tap at (200, 400)
curl -X POST http://localhost:8100/session -H 'Content-Type: application/json' -d '{"capabilities":{}}'
# Note the sessionId from the response, then:
curl -X POST http://localhost:8100/session/<sessionId>/wda/tap -H 'Content-Type: application/json' -d '{"x":200,"y":400}'
```

## What WDA Can Do

- **Tap at any (x, y) coordinate** — system-wide, works on lock screen, call screen, etc.
- **Swipe** from point A to B
- **Type text**
- **Press hardware buttons** (home, volume, lock)
- **Take screenshots**
- **Read screen elements**
- **Answer/decline calls** by tapping the Accept/Decline buttons
