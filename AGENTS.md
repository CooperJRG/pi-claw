# AGENTS.md - OpenClaw Smart Display

## Project mission
Build and maintain a lightweight, gift-worthy Raspberry Pi 3 smart display where **idle mode is the primary product**.

## Core rules
1. **Idle state is highest priority.**
   - Big clock, high legibility, calm aesthetic, useful ambient data.
   - Any feature that hurts idle readability or stability should be rejected.
2. **Pi is deployment target, not source of truth.**
   - Make edits in repo, deploy via scripts over SSH/rsync.
   - Avoid manual one-off editing on Pi.
3. **Stay lightweight for Pi 3.**
   - Prefer simple Python + Pygame patterns.
   - Avoid heavy dependencies/frameworks unless clearly justified.
4. **No listening/wake-word UI in v1.**
   - States are idle/thinking/speaking/offline only.
5. **Mock-first integrations.**
   - New integrations must preserve reliable local fallback mode.

## Architecture expectations
- Keep app modular under `app/openclaw_display/`.
- Integration boundaries live in provider interfaces (`providers.py`).
- State transitions should flow through `DisplayStateMachine`.
- Temporary card/announcement behavior must return cleanly to idle.

## Performance constraints (Pi 3)
- Keep FPS modest (default 20).
- Prefer subtle, low-cost animations.
- Avoid unnecessary redraw complexity and allocations.
- Keep startup path simple and deterministic.

## Coding style
- Small readable modules.
- Type hints encouraged for core interfaces.
- Defensive behavior: missing data should degrade gracefully.
- Do not add dependencies casually; justify in docs/PR.

## Validation checklist after edits
Run what applies:
1. `PYTHONPATH=app pytest -q`
2. `PYTHONPATH=app python app/main.py --windowed` (sanity run)
3. `python -m py_compile app/main.py app/openclaw_display/*.py`
4. `bash -n pi/scripts/*.sh`

If hardware-specific checks were not run on Pi, explicitly say so.
