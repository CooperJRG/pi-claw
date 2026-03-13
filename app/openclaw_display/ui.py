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
        # Prefer broadly-available fonts; fallback handled by SysFont.
        self._fonts["clock"] = pygame.font.SysFont("Avenir Next, Helvetica Neue, DejaVu Sans", 132, bold=True)
        self._fonts["date"] = pygame.font.SysFont("Avenir Next, Helvetica Neue, DejaVu Sans", 26)
        self._fonts["title"] = pygame.font.SysFont("Avenir Next, Helvetica Neue, DejaVu Sans", 19, bold=True)
        self._fonts["body"] = pygame.font.SysFont("Avenir Next, Helvetica Neue, DejaVu Sans", 23)
        self._fonts["small"] = pygame.font.SysFont("Avenir Next, Helvetica Neue, DejaVu Sans", 17)
        self._fonts["overlay"] = pygame.font.SysFont("Avenir Next, Helvetica Neue, DejaVu Sans", 34, bold=True)

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
        self._draw_background(surface, now)
        self._draw_clock(surface, now)
        self._draw_status(surface, assistant_state)
        self._draw_complication_cards(surface, weather, now_playing, reminder)

        if assistant_state in (AssistantState.THINKING, AssistantState.SPEAKING, AssistantState.OFFLINE):
            self._draw_state_overlay(surface, assistant_state, now)

        if card:
            self._draw_custom_card(surface, card)

    def _draw_background(self, surface: pygame.Surface, now: datetime) -> None:
        w = self.config.app.width
        h = self.config.app.height
        colors = self.config.theme

        surface.fill(colors.background)

        # Warm center glow for retro/watch-face depth.
        pulse = 0.08 + 0.03 * math.sin(now.timestamp() * 0.4)
        glow_radius = int(min(w, h) * (0.34 + pulse))
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*colors.accent, 26), (w // 2, int(h * 0.34)), glow_radius)
        surface.blit(glow, (0, 0))

        # Subtle horizontal scan lines to suggest sleek-retro texture.
        line = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 4):
            pygame.draw.line(line, (255, 255, 255, 6), (0, y), (w, y), 1)
        surface.blit(line, (0, 0))

        # Frame line inspired by watch face bezel.
        frame = pygame.Rect(16, 16, w - 32, h - 32)
        pygame.draw.rect(surface, (88, 92, 102), frame, width=1, border_radius=22)

    def _draw_clock(self, surface: pygame.Surface, now: datetime) -> None:
        w = self.config.app.width
        colors = self.config.theme

        clock = now.strftime("%H:%M")
        day = now.strftime("%A · %d %b %Y")

        # Add slightly spaced glyphs for a premium watch-face feel.
        clock = " ".join(list(clock))
        clock_label = self._fonts["clock"].render(clock, True, colors.text_primary)
        day_label = self._fonts["date"].render(day.upper(), True, colors.text_secondary)

        surface.blit(clock_label, clock_label.get_rect(center=(w // 2, 158)))
        surface.blit(day_label, day_label.get_rect(center=(w // 2, 236)))

    def _draw_complication_cards(
        self,
        surface: pygame.Surface,
        weather: WeatherInfo | None,
        now_playing: NowPlayingInfo | None,
        reminder: ReminderInfo | None,
    ) -> None:
        left = 36
        top = 286
        card_h = 112
        gap = 14
        width = self.config.app.width - 72

        weather_body = (
            f"{weather.summary} · {weather.temperature_c:.0f}°C  H{weather.high_c:.0f}° L{weather.low_c:.0f}°"
            if weather
            else "No weather source"
        )
        music_body = f"{now_playing.title} — {now_playing.artist}" if now_playing else "Nothing currently playing"
        reminder_body = f"{reminder.label} at {reminder.due_at.strftime('%H:%M')}" if reminder else "No upcoming reminders"

        self._draw_panel(surface, left, top, width, card_h, "WEATHER", weather_body)
        self._draw_panel(surface, left, top + card_h + gap, width, card_h, "NOW PLAYING", music_body)
        self._draw_panel(surface, left, top + (card_h + gap) * 2, width, card_h, "NEXT", reminder_body)

    def _draw_panel(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, title: str, content: str) -> None:
        rect = pygame.Rect(x, y, w, h)
        card_bg = self.config.theme.card_background
        pygame.draw.rect(surface, card_bg, rect, border_radius=14)
        pygame.draw.rect(surface, (88, 92, 102), rect, width=1, border_radius=14)

        # Header stripe gives subtle retro appliance feel.
        header = pygame.Rect(x, y, w, 30)
        pygame.draw.rect(surface, (54, 58, 68), header, border_top_left_radius=14, border_top_right_radius=14)

        title_label = self._fonts["title"].render(title, True, self.config.theme.text_secondary)
        body_text = self._trim(content, 52)
        body_label = self._fonts["body"].render(body_text, True, self.config.theme.text_primary)

        surface.blit(title_label, (x + 12, y + 7))
        surface.blit(body_label, (x + 14, y + 53))

    def _draw_status(self, surface: pygame.Surface, state: AssistantState) -> None:
        palette = {
            AssistantState.IDLE: (148, 223, 165),
            AssistantState.THINKING: (255, 204, 122),
            AssistantState.SPEAKING: (128, 186, 255),
            AssistantState.OFFLINE: (255, 138, 138),
        }
        dot_color = palette[state]

        status_rect = pygame.Rect(32, 34, 180, 30)
        pygame.draw.rect(surface, (41, 45, 55), status_rect, border_radius=15)
        pygame.draw.rect(surface, (88, 92, 102), status_rect, width=1, border_radius=15)
        pygame.draw.circle(surface, dot_color, (46, 49), 6)

        label = self._fonts["small"].render(state.value.upper(), True, self.config.theme.text_secondary)
        surface.blit(label, (58, 41))

    def _draw_state_overlay(self, surface: pygame.Surface, state: AssistantState, now: datetime) -> None:
        overlay = pygame.Surface((self.config.app.width, self.config.app.height), pygame.SRCALPHA)
        overlay.fill((8, 10, 14, 84))
        surface.blit(overlay, (0, 0))

        if state == AssistantState.THINKING:
            dots = "." * ((now.second % 3) + 1)
            txt = self._fonts["overlay"].render(f"PROCESSING{dots}", True, self.config.theme.warning)
            sub = self._fonts["small"].render("Working on your request", True, self.config.theme.text_secondary)
        elif state == AssistantState.SPEAKING:
            txt = self._fonts["overlay"].render("SPEAKING", True, self.config.theme.accent)
            sub = self._fonts["small"].render("Delivering assistant output", True, self.config.theme.text_secondary)
        else:
            txt = self._fonts["overlay"].render("OFFLINE", True, (255, 130, 130))
            sub = self._fonts["small"].render("Clock and local placeholders only", True, self.config.theme.text_secondary)

        surface.blit(txt, txt.get_rect(center=(self.config.app.width // 2, 96)))
        surface.blit(sub, sub.get_rect(center=(self.config.app.width // 2, 130)))

    def _draw_custom_card(self, surface: pygame.Surface, card: DisplayCard) -> None:
        card_rect = pygame.Rect(62, self.config.app.height - 176, self.config.app.width - 124, 122)
        pygame.draw.rect(surface, (70, 76, 92), card_rect, border_radius=14)
        pygame.draw.rect(surface, self.config.theme.accent, card_rect, width=2, border_radius=14)

        title = self._fonts["title"].render(card.title.upper(), True, self.config.theme.accent)
        body = self._fonts["body"].render(self._trim(card.body, 55), True, self.config.theme.text_primary)
        surface.blit(title, (card_rect.x + 14, card_rect.y + 14))
        surface.blit(body, (card_rect.x + 14, card_rect.y + 55))

    @staticmethod
    def _trim(content: str, limit: int) -> str:
        if len(content) <= limit:
            return content
        return content[: limit - 1] + "…"
