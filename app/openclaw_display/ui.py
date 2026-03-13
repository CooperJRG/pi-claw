from __future__ import annotations

import math
from datetime import datetime

import pygame

from .config import DisplayConfig
from .models import AssistantState, DisplayCard, NowPlayingInfo, ReminderInfo, RequestPhase, RequestVisual, WeatherInfo


class DisplayRenderer:
    def __init__(self, config: DisplayConfig) -> None:
        self.config = config
        self._fonts: dict[str, pygame.font.Font] = {}

    def setup_fonts(self) -> None:
        pygame.font.init()
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
        request_visual: RequestVisual | None,
    ) -> None:
        self._draw_background(surface, now)

        left_shift = 0
        if request_visual and request_visual.phase in (RequestPhase.READING, RequestPhase.RETURNING):
            target = int(self.config.app.width * 0.64)
            progress = request_visual.phase_progress
            if request_visual.phase == RequestPhase.READING:
                left_shift = int(target * min(progress * 2.3, 1.0))
            else:
                left_shift = int(target * max(1.0 - progress, 0.0))

        if request_visual:
            self._draw_face_mode(surface, now, request_visual, left_shift)
        else:
            self._draw_idle(surface, now, assistant_state, weather, now_playing, reminder, card)

    def _draw_idle(
        self,
        surface: pygame.Surface,
        now: datetime,
        assistant_state: AssistantState,
        weather: WeatherInfo | None,
        now_playing: NowPlayingInfo | None,
        reminder: ReminderInfo | None,
        card: DisplayCard | None,
    ) -> None:
        self._draw_clock(surface, now)
        self._draw_status(surface, assistant_state)
        self._draw_complication_cards(surface, weather, now_playing, reminder)

        if assistant_state == AssistantState.OFFLINE:
            self._draw_offline_banner(surface)
        if card:
            self._draw_custom_card(surface, card)

    def _draw_face_mode(self, surface: pygame.Surface, now: datetime, req: RequestVisual, left_shift: int) -> None:
        face_layer = pygame.Surface((self.config.app.width, self.config.app.height), pygame.SRCALPHA)
        self._draw_clock_small(face_layer, now)
        self._draw_face(face_layer, req, now)
        self._draw_status(face_layer, AssistantState.THINKING if req.phase == RequestPhase.THINKING else AssistantState.SPEAKING)
        surface.blit(face_layer, (-left_shift, 0))

        if req.phase in (RequestPhase.SPEAKING, RequestPhase.READING, RequestPhase.RETURNING):
            bubble_progress = 0.0
            if req.phase == RequestPhase.SPEAKING:
                bubble_progress = req.phase_progress
            else:
                bubble_progress = 1.0
            self._draw_response_panel(surface, req.response_text, req.response_scroll_px, bubble_progress, left_shift)

    def _draw_background(self, surface: pygame.Surface, now: datetime) -> None:
        w = self.config.app.width
        h = self.config.app.height
        colors = self.config.theme
        surface.fill(colors.background)

        pulse = 0.08 + 0.03 * math.sin(now.timestamp() * 0.4)
        glow_radius = int(min(w, h) * (0.34 + pulse))
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*colors.accent, 26), (w // 2, int(h * 0.34)), glow_radius)
        surface.blit(glow, (0, 0))

        line = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 4):
            pygame.draw.line(line, (255, 255, 255, 6), (0, y), (w, y), 1)
        surface.blit(line, (0, 0))

        frame = pygame.Rect(16, 16, w - 32, h - 32)
        pygame.draw.rect(surface, (88, 92, 102), frame, width=1, border_radius=22)

    def _draw_clock(self, surface: pygame.Surface, now: datetime) -> None:
        clock = " ".join(list(now.strftime("%H:%M")))
        day = now.strftime("%A · %d %b %Y").upper()
        clock_label = self._fonts["clock"].render(clock, True, self.config.theme.text_primary)
        day_label = self._fonts["date"].render(day, True, self.config.theme.text_secondary)
        surface.blit(clock_label, clock_label.get_rect(center=(self.config.app.width // 2, 158)))
        surface.blit(day_label, day_label.get_rect(center=(self.config.app.width // 2, 236)))

    def _draw_clock_small(self, surface: pygame.Surface, now: datetime) -> None:
        label = self._fonts["small"].render(now.strftime("%H:%M"), True, self.config.theme.text_secondary)
        surface.blit(label, (34, 28))

    def _draw_face(self, surface: pygame.Surface, req: RequestVisual, now: datetime) -> None:
        cx, cy = self.config.app.width // 2, 250
        eye_offset = 68
        eye_radius = 16

        pygame.draw.circle(surface, (240, 236, 224), (cx - eye_offset, cy), eye_radius)
        pygame.draw.circle(surface, (240, 236, 224), (cx + eye_offset, cy), eye_radius)

        pupil_shift = int(math.sin(now.timestamp() * 0.8) * 3)
        pygame.draw.circle(surface, (42, 42, 48), (cx - eye_offset + pupil_shift, cy), 6)
        pygame.draw.circle(surface, (42, 42, 48), (cx + eye_offset + pupil_shift, cy), 6)

        mouth_w = 64
        mouth_h = 10
        if req.phase == RequestPhase.THINKING:
            mouth_w = 48 + int(8 * math.sin(now.timestamp() * 3.2))
            mouth_h = 6
        elif req.phase == RequestPhase.SPEAKING:
            mouth_h = 10 + int(22 * (0.2 + abs(math.sin(now.timestamp() * 6.0))))
            mouth_w = 70
        else:
            mouth_h = 22
            mouth_w = 76

        mouth = pygame.Rect(cx - mouth_w // 2, cy + 66, mouth_w, mouth_h)
        pygame.draw.rect(surface, (230, 214, 193), mouth, border_radius=8)

        if req.phase == RequestPhase.THINKING:
            dots = "." * ((now.second % 3) + 1)
            text = self._fonts["overlay"].render(f"THINKING{dots}", True, self.config.theme.warning)
            surface.blit(text, text.get_rect(center=(self.config.app.width // 2, 368)))

    def _draw_response_panel(
        self,
        surface: pygame.Surface,
        text: str,
        scroll_px: float,
        bubble_progress: float,
        left_shift: int,
    ) -> None:
        w, h = self.config.app.width, self.config.app.height
        panel_x = int(w - left_shift + 8)
        panel = pygame.Rect(panel_x, 42, w - 54, h - 84)
        pygame.draw.rect(surface, (49, 53, 62), panel, border_radius=18)
        pygame.draw.rect(surface, self.config.theme.accent, panel, width=2, border_radius=18)

        tail_w = int(26 * bubble_progress)
        tail_h = int(24 * bubble_progress)
        if tail_w > 0 and tail_h > 0:
            p1 = (panel.x, 340)
            p2 = (panel.x - tail_w, 340 + tail_h // 2)
            p3 = (panel.x, 340 + tail_h)
            pygame.draw.polygon(surface, (49, 53, 62), (p1, p2, p3))
            pygame.draw.lines(surface, self.config.theme.accent, False, (p1, p2, p3), 2)

        header = self._fonts["title"].render("RESPONSE", True, self.config.theme.text_secondary)
        surface.blit(header, (panel.x + 18, panel.y + 14))

        text_area = pygame.Rect(panel.x + 18, panel.y + 48, panel.width - 36, panel.height - 64)
        clip_prev = surface.get_clip()
        surface.set_clip(text_area)

        wrapped = self._wrap_text(text, text_area.width)
        y = text_area.y - int(scroll_px)
        for line in wrapped:
            line_s = self._fonts["body"].render(line, True, self.config.theme.text_primary)
            surface.blit(line_s, (text_area.x, y))
            y += 34

        surface.set_clip(clip_prev)

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
        pygame.draw.rect(surface, self.config.theme.card_background, rect, border_radius=14)
        pygame.draw.rect(surface, (88, 92, 102), rect, width=1, border_radius=14)
        header = pygame.Rect(x, y, w, 30)
        pygame.draw.rect(surface, (54, 58, 68), header, border_top_left_radius=14, border_top_right_radius=14)

        title_label = self._fonts["title"].render(title, True, self.config.theme.text_secondary)
        body_label = self._fonts["body"].render(self._trim(content, 52), True, self.config.theme.text_primary)
        surface.blit(title_label, (x + 12, y + 7))
        surface.blit(body_label, (x + 14, y + 53))

    def _draw_status(self, surface: pygame.Surface, state: AssistantState) -> None:
        palette = {
            AssistantState.IDLE: (148, 223, 165),
            AssistantState.THINKING: (255, 204, 122),
            AssistantState.SPEAKING: (128, 186, 255),
            AssistantState.OFFLINE: (255, 138, 138),
        }
        status_rect = pygame.Rect(32, 34, 180, 30)
        pygame.draw.rect(surface, (41, 45, 55), status_rect, border_radius=15)
        pygame.draw.rect(surface, (88, 92, 102), status_rect, width=1, border_radius=15)
        pygame.draw.circle(surface, palette[state], (46, 49), 6)
        label = self._fonts["small"].render(state.value.upper(), True, self.config.theme.text_secondary)
        surface.blit(label, (58, 41))

    def _draw_offline_banner(self, surface: pygame.Surface) -> None:
        banner = pygame.Rect(self.config.app.width // 2 - 130, 90, 260, 36)
        pygame.draw.rect(surface, (110, 58, 58), banner, border_radius=10)
        msg = self._fonts["small"].render("OFFLINE · LOCAL MODE", True, (245, 214, 214))
        surface.blit(msg, msg.get_rect(center=banner.center))

    def _draw_custom_card(self, surface: pygame.Surface, card: DisplayCard) -> None:
        card_rect = pygame.Rect(62, self.config.app.height - 176, self.config.app.width - 124, 122)
        pygame.draw.rect(surface, (70, 76, 92), card_rect, border_radius=14)
        pygame.draw.rect(surface, self.config.theme.accent, card_rect, width=2, border_radius=14)
        title = self._fonts["title"].render(card.title.upper(), True, self.config.theme.accent)
        body = self._fonts["body"].render(self._trim(card.body, 55), True, self.config.theme.text_primary)
        surface.blit(title, (card_rect.x + 14, card_rect.y + 14))
        surface.blit(body, (card_rect.x + 14, card_rect.y + 55))

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if self._fonts["body"].size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _trim(content: str, limit: int) -> str:
        if len(content) <= limit:
            return content
        return content[: limit - 1] + "…"
