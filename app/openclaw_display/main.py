from __future__ import annotations

import argparse
from datetime import datetime, timedelta

import pygame

from .config import load_config
from .models import AssistantState, RequestPhase
from .providers import (
    MockAssistantEventProvider,
    MockNowPlayingProvider,
    MockReminderProvider,
    MockRequestFlowProvider,
    MockWeatherProvider,
)
from .state_machine import DisplayStateMachine
from .ui import DisplayRenderer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw Smart Display")
    parser.add_argument("--config", default="pi/config/display.yaml", help="Path to YAML config")
    parser.add_argument("--windowed", action="store_true", help="Force windowed mode for development")
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
    renderer.setup_fonts()

    weather_provider = MockWeatherProvider()
    now_playing_provider = MockNowPlayingProvider()
    reminder_provider = MockReminderProvider()
    event_provider = MockAssistantEventProvider()
    request_provider = MockRequestFlowProvider()

    machine = DisplayStateMachine(event_provider)

    weather = weather_provider.get_weather()
    now_playing = now_playing_provider.get_now_playing()
    reminder = reminder_provider.get_next_reminder()

    running = True
    manual_state: tuple[AssistantState, datetime] | None = None

    while running:
        now = datetime.now()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_1:
                    manual_state = (AssistantState.IDLE, now + timedelta(seconds=20))
                elif event.key == pygame.K_2:
                    manual_state = (AssistantState.THINKING, now + timedelta(seconds=20))
                elif event.key == pygame.K_3:
                    manual_state = (AssistantState.SPEAKING, now + timedelta(seconds=20))
                elif event.key == pygame.K_4:
                    manual_state = (AssistantState.OFFLINE, now + timedelta(seconds=20))

        snapshot = machine.tick(now)
        request_visual = request_provider.get_request_visual(now)

        state = snapshot.state
        if request_visual:
            if request_visual.phase == RequestPhase.THINKING:
                state = AssistantState.THINKING
            else:
                state = AssistantState.SPEAKING

        if manual_state and now < manual_state[1]:
            state = manual_state[0]
        elif manual_state and now >= manual_state[1]:
            manual_state = None

        renderer.draw(
            surface=screen,
            now=now,
            assistant_state=state,
            weather=weather,
            now_playing=now_playing,
            reminder=reminder,
            card=snapshot.card,
            request_visual=request_visual,
        )
        pygame.display.flip()
        clock.tick(config.app.fps)

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
