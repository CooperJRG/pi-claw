# Architecture (v1)

## System overview
OpenClaw Smart Display is a local-rendered Pygame application optimized for Raspberry Pi 3, designed to run continuously as a systemd service. The idle screen is the default and dominant user experience.

## Responsibility split: local machine vs Pi

### Local machine (source of truth)
- Develop and test code
- Commit changes in git
- Deploy to Pi via `pi/scripts/deploy.sh`
- Operate service remotely (`restart_remote.sh`, `logs_remote.sh`)

### Raspberry Pi (runtime target)
- Runs synced application code in `/opt/openclaw-display`
- Executes app via systemd service
- Displays fullscreen UI on attached square screen
- Stores runtime logs in journald

## App structure

- `app/openclaw_display/main.py` - app loop, event handling, render cadence
- `app/openclaw_display/ui.py` - all drawing/layout for idle and overlays
- `app/openclaw_display/state_machine.py` - state + temporary card lifecycle
- `app/openclaw_display/providers.py` - adapter interfaces + mock providers
- `app/openclaw_display/models.py` - domain/state dataclasses
- `app/openclaw_display/config.py` - YAML config loading

## State model
Supported assistant/system states:
- `idle` (default)
- `thinking`
- `speaking`
- `offline`

No listening state is modeled in v1.

State rendering is additive: idle layout remains the base, while temporary overlay treatment communicates non-idle states.

## Mock integration strategy
V1 uses provider interfaces so real sources can be introduced without reworking UI/state core:
- `WeatherProvider`
- `NowPlayingProvider`
- `ReminderProvider`
- `AssistantEventProvider`
- `RequestFlowProvider` (request-phase animation + response payload boundary)

Current implementations are mocks to guarantee runnable behavior with no external dependencies, including a deterministic request-flow demo provider that exercises thinking/speaking/response transitions.

## Future OpenClaw integration boundary
A future OpenClaw bridge should implement `AssistantEventProvider` and can map external events into:
- assistant state updates (idle/thinking/speaking/offline)
- temporary `DisplayCard` pushes
- now-playing metadata updates
- reminder/timer notifications

## Cron-driven / pushed cards concept
Future automation can inject temporary cards (e.g., reminders, status notes) that:
1. appear in dedicated custom card area
2. persist for configured duration
3. auto-expire
4. return to idle surface automatically

This preserves idle mode as the long-lived resting state while allowing occasional high-value interruptions.
