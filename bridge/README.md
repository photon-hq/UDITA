# Bridge

Mac-side of UDITA. See **`../README.md`** for overview.

- **Multi-device:** Device dropdown; list from env `DEVICES` (comma-separated IPs) or add via "Set" in the dashboard.
- **One app per iPhone:** WebDriverAgent (WDA) only. Build from `../wda`, run on each device.

## Quick start

1. Start WDA on each iPhone (see `../wda/BUILD_INSTRUCTIONS.md`). Same Wi‑Fi as Mac.
2. `./start.sh` (optional: `export DEVICES=192.168.0.107,192.168.0.108`)
3. Open http://localhost:5050 — select device, then use the dashboard.

Session auto-refreshes; if a device goes offline, pick another from the dropdown or retry.
