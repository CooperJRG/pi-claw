"""Providers backed by SharedDisplayState (pushed by OpenClaw over HTTP)."""
from __future__ import annotations

import time
from datetime import datetime

from .models import InfoPanel, RequestPhase, RequestVisual
from .providers import InfoPanelProvider, RequestFlowProvider
from .shared_state import READ_DURATION, RETURN_DURATION, SharedDisplayState


class RemoteInfoPanelProvider(InfoPanelProvider):
    """Returns whatever panels OpenClaw last pushed via POST /panels."""

    def __init__(self, state: SharedDisplayState) -> None:
        self._state = state

    def get_panels(self) -> list[InfoPanel]:
        with self._state.lock:
            return list(self._state.panels)


class RemoteRequestFlowProvider(RequestFlowProvider):
    """Translates SharedDisplayState into RequestVisual frames.

    Phase lifecycle (driven by OpenClaw pushes):
        idle      → no visual (clock shown)
        thinking  → THINKING  (held until OpenClaw pushes next phase)
        speaking  → SPEAKING  (held until OpenClaw pushes next phase)
        reading   → READING   (auto-advances to RETURNING after READ_DURATION)
                  → RETURNING (smooth slide back; then idle after RETURN_DURATION)
        done      → RETURNING (smooth slide back; then idle after RETURN_DURATION)
    """

    def __init__(self, state: SharedDisplayState) -> None:
        self._state = state

    def get_request_visual(self, now: datetime) -> RequestVisual | None:
        phase, response_text, phase_start, _ = self._state.snapshot()
        elapsed = time.time() - phase_start

        if phase == "idle":
            return None

        if phase == "thinking":
            return RequestVisual(
                phase=RequestPhase.THINKING,
                response_text="",
                phase_progress=min(1.0, elapsed / 999),
                scroll_progress=0.0,
            )

        if phase == "speaking":
            return RequestVisual(
                phase=RequestPhase.SPEAKING,
                response_text=response_text,
                phase_progress=min(1.0, elapsed / 999),
                scroll_progress=0.0,
            )

        if phase == "reading":
            if elapsed < READ_DURATION:
                # Still reading — slide in, scroll through response
                p = elapsed / READ_DURATION
                return RequestVisual(
                    phase=RequestPhase.READING,
                    response_text=response_text,
                    phase_progress=p,
                    scroll_progress=p,
                )
            ret_elapsed = elapsed - READ_DURATION
            if ret_elapsed < RETURN_DURATION:
                # Sliding back to idle (auto after 14s)
                return RequestVisual(
                    phase=RequestPhase.RETURNING,
                    response_text=response_text,
                    phase_progress=ret_elapsed / RETURN_DURATION,
                    scroll_progress=1.0,
                )
            # Fully returned — reset to idle
            self._state.push_phase("idle")
            return None

        if phase == "returning":
            # API sent "done" or we entered returning from reading — smooth slide back
            if elapsed < RETURN_DURATION:
                return RequestVisual(
                    phase=RequestPhase.RETURNING,
                    response_text=response_text,
                    phase_progress=elapsed / RETURN_DURATION,
                    scroll_progress=1.0,
                )
            self._state.push_phase("idle")
            return None

        return None
