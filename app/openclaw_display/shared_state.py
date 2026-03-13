"""Thread-safe shared state between the HTTP server and the pygame render loop."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from .models import InfoPanel

# How long the display lingers on the response before sliding back to idle
READ_DURATION = 14.0
RETURN_DURATION = 2.0


@dataclass
class SharedDisplayState:
    """All mutable state pushed by OpenClaw and consumed by the render loop."""

    # Info panels (news, reminders, etc.)
    panels: list[InfoPanel] = field(default_factory=list)

    # Current request phase: "idle" | "thinking" | "speaking" | "reading"
    phase: str = "idle"
    response_text: str = ""
    phase_start: float = field(default_factory=time.time)

    # Internal lock — always acquire before reading or writing the fields above
    lock: threading.Lock = field(default_factory=threading.Lock)

    def push_phase(self, phase: str, response_text: str = "") -> None:
        """Called from the HTTP thread to advance the request state."""
        with self.lock:
            self.phase = phase
            self.phase_start = time.time()
            if response_text:
                self.response_text = response_text

    def push_panels(self, panels: list[InfoPanel]) -> None:
        with self.lock:
            self.panels = panels

    def snapshot(self) -> tuple[str, str, float, list[InfoPanel]]:
        """Return (phase, response_text, phase_start, panels) atomically."""
        with self.lock:
            return self.phase, self.response_text, self.phase_start, list(self.panels)
