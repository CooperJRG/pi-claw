# Raspberry Pi deployment and OpenClaw integration

This guide walks through: (1) getting the display app onto the Pi, (2) making it run at startup, and (3) having OpenClaw send API calls to it.

---

## Part 1: Get the app onto the Raspberry Pi

### Prerequisites

- Raspberry Pi 3 (or compatible) with Raspberry Pi OS (desktop or lite with a display).
- Display connected and working (HDMI).
- Pi on the same network as your dev machine; SSH enabled (`sudo raspi-config` → Interface Options → SSH → Enable).
- (Optional) Know your Pi’s hostname or IP, e.g. `raspberrypi.local` or `192.168.1.10`.

### Option A: One-time install on the Pi (recommended first time)

1. **Copy the repo onto the Pi** (from your dev machine):
   ```bash
   # From the pi-claw repo root on your dev machine
   rsync -az --delete \
     --exclude '.git/' --exclude '__pycache__/' --exclude '.pytest_cache/' --exclude '.venv/' \
     ./ pi@raspberrypi.local:/opt/openclaw-display/
   ```
   Or use the project script (same effect):
   ```bash
   PI_HOST=pi@raspberrypi.local ./pi/scripts/deploy.sh
   ```
   Adjust `PI_HOST` if your Pi has a different user or hostname.

2. **SSH into the Pi and run the install script** (installs system packages, venv, systemd unit, and starts the service):
   ```bash
   ssh pi@raspberrypi.local
   cd /opt/openclaw-display
   sudo ./pi/scripts/install_pi.sh
   ```
   The script:
   - Installs Python 3, venv, pip, SDL2 and TTF deps, rsync.
   - Creates `/opt/openclaw-display/.venv` and installs `app/requirements.txt`.
   - Installs the systemd unit and enables it so it starts on boot.
   - Starts the display service (clock + HTTP server on port 8080).

3. **Fullscreen on the Pi (optional)**  
   Edit the Pi config so the app runs fullscreen:
   ```bash
   sudo nano /opt/openclaw-display/pi/config/display.yaml
   ```
   Set `fullscreen: true` under `app:`.

4. **Restart the service** so it picks up config:
   ```bash
   sudo systemctl restart openclaw-display
   ```
   You should see the clock on the display. If not, check: `sudo journalctl -u openclaw-display -f`.

### Option B: Deploy from your dev machine (ongoing updates)

After the first install (Option A), use this to push code/config changes and restart:

1. **Sync the repo to the Pi** (from repo root):
   ```bash
   PI_HOST=pi@raspberrypi.local ./pi/scripts/deploy.sh
   ```

2. **SSH in and restart the service**:
   ```bash
   ssh pi@raspberrypi.local 'sudo systemctl restart openclaw-display'
   ```
   Or use the project helper if you have it:
   ```bash
   ./pi/scripts/restart_remote.sh
   ```

3. **(Optional) Update venv after dependency changes**  
   If you changed `app/requirements.txt`, on the Pi:
   ```bash
   /opt/openclaw-display/.venv/bin/pip install -r /opt/openclaw-display/app/requirements.txt
   sudo systemctl restart openclaw-display
   ```

---

## Part 2: Make it the startup behavior

The install script already does this by installing and enabling the systemd unit.

- **Service file:** `pi/systemd/openclaw-display.service`
- **Installed as:** `/etc/systemd/system/openclaw-display.service`
- **Enabled = run on boot:** `systemctl enable openclaw-display` (done by `install_pi.sh`)

### Useful commands (on the Pi)

| Goal                    | Command |
|-------------------------|--------|
| Start on boot           | Already enabled after install |
| Start now               | `sudo systemctl start openclaw-display` |
| Stop                    | `sudo systemctl stop openclaw-display` |
| Restart                 | `sudo systemctl restart openclaw-display` |
| View logs (live)        | `sudo journalctl -u openclaw-display -f` |
| Status                  | `sudo systemctl status openclaw-display` |
| Disable startup         | `sudo systemctl disable openclaw-display` |

### How it runs at startup

- **After:** `network-online.target` (so the Pi has network when the app starts).
- **User:** `pi` (so it runs as the normal Pi user, not root).
- **Working directory:** `/opt/openclaw-display`.
- **Command:**  
  `/opt/openclaw-display/.venv/bin/python /opt/openclaw-display/app/main.py --config /opt/openclaw-display/pi/config/display.yaml`  
  So: no `--mock` (HTTP server runs), no `--windowed` (uses config for fullscreen).  
  To change port, add `--port 8080` (or another port) to the `ExecStart` line in the unit and run `sudo systemctl daemon-reload` then `sudo systemctl restart openclaw-display`.

