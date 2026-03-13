"""Lightweight HTTP server that receives push events from OpenClaw.

Runs in a daemon thread so the pygame render loop is never blocked.

Endpoints
---------
POST /panels
    Body: {"panels": [{"title": "NEWS", "items": ["...", ...]}, ...]}
    Updates the info panels shown at the bottom of the display.
    OpenClaw should call this every 30 minutes (or whenever content changes).

POST /request
    Body: {"phase": "thinking"}
           {"phase": "speaking"}
           {"phase": "reading", "response_text": "Full response text here."}
           {"phase": "done"}
    Drives the request flow animation on the display.

GET /status
    Returns current phase + uptime — useful for debugging.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING

from .models import InfoPanel
from .shared_state import SharedDisplayState

log = logging.getLogger(__name__)

VALID_PHASES = {"thinking", "speaking", "reading", "done"}


def _make_handler(state: SharedDisplayState) -> type[BaseHTTPRequestHandler]:
    """Return a request handler class closed over *state*."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:  # noqa: ANN001
            log.debug(fmt, *args)

        # ------------------------------------------------------------------
        # Routing
        # ------------------------------------------------------------------

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/status":
                self._json(200, {"phase": state.phase, "uptime": time.time()})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid JSON"})
                return

            if self.path == "/panels":
                self._handle_panels(body)
            elif self.path == "/request":
                self._handle_request(body)
            else:
                self._json(404, {"error": "not found"})

        # ------------------------------------------------------------------
        # Handlers
        # ------------------------------------------------------------------

        def _handle_panels(self, body: dict) -> None:
            raw_panels = body.get("panels", [])
            if not isinstance(raw_panels, list):
                self._json(400, {"error": "panels must be a list"})
                return

            panels: list[InfoPanel] = []
            for p in raw_panels:
                title = str(p.get("title", ""))
                items = [str(i) for i in p.get("items", [])]
                if title:
                    panels.append(InfoPanel(title=title, items=items))

            state.push_panels(panels)
            log.info("Panels updated: %d panel(s)", len(panels))
            self._json(200, {"ok": True, "count": len(panels)})

        def _handle_request(self, body: dict) -> None:
            phase = body.get("phase", "")
            if phase not in VALID_PHASES:
                self._json(400, {"error": f"phase must be one of {sorted(VALID_PHASES)}"})
                return

            response_text = str(body.get("response_text", ""))

            if phase == "done":
                # Start smooth slide-back; provider will transition to idle after RETURN_DURATION
                state.push_phase("returning")
            else:
                state.push_phase(phase, response_text)

            log.info("Request phase → %s", phase)
            self._json(200, {"ok": True, "phase": phase})

        # ------------------------------------------------------------------
        # Helpers
        # ------------------------------------------------------------------

        def _json(self, code: int, data: dict) -> None:
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


class DisplayServer:
    """Wraps HTTPServer in a daemon thread."""

    def __init__(self, state: SharedDisplayState, host: str = "0.0.0.0", port: int = 8080) -> None:
        self._state = state
        self._host = host
        self._port = port
        self._server: HTTPServer | None = None

    def start(self) -> None:
        handler = _make_handler(self._state)
        self._server = HTTPServer((self._host, self._port), handler)
        thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        thread.start()
        log.info("DisplayServer listening on %s:%d", self._host, self._port)

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
