from __future__ import annotations

import math

import pygame

CORNER_RADIUS = 10


class SplitFlapDisplay:
    """Renders a split-flap style clock with flip animations.

    Supports flipping each digit card to an arbitrary "face card" surface
    and smoothly closing the colon gap so the face cards sit together.
    """

    DIGIT_FLIP_SEC = 0.28
    FACE_FLIP_SEC = 0.35
    FACE_STAGGER_SEC = 0.07
    SLIDE_SEC = 0.50  # gap-close duration

    def __init__(
        self,
        digit_w: int,
        digit_h: int,
        font: pygame.font.Font,
        card_color: tuple[int, int, int],
        text_color: tuple[int, int, int],
        split_color: tuple[int, int, int],
        gap: int = 10,
        colon_gap: int = 28,
    ) -> None:
        self.digit_w = digit_w
        self.digit_h = digit_h
        self.font = font
        self.card_color = card_color
        self.text_color = text_color
        self.split_color = split_color
        self.gap = gap
        self.colon_gap = colon_gap

        # Digit state
        self._digits = ["", "", "", ""]
        self._prev = ["", "", "", ""]
        self._flip_start = [0.0] * 4
        self._digit_cache: dict[str, tuple[pygame.Surface, pygame.Surface]] = {}

        # Face-card state
        self._face_cards: list[tuple[pygame.Surface, pygame.Surface]] = []
        self._showing_face = [False, False, False, False]
        self._face_flip_start = [0.0] * 4
        self._face_flip_dir = [0, 0, 0, 0]

        # Gap-slide state
        self._slide_start: float = 0.0
        self._slide_dir: int = 0  # 1 = closing, -1 = opening

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def total_width(self) -> int:
        return self.digit_w * 4 + self.gap * 2 + self.colon_gap * 2

    @property
    def face_width(self) -> int:
        """Width when colon gap is fully closed (uniform gaps)."""
        return self.digit_w * 4 + self.gap * 3

    @property
    def is_face_mode(self) -> bool:
        return (
            any(self._showing_face)
            or any(d != 0 for d in self._face_flip_dir)
        )

    # ------------------------------------------------------------------
    # Pre-render helpers (digit cards, cached)
    # ------------------------------------------------------------------

    def _get_halves(self, char: str) -> tuple[pygame.Surface, pygame.Surface]:
        if char in self._digit_cache:
            return self._digit_cache[char]

        w, h = self.digit_w, self.digit_h
        half = h // 2

        full = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(
            full, self.card_color, pygame.Rect(0, 0, w, half - 1),
            border_top_left_radius=CORNER_RADIUS,
            border_top_right_radius=CORNER_RADIUS,
        )
        pygame.draw.rect(
            full, self.card_color, pygame.Rect(0, half + 1, w, half - 1),
            border_bottom_left_radius=CORNER_RADIUS,
            border_bottom_right_radius=CORNER_RADIUS,
        )

        highlight = tuple(min(255, c + 18) for c in self.card_color)
        shadow = tuple(max(0, c - 12) for c in self.card_color)
        pygame.draw.line(full, highlight, (4, half - 2), (w - 4, half - 2), 1)
        pygame.draw.line(full, shadow, (4, half + 2), (w - 4, half + 2), 1)

        if char:
            text_surf = self.font.render(char, True, self.text_color)
            # Crop to the actual glyph bounding box (trim transparent edges)
            bbox = text_surf.get_bounding_rect()
            if bbox.width > 0 and bbox.height > 0:
                text_surf = text_surf.subsurface(bbox).copy()
            pad = 6
            target_w = w - pad * 2
            target_h = h - pad * 2
            tw, th = text_surf.get_size()
            # Scale to 75% of card height, keep aspect ratio
            scale = (target_h * 0.75) / th
            sw = min(int(tw * scale), target_w)
            sh = int(th * scale)
            text_surf = pygame.transform.smoothscale(text_surf, (sw, sh))
            tx = (w - sw) // 2
            ty = (h - sh) // 2
            full.blit(text_surf, (tx, ty))

        top = full.subsurface(pygame.Rect(0, 0, w, half)).copy()
        bot = full.subsurface(pygame.Rect(0, half, w, half)).copy()
        self._digit_cache[char] = (top, bot)
        return top, bot

    # ------------------------------------------------------------------
    # Public API — digit updates
    # ------------------------------------------------------------------

    def update(self, time_str: str, now: float) -> None:
        digits = [time_str[0], time_str[1], time_str[3], time_str[4]]
        for i in range(4):
            if digits[i] != self._digits[i]:
                self._prev[i] = self._digits[i]
                self._digits[i] = digits[i]
                self._flip_start[i] = now

    # ------------------------------------------------------------------
    # Public API — face card transitions
    # ------------------------------------------------------------------

    def set_face_cards(self, cards: list[pygame.Surface]) -> None:
        self._face_cards = []
        half = self.digit_h // 2
        for card in cards:
            top = card.subsurface(pygame.Rect(0, 0, self.digit_w, half)).copy()
            bot = card.subsurface(pygame.Rect(0, half, self.digit_w, half)).copy()
            self._face_cards.append((top, bot))

    def flip_to_face(self, now: float) -> None:
        for i in range(4):
            self._face_flip_start[i] = now + i * self.FACE_STAGGER_SEC
            self._face_flip_dir[i] = 1
        self._slide_start = now
        self._slide_dir = 1

    def flip_to_digits(self, now: float) -> None:
        for i in range(4):
            self._face_flip_start[i] = now + (3 - i) * self.FACE_STAGGER_SEC
            self._face_flip_dir[i] = -1
        self._slide_start = now
        self._slide_dir = -1

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------

    def _digit_positions(self, x: int) -> list[int]:
        positions: list[int] = []
        cx = x
        for i in range(4):
            positions.append(cx)
            if i == 1:
                cx += self.digit_w + self.colon_gap * 2
            else:
                cx += self.digit_w + self.gap
        return positions

    def _face_positions(self, x: int) -> list[int]:
        """Positions with uniform gap (colon gap removed)."""
        digit_center = x + self.total_width // 2
        fx = digit_center - self.face_width // 2
        return [fx + i * (self.digit_w + self.gap) for i in range(4)]

    def _slide_progress(self, now: float) -> float:
        if self._slide_start == 0.0:
            return 1.0 if all(self._showing_face) else 0.0
        elapsed = now - self._slide_start
        raw = min(1.0, elapsed / self.SLIDE_SEC)
        eased = 1.0 - (1.0 - raw) ** 2
        if self._slide_dir == -1:
            return 1.0 - eased
        return eased

    def get_positions(self, x: int, now: float) -> list[int]:
        """Current interpolated card positions (for external mouth calc)."""
        slide = self._slide_progress(now)
        if slide < 0.001:
            return self._digit_positions(x)
        if slide > 0.999:
            return self._face_positions(x)
        dp = self._digit_positions(x)
        fp = self._face_positions(x)
        return [int(d + (f - d) * slide) for d, f in zip(dp, fp)]

    # ------------------------------------------------------------------
    # Main render
    # ------------------------------------------------------------------

    def render(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        now: float,
        blink_colon: bool = True,
    ) -> None:
        positions = self.get_positions(x, now)

        for i in range(4):
            self._render_one(surface, positions[i], y, i, now)

        # Colon — fade as slide progresses
        slide = self._slide_progress(now)
        if slide < 0.3 and not any(self._showing_face):
            self._draw_colon(surface, positions, y, now, blink_colon)

    # ------------------------------------------------------------------
    # Per-digit render dispatch
    # ------------------------------------------------------------------

    def _render_one(
        self, surface: pygame.Surface, x: int, y: int, idx: int, now: float,
    ) -> None:
        if self._face_flip_dir[idx] != 0 and self._face_cards:
            elapsed = now - self._face_flip_start[idx]
            if elapsed < 0:
                self._draw_current(surface, x, y, idx, now)
            elif elapsed < self.FACE_FLIP_SEC:
                self._draw_face_flip(surface, x, y, idx, elapsed)
            else:
                self._showing_face[idx] = (self._face_flip_dir[idx] == 1)
                self._face_flip_dir[idx] = 0
                self._draw_current(surface, x, y, idx, now)
            return

        self._draw_current(surface, x, y, idx, now)

    def _draw_current(
        self, surface: pygame.Surface, x: int, y: int, idx: int, now: float,
    ) -> None:
        if self._showing_face[idx] and self._face_cards:
            self._draw_card_pair(surface, x, y, self._face_cards[idx])
        else:
            elapsed = now - self._flip_start[idx]
            if self._prev[idx] and elapsed < self.DIGIT_FLIP_SEC:
                self._draw_digit_flip(surface, x, y, idx, elapsed)
            else:
                self._draw_static(surface, x, y, self._digits[idx])

    # ------------------------------------------------------------------
    # Drawing primitives
    # ------------------------------------------------------------------

    def _draw_static(self, surface: pygame.Surface, x: int, y: int, char: str) -> None:
        if not char:
            return
        top, bottom = self._get_halves(char)
        half = self.digit_h // 2
        surface.blit(top, (x, y))
        surface.blit(bottom, (x, y + half))

    def _draw_card_pair(
        self, surface: pygame.Surface, x: int, y: int,
        pair: tuple[pygame.Surface, pygame.Surface],
    ) -> None:
        top, bottom = pair
        half = self.digit_h // 2
        surface.blit(top, (x, y))
        surface.blit(bottom, (x, y + half))

    def _draw_colon(
        self, surface: pygame.Surface, positions: list[int],
        y: int, now: float, blink: bool,
    ) -> None:
        colon_x = positions[1] + self.digit_w + (positions[2] - positions[1] - self.digit_w) // 2
        show = not blink or int(now * 2) % 2 == 0
        if show:
            dot_r = max(4, self.digit_w // 22)
            cy_top = y + self.digit_h // 2 - self.digit_h // 7
            cy_bot = y + self.digit_h // 2 + self.digit_h // 7
            pygame.draw.circle(surface, self.card_color, (colon_x, cy_top), dot_r)
            pygame.draw.circle(surface, self.card_color, (colon_x, cy_bot), dot_r)

    # ------------------------------------------------------------------
    # Flip animations
    # ------------------------------------------------------------------

    def _draw_digit_flip(
        self, surface: pygame.Surface, x: int, y: int, idx: int, elapsed: float,
    ) -> None:
        self._animate_flip(
            surface, x, y,
            self._get_halves(self._prev[idx]),
            self._get_halves(self._digits[idx]),
            elapsed, self.DIGIT_FLIP_SEC,
        )

    def _draw_face_flip(
        self, surface: pygame.Surface, x: int, y: int, idx: int, elapsed: float,
    ) -> None:
        if self._face_flip_dir[idx] == 1:
            old = self._get_halves(self._digits[idx])
            new = self._face_cards[idx]
        else:
            old = self._face_cards[idx]
            new = self._get_halves(self._digits[idx])
        self._animate_flip(surface, x, y, old, new, elapsed, self.FACE_FLIP_SEC)

    def _animate_flip(
        self,
        surface: pygame.Surface,
        x: int, y: int,
        old_pair: tuple[pygame.Surface, pygame.Surface],
        new_pair: tuple[pygame.Surface, pygame.Surface],
        elapsed: float,
        duration: float,
    ) -> None:
        progress = min(1.0, elapsed / duration)
        half = self.digit_h // 2
        hinge_y = y + half
        angle = math.pi * progress

        old_top, old_bottom = old_pair
        new_top, new_bottom = new_pair

        surface.blit(new_top, (x, y))
        surface.blit(old_bottom, (x, hinge_y))

        sy = max(0.01, abs(math.cos(angle)))
        h = max(1, int(half * sy))
        if progress < 0.5:
            flap = pygame.transform.scale(old_top, (self.digit_w, h))
            surface.blit(flap, (x, hinge_y - h))
        else:
            flap = pygame.transform.scale(new_bottom, (self.digit_w, h))
            surface.blit(flap, (x, hinge_y))
