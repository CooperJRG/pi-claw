# Rebuild prompt — OpenClaw Smart Display

**Use this prompt with Claude Code (or similar) to rebuild the display from scratch against the spec.**

---

## Instruction

**Throw out the previous implementation.** The current code in `app/openclaw_display/` is a rough prototype. Do not treat it as sacred. You may delete, rewrite, or replace any of it. The goal is to build a **much better** project that adheres to the spec.

**The spec is CLOCK.md.** Treat **CLOCK.md** as the bible. Every layout choice, every transition, and every behavior must align with what CLOCK.md describes:

- **Idle layout:** Split-flap clock with long numerals taking most of the screen; small weather widget top left; reserved strip at the bottom for 1–2 notifications (news, reminders). Macintosh-inspired: clean, friendly, retro. No extra chrome.
- **Request flow (prompted by OpenClaw):** When a request comes in, the clock flips into an animated face and the time moves to the top left. Then: thinking (animated face) → speaking (mouth opens, speech-bubble corner appears toward the left) → full response (display slides left, response panel with slow scroll) → after x time, slide right back to idle.
- **OpenClaw** controls when requests start, what goes in the notification area, and state transitions. For now, support **dummy requests** so the full flow can be demonstrated without a live OpenClaw backend.

Rebuild the display app so that:

1. **Idle** matches CLOCK.md’s layout and aesthetic (split-flap time, weather top left, 1–2 notifications at bottom).
2. **Request flow** matches CLOCK.md’s sequence (flip to face, time in top left, thinking → speaking → bubble corner → slide left → full response with slow scroll → slide right → idle).
3. The codebase stays **modular** under `app/openclaw_display/`, with clear boundaries (e.g. providers, state machine) as in **AGENTS.md**.
4. **AGENTS.md** constraints still apply: lightweight for Raspberry Pi 3, modest FPS, mock-first, no wake-word UI in v1.

Do not preserve the old structure or naming for its own sake. If a cleaner architecture emerges from CLOCK.md, use it. The only non‑negotiable references are **CLOCK.md** (product/design spec) and **AGENTS.md** (project rules and constraints).

---

## Suggested copy-paste for Claude

```
Rebuild the OpenClaw Smart Display app in this repo. Treat the existing code in app/openclaw_display/ as disposable—throw it out or rewrite it freely. The single source of truth is CLOCK.md: follow its layout (split-flap clock, weather top left, 1–2 notifications at bottom), its Macintosh-inspired aesthetic, and its full request flow (flip to animated face, time in top left, thinking → speaking with speech-bubble corner → slide left to full response with slow scroll → slide right back to idle). OpenClaw prompts this flow; support dummy requests so the flow is demonstrable. Keep the app modular and Pi 3–friendly per AGENTS.md. Prioritize CLOCK.md over the current implementation.
```
