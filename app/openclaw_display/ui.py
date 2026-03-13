from __future__ import annotations

import math
from datetime import datetime

import pygame

from .config import DisplayConfig
from .face import FaceCardRenderer
from .models import AssistantState, InfoPanel, RequestPhase, RequestVisual, WeatherInfo
from .split_flap import SplitFlapDisplay

# Monospace font families
MONO_FAMILY = "Consolas, Courier New, Lucida Console, monospace"

THINKING_PHRASES = [
    "Thinking\u2026",
    "Considering\u2026",
    "Pondering\u2026",
    "Hmm, let me see\u2026",
    "Analyzing\u2026",
    "Working through this\u2026",
    "One moment\u2026",
    "Pulling it together\u2026",
    "Reflecting\u2026",
    "Let me think\u2026",
]

# Retro window chrome constants
TITLEBAR_H = 24
WIN_BORDER = 2
WIN_CORNER = 3
TITLEBAR_BTN_R = 5


class DisplayRenderer:
    """Composites the full display with retro-computer window chrome."""

    def __init__(self, config: DisplayConfig) -> None:
        self.cfg = config
        self.w = config.app.width
        self.h = config.app.height
        self._fonts: dict[str, pygame.font.Font] = {}
        self._flap: SplitFlapDisplay | None = None
        self._face: FaceCardRenderer | None = None
        self._prev_in_request = False
        self._mouth_cy: int = 0

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self) -> None:
        pygame.font.init()
        theme = self.cfg.theme

        self._fonts["weather"] = pygame.font.SysFont(MONO_FAMILY, 30)
        self._fonts["panel_item"] = pygame.font.SysFont(MONO_FAMILY, 26)
        self._fonts["clock_small"] = pygame.font.SysFont(MONO_FAMILY, 34, bold=True)
        self._fonts["thinking"] = pygame.font.SysFont(MONO_FAMILY, 30)
        self._fonts["resp_body"] = pygame.font.SysFont(MONO_FAMILY, 28)
        self._fonts["resp_prompt"] = pygame.font.SysFont(MONO_FAMILY, 28, bold=True)
        self._fonts["win_title"] = pygame.font.SysFont(MONO_FAMILY, 16, bold=True)

        digit_h = 320
        digit_font = pygame.font.SysFont(MONO_FAMILY, 220, bold=True)

        self._flap = SplitFlapDisplay(
            digit_w=130,
            digit_h=digit_h,
            font=digit_font,
            card_color=theme.flap_bg,
            text_color=theme.flap_text,
            split_color=theme.flap_split,
            gap=10,
            colon_gap=22,
        )

        self._face = FaceCardRenderer(
            card_color=theme.flap_bg,
            iris_color=theme.face_iris,
            eye_white=theme.face_eye,
            pupil_color=theme.face_pupil,
            mouth_color=theme.face_mouth,
            outline_color=tuple(min(255, c + 28) for c in theme.flap_bg),
        )

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    @property
    def _clock_x(self) -> int:
        return (self.w - self._flap.total_width) // 2

    @property
    def _clock_y(self) -> int:
        return 94

    @property
    def _panels_top(self) -> int:
        return self._clock_y + self._flap.digit_h + 60

    def _mouth_screen(self, t: float, slide_px: int = 0) -> tuple[int, int]:
        pos = self._flap.get_positions(self._clock_x - slide_px, t)
        mx = (pos[1] + self._flap.digit_w + pos[2]) // 2
        my = self._clock_y + self._mouth_cy
        return mx, my

    # ------------------------------------------------------------------
    # Retro window chrome
    # ------------------------------------------------------------------

    def _draw_window(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        body_color: tuple[int, int, int],
    ) -> pygame.Rect:
        """Draw a retro-computer window and return the inner content rect."""
        theme = self.cfg.theme

        # Outer border
        pygame.draw.rect(surface, theme.win_border, rect, border_radius=WIN_CORNER)
        inner = rect.inflate(-WIN_BORDER * 2, -WIN_BORDER * 2)

        # Title bar
        tb = pygame.Rect(inner.x, inner.y, inner.width, TITLEBAR_H)
        pygame.draw.rect(surface, theme.win_titlebar, tb)

        # Title bar buttons (left side)
        btn_y = tb.centery
        btn_x = tb.x + 10
        pygame.draw.circle(surface, theme.win_btn_close, (btn_x, btn_y), TITLEBAR_BTN_R)
        btn_x += 16
        pygame.draw.circle(surface, theme.win_btn_dim, (btn_x, btn_y), TITLEBAR_BTN_R)
        btn_x += 16
        pygame.draw.circle(surface, theme.win_btn_dim, (btn_x, btn_y), TITLEBAR_BTN_R)

        # Title text (centered)
        title_surf = self._fonts["win_title"].render(title, True, theme.win_titlebar_text)
        title_rect = title_surf.get_rect(center=tb.center)
        surface.blit(title_surf, title_rect)

        # Body area
        body = pygame.Rect(inner.x, inner.y + TITLEBAR_H, inner.width, inner.height - TITLEBAR_H)
        pygame.draw.rect(surface, body_color, body)

        # Content inset
        return body.inflate(-12, -8)

    # ------------------------------------------------------------------
    # Main draw entry
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
        now: datetime,
        state: AssistantState,
        weather: WeatherInfo | None,
        panels: list[InfoPanel],
        request: RequestVisual | None,
    ) -> None:
        t = now.timestamp()
        theme = self.cfg.theme
        in_request = request is not None

        # Transition edges
        if in_request and not self._prev_in_request:
            self._flap.flip_to_face(t)
        if not in_request and self._prev_in_request:
            self._flap.flip_to_digits(t)
        self._prev_in_request = in_request

        # Keep digit time current
        time_str = now.strftime("%H:%M")
        self._flap.update(time_str, t)

        # Update face cards each frame while face is visible
        if self._flap.is_face_mode and request is not None:
            cards, self._mouth_cy = self._face.render_cards(
                self._flap.digit_w, self._flap.digit_h, request.phase, t,
            )
            self._flap.set_face_cards(cards)

        # Background
        surface.fill(theme.background)

        # --- slide offset for reading/returning ---
        slide_px = 0
        if request is not None and request.phase == RequestPhase.READING:
            slide_px = int(
                _ease_out(min(1.0, request.phase_progress * 5.0)) * self.w
            )
        elif request is not None and request.phase == RequestPhase.RETURNING:
            slide_px = int(
                (1.0 - _ease_out(request.phase_progress)) * self.w
            )

        # Compact time (during request, slides off)
        if in_request:
            tl = self._fonts["clock_small"].render(time_str, True, theme.text_secondary)
            surface.blit(tl, (28 - slide_px, 24))

        # Weather — always visible, right-aligned, never slides
        self._draw_weather(surface, weather)

        # Split-flap display (digits or face cards)
        self._flap.render(
            surface, self._clock_x - slide_px, self._clock_y, t,
            blink_colon=not self._flap.is_face_mode,
        )

        # Thought-bubble trail (speaking / reading / returning)
        if request is not None and request.phase == RequestPhase.SPEAKING:
            progress = min(1.0, request.phase_progress * 2.5)
            mx, my = self._mouth_screen(t)
            self._draw_thought_trail(surface, mx, my, self.w - 16, progress)

        if request is not None and request.phase in (
            RequestPhase.READING, RequestPhase.RETURNING,
        ):
            mx, my = self._mouth_screen(t, slide_px)
            panel_x = self.w - slide_px + 6
            self._draw_thought_trail(surface, mx, my, panel_x - 4, 1.0)

        # Response panel (full-width terminal window)
        if request is not None and request.phase in (
            RequestPhase.READING, RequestPhase.RETURNING,
        ):
            self._draw_response_panel(surface, request, slide_px)

        # Info panels at bottom — two stacked windows, slide off with face
        self._draw_info_panels(surface, panels, slide_px)

        # Thinking phrase — drawn after panels so it's on top
        if request is not None and request.phase == RequestPhase.THINKING:
            phrase = THINKING_PHRASES[int(t / 2.2) % len(THINKING_PHRASES)]
            label = self._fonts["thinking"].render(phrase, True, theme.text_secondary)
            lr = label.get_rect(
                center=(self.w // 2 - slide_px, self._clock_y + self._flap.digit_h + 30),
            )
            surface.blit(label, lr)

        if state == AssistantState.OFFLINE:
            self._draw_offline_indicator(surface)

    # ------------------------------------------------------------------
    # Weather
    # ------------------------------------------------------------------

    def _draw_weather(self, surface: pygame.Surface, weather: WeatherInfo | None) -> None:
        if not weather:
            return
        theme = self.cfg.theme
        font = self._fonts["weather"]
        text = f"{weather.temperature} {weather.condition}"
        text_w, text_h = font.size(text)
        # Account for: border(2)*2 + content inset(6)*2 + small padding
        chrome_w = WIN_BORDER * 2 + 6 * 2 + 12
        chrome_h = WIN_BORDER * 2 + TITLEBAR_H + 4 + 8
        win_w = text_w + chrome_w
        win_h = text_h + chrome_h
        win_rect = pygame.Rect(self.w - win_w - 16, 10, win_w, win_h)
        content = self._draw_window(surface, win_rect, "WEATHER", theme.notif_bg)
        label = font.render(text, True, theme.text_primary)
        surface.blit(label, (content.x, content.y + 2))

    # ------------------------------------------------------------------
    # Info panels (two side-by-side retro windows)
    # ------------------------------------------------------------------

    def _draw_info_panels(
        self,
        surface: pygame.Surface,
        panels: list[InfoPanel],
        slide_px: int,
    ) -> None:
        theme = self.cfg.theme
        margin = 16
        gap = 6
        top = self._panels_top
        bot = self.h - 8
        panel_w = self.w - margin * 2

        # Split vertical space between panels
        count = min(len(panels), 2)
        if count == 0:
            return
        panel_h = (bot - top - gap * (count - 1)) // count

        for i, panel in enumerate(panels[:2]):
            px = margin - slide_px
            py = top + i * (panel_h + gap)
            win_rect = pygame.Rect(px, py, panel_w, panel_h)

            # Skip if fully off-screen
            if px + panel_w < 0:
                continue

            content = self._draw_window(surface, win_rect, panel.title, theme.notif_bg)

            # Items — compact line spacing
            font = self._fonts["panel_item"]
            y = content.y + 2
            for item_text in panel.items:
                if y + 26 > content.bottom:
                    break
                bullet = font.render(">", True, theme.text_secondary)
                surface.blit(bullet, (content.x, y))
                label = font.render(
                    _trim(item_text, 50), True, theme.text_primary,
                )
                surface.blit(label, (content.x + 20, y))
                y += 34

    # ------------------------------------------------------------------
    # Offline indicator
    # ------------------------------------------------------------------

    def _draw_offline_indicator(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, (200, 80, 80), (self.w - 28, 28), 6)

    # ------------------------------------------------------------------
    # Thought-bubble trail
    # ------------------------------------------------------------------

    def _draw_thought_trail(
        self,
        surface: pygame.Surface,
        mouth_x: int,
        mouth_y: int,
        target_x: int,
        progress: float,
    ) -> None:
        if progress < 0.05:
            return
        theme = self.cfg.theme

        count = 6
        for i in range(count):
            t = 0.08 + (i / (count - 1)) * 0.92 if count > 1 else 1.0
            if t > progress:
                break

            bx = int(mouth_x + (target_x - mouth_x) * t)
            arc = -int(14 * math.sin(t * math.pi))
            by = mouth_y + arc

            br = int(3 + t * 10)
            pygame.draw.circle(surface, theme.bubble_bg, (bx, by), br)
            pygame.draw.circle(surface, theme.bubble_border, (bx, by), br, 1)

    # ------------------------------------------------------------------
    # Response panel — full-width terminal window (warm Macintosh tones)
    # ------------------------------------------------------------------

    def _draw_response_panel(
        self,
        surface: pygame.Surface,
        request: RequestVisual,
        slide_px: int,
    ) -> None:
        theme = self.cfg.theme
        margin = 10
        # Full width of the screen, slides in from the right
        panel_x = self.w - slide_px + margin
        panel_y = 10
        panel_w = self.w - margin * 2
        panel_h = self.h - 20

        win_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        content = self._draw_window(surface, win_rect, "OPENCLAW", theme.terminal_bg)

        # Prompt line
        prompt = self._fonts["resp_prompt"].render("$ openclaw >", True, theme.terminal_prompt)
        surface.blit(prompt, (content.x, content.y + 4))

        # Dashed separator
        sep_y = content.y + 28
        dash_len = 6
        gap_len = 4
        x = content.x
        while x < content.right:
            end_x = min(x + dash_len, content.right)
            pygame.draw.line(surface, theme.terminal_dim, (x, sep_y), (end_x, sep_y), 1)
            x += dash_len + gap_len

        # Scrolling response text
        text_area = pygame.Rect(
            content.x, sep_y + 8, content.width, content.height - 36,
        )
        clip_prev = surface.get_clip()
        surface.set_clip(text_area)

        font = self._fonts["resp_body"]
        lines = _wrap_text(request.response_text, text_area.width, font)
        line_h = 38
        total_h = len(lines) * line_h
        max_scroll = max(0, total_h - text_area.height)
        scroll_px = int(request.scroll_progress * max_scroll)

        y = text_area.y - scroll_px
        for line in lines:
            if text_area.y - line_h < y < text_area.bottom + line_h:
                lbl = font.render(line, True, theme.terminal_text)
                surface.blit(lbl, (text_area.x, y))
            y += line_h

        # Blinking block cursor (inline with last text line)
        if lines:
            cursor_y = text_area.y - scroll_px + (len(lines) - 1) * line_h + 2
            cursor_x = text_area.x + font.size(lines[-1])[0] + 3
        else:
            cursor_y = text_area.y + 2
            cursor_x = text_area.x
        if text_area.y <= cursor_y < text_area.bottom:
            if int(pygame.time.get_ticks() / 530) % 2 == 0:
                cursor_h = font.get_height()
                pygame.draw.rect(
                    surface, theme.terminal_text,
                    pygame.Rect(cursor_x, cursor_y, 10, cursor_h),
                )

        surface.set_clip(clip_prev)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _ease_out(t: float) -> float:
    return 1.0 - (1.0 - t) ** 2


def _trim(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def _wrap_text(text: str, max_width: int, font: pygame.font.Font) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