---

## Part 3: OpenClaw making API calls to the display

The display runs an HTTP server (default port **8080**) and listens for pushes from OpenClaw. OpenClaw runs elsewhere (e.g. your main machine or another Pi) and calls the display’s API when something happens.

### Display URL

- **Same machine as OpenClaw:** `http://localhost:8080`
- **Pi on the network:** `http://<pi-ip>:8080` or `http://raspberrypi.local:8080`

Configure this URL in OpenClaw (e.g. env var or config) so it knows where to push.

### Endpoints OpenClaw should call

**1. POST /request** — Drive the request flow (thinking → speaking → reading → done).

| When OpenClaw…              | Call |
|-----------------------------|------|
| Starts handling a user request | `POST /request` with `{"phase": "thinking"}` |
| Starts speaking the reply   | `POST /request` with `{"phase": "speaking"}` |
| Has full text to show       | `POST /request` with `{"phase": "reading", "response_text": "Full response text here."}` |
| User dismisses or flow ends | `POST /request` with `{"phase": "done"}` |

The display will: show the animated face (thinking), then mouth + bubble, then slide left to show the response and scroll it. When you send `"done"` (or after ~14s in reading), it smoothly slides back to the clock.

**2. POST /panels** — Set the bottom notification panels (news, reminders, etc.).

```json
POST /panels
Content-Type: application/json

{
  "panels": [
    { "title": "NEWS", "items": ["Headline one.", "Headline two."] },
    { "title": "NEXT", "items": ["Call Sam at 3:15 PM"] ]
  ]
}
```

- Up to two panels are shown (e.g. NEWS and NEXT).
- Call whenever content changes (e.g. every 30 minutes or when reminders/news update).

**3. GET /status** (optional) — Check display phase and uptime for debugging.

```
GET /status   →   {"phase": "idle"|"thinking"|"speaking"|"reading"|"returning", "uptime": 123.45}
```

### Example: driving the flow from OpenClaw

When the user asks something and OpenClaw decides to answer:

1. **Request starts**  
   `POST http://<display-host>:8080/request`  
   Body: `{"phase": "thinking"}`

2. **When you begin TTS or have the reply text**  
   `POST .../request`  
   Body: `{"phase": "speaking"}`  
   (Optional: you can skip speaking and go straight to reading if you only show text.)

3. **When you have the full response to show**  
   `POST .../request`  
   Body: `{"phase": "reading", "response_text": "Today will be partly cloudy, high of 22. You have one reminder at 3:15 to call Sam."}`

4. **When the user dismisses or you want to return to the clock**  
   `POST .../request`  
   Body: `{"phase": "done"}`  
   The display will smoothly slide back to the clock (no snap).

### Example: updating panels from OpenClaw

When you have news headlines or reminders:

```bash
curl -X POST http://raspberrypi.local:8080/panels \
  -H "Content-Type: application/json" \
  -d '{"panels": [
    {"title": "NEWS", "items": ["Local team wins.", "Weather: sunny tomorrow."]},
    {"title": "NEXT", "items": ["Call Sam at 3:15 PM"]}
  ]}'
```

In OpenClaw you’d do the same with your HTTP client (e.g. `requests.post(...)` or your framework’s HTTP API).

### Where to put this in OpenClaw

- **Display base URL:** Set in OpenClaw config or env (e.g. `OPENCLAW_DISPLAY_URL=http://raspberrypi.local:8080`).
- **Request flow:** In the code path that handles a user request: when you start processing → `thinking`; when you start speaking → `speaking`; when you have the final text to show → `reading` with `response_text`; when done or dismissed → `done`.
- **Panels:** In the code that refreshes news/reminders (or on a timer), call `POST /panels` with the current items.

---

## Quick reference

| Step | What to do |
|------|------------|
| First-time setup | Copy repo to Pi → SSH in → `sudo ./pi/scripts/install_pi.sh` |
| Enable fullscreen | Set `fullscreen: true` in `pi/config/display.yaml` on the Pi, then restart service |
| Deploy updates | From dev machine: `./pi/scripts/deploy.sh` then restart service on Pi |
| Startup at boot | Already enabled by install script; use `systemctl enable/disable openclaw-display` to change |
| OpenClaw → display | POST /request with `thinking` / `speaking` / `reading` / `done`; POST /panels with news/reminders |
| Display URL | `http://<pi-ip-or-hostname>:8080` (e.g. `http://raspberrypi.local:8080`) |
