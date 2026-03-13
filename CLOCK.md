# CLOCK.md — OpenClaw Smart Display Clock Vision

This document describes the intended design and behavior of the main clock screen. The display is a **retro smart clock** driven by OpenClaw: clean, friendly, and legible, with the clock as the hero and a small set of widgets and notifications around it.

---

## Core concept

- **Split-flap clock.** The time is shown in a split-flap (flip) style: numerals flip to reveal the current time, like classic airport or station boards. Transitions (e.g. idle → thinking) can echo this with a flip-to-face effect so the whole experience feels like one coherent flip clock.
- **Long numerals, most of the screen.** The time digits are large and high-contrast, taking up most of the vertical space. Legibility at a glance is the priority; the clock is the primary product.
- **Macintosh-inspired.** Aesthetic is clean and friendly, with a slight retro feel: clear typography, restrained palette, soft edges, no clutter. Think early Mac: approachable, human, and calm rather than flashy or corporate.
- **Retro smart clock.** It’s a clock first, with a small number of smart elements (weather, notifications) that don’t compete with the time. OpenClaw controls what appears in those areas.

---

## Layout (idle)

- **Top left:** Small **weather widget** — temperature and condition only (e.g. “21° Partly cloudy”). Compact, always in the same spot, low visual weight.
- **Center / majority of screen:** **Split-flap time** — long numerals (hours and minutes; optionally seconds), flip-style. This is the main focus; layout and styling should give it most of the space and attention.
- **Bottom:** Space for **1 or 2 notifications** — e.g. one line each, or one short block. Typical content:
  - **News** (headline or short summary)
  - **Reminders** (e.g. “Call Sam at 3:15 PM”)
  OpenClaw decides what to show here; the clock layout must **always** reserve this strip so 1–2 items fit without overlapping the time or the weather.
- **No other chrome.** Avoid extra panels, logos, or decorative elements that aren’t weather, time, or the notification strip. Status (idle/thinking/speaking/offline) can be minimal (e.g. small indicator) so the clock stays clean.

---

## Idle behavior and request flow (prompted by OpenClaw)

When a request comes in, **OpenClaw** prompts the display to leave idle and run through a defined sequence. For now this is demonstrated with **dummy requests**; the same flow will later be driven by real OpenClaw triggers.

1. **Request arrives → thinking mode**
   - The clock **dynamically turns into an animated face** (e.g. a flip-clock-style transition so the time “flips” to reveal the face).
   - The **time moves to the top left** of the screen and stays visible there in a compact form for the duration of the request.

2. **Thinking**
   - The **animated face** is shown (eyes, subtle “thinking” mouth).
   - A “Thinking…” or similar indicator may appear. The face remains the focus until the response starts.

3. **Response starts (speaking)**
   - The **mouth opens** and animates as if speaking.
   - A **speech-bubble corner** begins to appear toward the **left** of the screen, hinting at the coming response panel.

4. **Full response (reading)**
   - The display **slides left** and a **full response panel** is shown (the “speech bubble” expands into a readable card).
   - The response text **scrolls slowly** so the full content can be read.
   - This phase lasts for a set duration (x time).

5. **Return to idle**
   - The screen **slides right** and the view returns to the **idle** layout: big split-flap clock, weather top left, notifications at the bottom.
   - The face and response panel are gone; the clock is again the hero.

**Summary of the flow:** Idle (clock) → request in → flip to animated face, time in top left → thinking → mouth opens, bubble corner appears → slide left, full response, slow scroll → after x time, slide right → back to idle. All of this is **prompted by OpenClaw** (and currently exercised with dummy request flows).

---

## Who controls what

- **OpenClaw** controls:
  - **When a request starts** — prompting the transition from idle to thinking and the full request flow above (flip to face, speech bubble, slide to response, return to idle).
  - What appears in the **notification area** (news, reminders, or other short alerts).
  - When **cards/announcements** show and when they dismiss (return to the standard clock layout).
  - **State transitions** (idle ↔ thinking/speaking/reading/returning), including flip-to-face and slide behavior.
- The **clock app** is responsible for:
  - Rendering the split-flap time, weather widget, and notification strip according to this layout.
  - Executing flip/transition animations and keeping the clock readable at all times.

---

## Design principles

1. **Clean and friendly.** Every element has a reason; nothing feels harsh or noisy. Type and spacing support quick reading and a calm mood.
2. **Retro, not dated.** The split-flap and Mac-inspired cues should feel intentional and cohesive, not like a generic “old” skin.
3. **Clock first.** Weather and notifications support the experience; they never dominate or obscure the time.
4. **Reserved space.** The bottom notification area is a fixed part of the layout so OpenClaw can reliably show 1 or 2 items without layout reflow or overlap.

---

## Summary

- **Split-flap** time with **long numerals** taking most of the screen.
- **Macintosh-inspired**: clean, friendly, retro smart clock.
- **Top left:** small weather (temp + condition).
- **Bottom:** dedicated space for **1 or 2 notifications** (news, reminders, etc.), controlled by OpenClaw.
- **OpenClaw** prompts the **request flow**: idle → flip to animated face (time in top left) → thinking → mouth + speech-bubble corner → slide left to full response (slow scroll) → after x time slide right → back to idle. This is demonstrated with dummy requests today and will be driven by OpenClaw in production.

This is the target for the main clock UI; implementation in `app/openclaw_display/` should move toward this layout and behavior while respecting AGENTS.md (idle priority, Pi 3 constraints, mock-first).
