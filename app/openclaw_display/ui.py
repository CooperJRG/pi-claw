from __future__ import annotations

import math
from datetime import datetime

import pygame

from .config import DisplayConfig
from .models import AssistantState, DisplayCard, NowPlayingInfo, ReminderInfo, WeatherInfo


class DisplayRenderer:
    def __init__(self, config: DisplayConfig) -> None:
        self.config = config
        self._fonts: dict[str, pygame.font.Font] = {}

    def setup_fonts(self) -> None:
        pygame.font.init()
        self._fonts["clock"] = pygame.font.SysFont("DejaVu Sans", 120, bold=True)
        self._fonts["h1"] = pygame.font.SysFont("DejaVu Sans", 38, bold=True)
        self._fonts["h2"] = pygame.font.SysFont("DejaVu Sans", 30, bold=True)
        self._fonts["body"] = pygame.font.SysFont("DejaVu Sans", 24)
        self._fonts["small"] = pygame.font.SysFont("DejaVu Sans", 20)

    def draw(
        self,
        surface: pygame.Surface,
        now: datetime,
        assistant_state: AssistantState,
        weather: WeatherInfo | None,
        now_playing: NowPlayingInfo | None,
        reminder: ReminderInfo | None,
        card: DisplayCard | None,
    ) -> None:
        w = self.config.app.width
        h = self.config.app.height
        colors = self.config.theme

        surface.fill(colors.background)
        breath = 0.08 + 0.06 * math.sin(now.timestamp() * 0.6)
        glow_radius = int(min(w, h) * (0.45 + breath))
        pygame.draw.circle(
            surface,
            (*colors.accent, 35),
            (w // 2, h // 2),
            glow_radius,
        )

        self._draw_clock(surface, now)
        self._draw_cards(surface, weather, now_playing, reminder)
        self._draw_status(surface, assistant_state, now)

        if assistant_state in (AssistantState.THINKING, AssistantState.SPEAKING, AssistantState.OFFLINE):
            self._draw_state_overlay(surface, assistant_state, now)

        if card:
            self._draw_custom_card(surface, card)

    def _draw_clock(self, surface: pygame.Surface, now: datetime) -> None:
        clock = now.strftime("%H:%M")
        day = now.strftime("%A, %d %b %Y")

        clock_label = self._fonts["clock"].render(clock, True, self.config.theme.text_primary)
        day_label = self._fonts["body"].render(day, True, self.config.theme.text_secondary)

        surface.blit(clock_label, clock_label.get_rect(center=(self.config.app.width // 2, 150)))
        surface.blit(day_label, day_label.get_rect(center=(self.config.app.width // 2, 235)))

    def _draw_cards(
        self,
        surface: pygame.Surface,
        weather: WeatherInfo | None,
        now_playing: NowPlayingInfo | None,
        reminder: ReminderInfo | None,
    ) -> None:
        left = 36
        top = 280
        card_h = 118
        gap = 14

        self._draw_panel(
            surface,
            left,
            top,
            self.config.app.width - 72,
            card_h,
            "Weather",
            f"{weather.summary}  {weather.temperature_c:.0f}°C  H:{weather.high_c:.0f}° L:{weather.low_c:.0f}°" if weather else "Weather unavailable",
        )
        self._draw_panel(
            surface,
            left,
            top + card_h + gap,
            self.config.app.width - 72,
            card_h,
            "Now Playing",
            f"{now_playing.title} — {now_playing.artist}" if now_playing else "Nothing playing",
        )
        reminder_text = (
            f"{reminder.label} @ {reminder.due_at.strftime('%H:%M')}" if reminder else "No upcoming reminders"
        )
        self._draw_panel(
            surface,
            left,
            top + (card_h + gap) * 2,
            self.config.app.width - 72,
            card_h,
            "Next Reminder",
            reminder_text,
        )

    def _draw_panel(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, title: str, content: str) -> None:
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, self.config.theme.card_background, rect, border_radius=14)
        pygame.draw.rect(surface, (62, 70, 86), rect, width=1, border_radius=14)

        title_label = self._fonts["small"].render(title, True, self.config.theme.text_secondary)
        body_label = self._fonts["body"].render(content[:56], True, self.config.theme.text_primary)

        surface.blit(title_label, (x + 14, y + 16))
        surface.blit(body_label, (x + 14, y + 56))

    def _draw_status(self, surface: pygame.Surface, state: AssistantState, now: datetime) -> None:
        palette = {
            AssistantState.IDLE: (120, 220, 160),
            AssistantState.THINKING: (255, 204, 122),
            AssistantState.SPEAKING: (128, 186, 255),
            AssistantState.OFFLINE: (255, 130, 130),
        }

        dot_color = palette[state]
        pygame.draw.circle(surface, dot_color, (42, 42), 8)

        label = self._fonts["small"].render(state.value.upper(), True, self.config.theme.text_secondary)
        surface.blit(label, (58, 30))

        sec = self._fonts["small"].render(now.strftime("%H:%M:%S"), True, self.config.theme.text_secondary)
        surface.blit(sec, (self.config.app.width - 138, 30))

    def _draw_state_overlay(self, surface: pygame.Surface, state: AssistantState, now: datetime) -> None:
        overlay = pygame.Surface((self.config.app.width, self.config.app.height), pygame.SRCALPHA)
        overlay.fill((8, 10, 14, 70))
        surface.blit(overlay, (0, 0))

        if state == AssistantState.THINKING:
            label = "Processing"
            dots = "." * ((now.second % 3) + 1)
            msg = f"{label}{dots}"
            txt = self._fonts["h1"].render(msg, True, self.config.theme.warning)
            surface.blit(txt, txt.get_rect(center=(self.config.app.width // 2, 95)))
        elif state == AssistantState.SPEAKING:
            txt = self._fonts["h1"].render("Speaking", True, self.config.theme.accent)
            sub = self._fonts["small"].render("Output in progress", True, self.config.theme.text_secondary)
            surface.blit(txt, txt.get_rect(center=(self.config.app.width // 2, 95)))
            surface.blit(sub, sub.get_rect(center=(self.config.app.width // 2, 132)))
        elif state == AssistantState.OFFLINE:
            txt = self._fonts["h1"].render("Offline Mode", True, (255, 130, 130))
            sub = self._fonts["small"].render("Using local placeholders", True, self.config.theme.text_secondary)
            surface.blit(txt, txt.get_rect(center=(self.config.app.width // 2, 95)))
            surface.blit(sub, sub.get_rect(center=(self.config.app.width // 2, 132)))

    def _draw_custom_card(self, surface: pygame.Surface, card: DisplayCard) -> None:
        card_rect = pygame.Rect(70, self.config.app.height - 176, self.config.app.width - 140, 124)
        pygame.draw.rect(surface, (51, 64, 89), card_rect, border_radius=14)
        pygame.draw.rect(surface, self.config.theme.accent, card_rect, width=2, border_radius=14)

        title = self._fonts["small"].render(card.title, True, self.config.theme.accent)
        body = self._fonts["body"].render(card.body[:60], True, self.config.theme.text_primary)
        surface.blit(title, (card_rect.x + 16, card_rect.y + 16))
        surface.blit(body, (card_rect.x + 16, card_rect.y + 58))
