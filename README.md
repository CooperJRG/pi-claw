# OpenClaw Smart Display (Raspberry Pi v1)

A lightweight, square-first smart display app built for Raspberry Pi 3. This v1 is intentionally practical:

- **Idle mode is the core product** (big clock + useful ambient panels)
- sleek-retro visual styling (Apple Lisa + Apple Watch face inspired)
- graceful fallback if integrations are missing
- mock-driven runtime that works tomorrow without external APIs
- Pi is a **deployment target**, not the source-of-truth dev machine

## Chosen stack

- **Python 3 + Pygame** for lightweight fullscreen rendering on Pi 3.
- Minimal dependencies (`pygame`, `PyYAML`) for reliability and low overhead.
- `systemd` for auto-start and remote operations.
- `rsync + ssh` scripts for fast deployment and maintenance.

## Repository layout

```text
.
├── AGENTS.md
├── README.md
├── app
│   ├── main.py
│   ├── openclaw_display
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── providers.py
│   │   ├── state_machine.py
│   │   └── ui.py
│   └── requirements.txt
├── docs
│   ├── ARCHITECTURE.md
│   └── UI_SPEC.md
├── pi
│   ├── config
│   │   └── display.yaml
│   ├── scripts
│   │   ├── deploy.sh
│   │   ├── install_pi.sh
│   │   ├── logs_remote.sh
│   │   └── restart_remote.sh
│   └── systemd
│       └── openclaw-display.service
└── tests
    └── test_state_machine.py
```

## Local development flow

1. Create environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r app/requirements.txt
   pip install pytest
   ```
2. Run app (windowed dev mode):
   ```bash
   PYTHONPATH=app python app/main.py --windowed
   ```
3. Dev hotkeys:
   - `1`: force idle (20s)
   - `2`: force thinking (20s)
   - `3`: force speaking (20s)
   - `4`: force offline (20s)
   - `q` / `esc`: exit

## Pi setup flow (first install)

Assumptions:
- Raspberry Pi OS
- SSH access working
- repo copied to your local machine (source of truth)

On the Pi (or over SSH):

```bash
cd /path/to/repo
sudo bash pi/scripts/install_pi.sh
```

What this does:
- installs apt dependencies + SDL libs
- syncs repo to `/opt/openclaw-display`
- creates `/opt/openclaw-display/.venv`
- installs Python deps
- installs and enables `openclaw-display.service`
- starts the service

## Deploy to Pi after edits

From your local dev machine:

```bash
PI_HOST=pi@raspberrypi.local bash pi/scripts/deploy.sh
PI_HOST=pi@raspberrypi.local bash pi/scripts/restart_remote.sh
```

## Restart and inspect logs remotely

Restart:
```bash
PI_HOST=pi@raspberrypi.local bash pi/scripts/restart_remote.sh
```

Recent logs:
```bash
PI_HOST=pi@raspberrypi.local bash pi/scripts/logs_remote.sh
```

Follow logs live:
```bash
PI_HOST=pi@raspberrypi.local FOLLOW=1 bash pi/scripts/logs_remote.sh
```

## Runtime behavior summary

- Default surface is idle mode with strong glanceable layout.
- Lightweight overlays represent thinking, speaking, offline states.
- No microphone/listening UI is implemented.
- Weather/music/reminders/custom cards are mock-backed for stable demo mode.
- Custom temporary cards auto-expire and return to idle.

## v1 limitations

- No real weather/music/calendar APIs yet (by design).
- Mock event provider simulates assistant states on a schedule.
- No remote push endpoint yet; integration boundary exists via provider interfaces.
- Visual tuning may still be adjusted on physical Pi screen for exact DPI/readability.

## Tomorrow Runbook (exact steps)

1. **On your dev machine**
   ```bash
   git clone <your-repo>
   cd pi-claw
   ```
2. **Test locally quickly**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r app/requirements.txt pytest
   PYTHONPATH=app pytest -q
   PYTHONPATH=app python app/main.py --windowed
   ```
3. **Install on Pi (first time)**
   ```bash
   scp -r . pi@raspberrypi.local:/home/pi/pi-claw
   ssh pi@raspberrypi.local 'cd /home/pi/pi-claw && sudo bash pi/scripts/install_pi.sh'
   ```
4. **Iterate after edits**
   ```bash
   PI_HOST=pi@raspberrypi.local bash pi/scripts/deploy.sh
   PI_HOST=pi@raspberrypi.local bash pi/scripts/restart_remote.sh
   PI_HOST=pi@raspberrypi.local FOLLOW=1 bash pi/scripts/logs_remote.sh
   ```
5. **Done**
   - Reboot Pi if desired; service auto-starts on boot.
