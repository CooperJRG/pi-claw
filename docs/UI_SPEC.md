# UI Specification (v1)

## Design intent
A calm, legible, gift-worthy square display with subtle personality and a sleek-retro finish inspired by Apple Lisa-era restraint and Apple Watch face clarity. Idle screen quality is the main success criteria.

## Visual priorities
1. Time readability
2. Idle mode utility and beauty
3. Current assistant/system state visibility
4. Secondary cards (weather/music/reminder)
5. Temporary custom push card

## Square-first layout
- Centered large digital clock near top-middle
- Date/week line beneath clock
- Three stacked info panels in lower half
- Compact status indicator in top-left
- Small clock seconds top-right
- Optional temporary custom card anchored near bottom

## Idle state (primary)
- Dominant large time (`HH:MM`)
- Date and weekday for context
- Ambient panels:
  - Weather (or unavailable placeholder)
  - Now Playing (or nothing playing placeholder)
  - Next Reminder (or no reminders placeholder)
- Subtle breathing glow behind content for personality

## Thinking / processing state
- Keep idle layout visible
- Add light dim overlay
- Show "Processing..." text with low-cost animated dots
- Temporary state feel (not full visual rewrite)

## Speaking / output state
- Keep idle base visible
- Add overlay label "Speaking"
- Optional single line "Output in progress"
- No heavy waveform rendering in v1

## Offline state
- Keep clock and core layout visible
- Show clear offline label and local fallback messaging
- Avoid crash/freeze when integrations unavailable

## Temporary pushed card behavior
- Appears as highlighted card near bottom
- Includes title + short body text
- Auto-expires and fades back to pure idle
- Intended for future OpenClaw/cron-triggered reminders or announcements


## Request transition demo behavior (dummy v1)
- On incoming request, idle transitions to a **face mode**.
- During thinking, large clock is replaced by animated face; current time moves to top-left.
- During speaking start, mouth opens and a speech-bubble corner grows from the left side.
- Display then slides left to reveal a full response panel, with slow auto-scroll for readability.
- After timeout, panel slides right and UI returns to idle cleanly.

## Style constraints
- Calm dark background + warm champagne accent color
- High contrast text for glanceability
- Avoid clutter and excessive constant animation
- Avoid playful/cartoon face metaphors in v1
- Use restrained geometric framing and "complication" style cards instead of flashy chrome
