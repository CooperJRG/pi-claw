from __future__ import annotations

import argparse
import logging
from datetime import datetime

import pygame

from .config import load_config
from .providers import MockInfoPanelProvider, MockRequestFlowProvider, MockWeatherProvider
from .remote_providers import RemoteInfoPanelProvider, RemoteRequestFlowProvider
from .server import DisplayServer
from .shared_state import SharedDisplayState
from .state_machine import DisplayStateMachine
from .ui import DisplayRenderer

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw Smart Display")
    parser.add_argument("--config", default="pi/config/display.yaml", help="Path to YAML config")
    parser.add_argument("--windowed", action="store_true", help="Force windowed mode")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock providers (no HTTP server — for local development)",
    )
    parser.add_argument("--port", type=int, default=8080, help="HTTP server port (default 8080)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    pygame.init()
    flags = pygame.FULLSCREEN if config.app.fullscreen and not args.windowed else 0
    screen = pygame.display.set_mode((config.app.width, config.app.height), flags)
    pygame.display.set_caption(config.app.title)

    clock = pygame.time.Clock()
    renderer = DisplayRenderer(config)
    renderer.setup()

    weather_prov = MockWeatherProvider()
    server: DisplayServer | None = None

    if args.mock:
        panel_prov = MockInfoPanelProvider()
        request_prov = MockRequestFlowProvider()
    else:
        state = SharedDisplayState()
        server = DisplayServer(state, port=args.port)
        server.start()
        panel_prov = RemoteInfoPanelProvider(state)
        request_prov = RemoteRequestFlowProvider(state)

    machine = DisplayStateMachine(request_prov)
    weather = weather_prov.get_weather()

    running = True
    while running:
        now = datetime.now()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

        state_val, request = machine.tick(now)
        panels = panel_prov.get_panels()

        renderer.draw(
            surface=screen,
            now=now,
            state=state_val,
            weather=weather,
            panels=panels,
            request=request,
        )

        pygame.display.flip()
        clock.tick(config.app.fps)

    if server:
        server.stop()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
