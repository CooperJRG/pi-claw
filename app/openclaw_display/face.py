from __future__ import annotations

import math

import pygame

from .models import RequestPhase
from .split_flap import CORNER_RADIUS

# Cell size for the blob-pixel grid
CELL = 19
# Heavier overlap so individual cells melt together into one mass
OVERLAP = 11
# Corner radius on each blob cell
BLOB_R = 8


# ------------------------------------------------------------------
# Blob-pixel patterns — each is a set of (col, row) offsets
# ------------------------------------------------------------------

# Eye sclera: a rounded cross / diamond shape (~5 wide, 5 tall)
EYE_SCLERA = {
    # row 0 — narrow top
    (1, 0), (2, 0), (3, 0),
    # row 1
    (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
    # row 2 — widest
    (0, 2), (1, 2), (2, 2), (3, 2), (4, 2),
    # row 3
    (0, 3), (1, 3), (2, 3), (3, 3), (4, 3),
    # row 4 — narrow bottom
    (1, 4), (2, 4), (3, 4),
}

# Pupil: 2x2 blob that drifts within the sclera
PUPIL_SHAPE = {(0, 0), (1, 0), (0, 1), (1, 1)}

# Blink: a thin horizontal bar
EYE_BLINK = {(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}

# ------------------------------------------------------------------
# Mouth shapes — significantly larger patterns
# Centered on col=0, rows grow downward
# ------------------------------------------------------------------

MOUTH_IDLE = {
    (-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    (-4, 1), (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
    (-3, 2), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (3, 2),
    (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3),
}

MOUTH_THINK_WIDE = {
    (-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1),
}
MOUTH_THINK_NARROW = {
    (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0),
    (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),
}

MOUTH_SPEAK_FRAMES = [
    # Frame 0 — open wide
    {
        (-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
        (-5, 1), (-4, 1), (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
        (-4, 2), (-3, 2), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2),
        (-3, 3), (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3), (3, 3),
        (-2, 4), (-1, 4), (0, 4), (1, 4), (2, 4),
    },
    # Frame 1 — open wider
    {
        (-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
        (-5, 1), (-4, 1), (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
        (-5, 2), (-4, 2), (-3, 2), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2),
        (-4, 3), (-3, 3), (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3), (3, 3), (4, 3),
        (-3, 4), (-2, 4), (-1, 4), (0, 4), (1, 4), (2, 4), (3, 4),
        (-2, 5), (-1, 5), (0, 5), (1, 5), (2, 5),
    },
    # Frame 2 — medium
    {
        (-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
        (-4, 1), (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
        (-3, 2), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (3, 2),
        (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3),
    },
]

# Nose hint: two small dots
NOSE_DOTS = {(0, 0), (1, 0)}


class FaceCardRenderer:
    """Renders the OpenClaw face using blob-pixel (merged rounded squares).

    Each facial feature is defined as a set of grid cells. Cells are drawn
    as overlapping rounded rectangles so adjacent blobs merge together like
    slime blocks — retro-modern aesthetic.
    """

    def __init__(
        self,
        card_color: tuple[int, int, int],
        iris_color: tuple[int, int, int],
        eye_white: tuple[int, int, int],
        pupil_color: tuple[int, int, int],
        mouth_color: tuple[int, int, int],
        outline_color: tuple[int, int, int],
    ) -> None:
        self.card = card_color
        self.iris = iris_color
        self.eye_white = eye_white
        self.pupil = pupil_color
        self.mouth = mouth_color
        self.outline = outline_color

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def render_cards(
        self,
        digit_w: int,
        digit_h: int,
        phase: RequestPhase,
        now: float,
    ) -> tuple[list[pygame.Surface], int]:
        """Return (4 card surfaces, mouth_cy relative to card top)."""
        mouth_cy = int(digit_h * 0.72)
        cards = [
            self._eye_card(digit_w, digit_h, False, phase, now),
            self._mouth_half(digit_w, digit_h, False, phase, now, mouth_cy),
            self._mouth_half(digit_w, digit_h, True, phase, now, mouth_cy),
            self._eye_card(digit_w, digit_h, True, phase, now),
        ]
        return cards, mouth_cy

    # ------------------------------------------------------------------
    # Blob drawing
    # ------------------------------------------------------------------

    @staticmethod
    def _draw_blobs(
        surface: pygame.Surface,
        cells: set[tuple[int, int]],
        ox: int,
        oy: int,
        color: tuple[int, int, int],
        cell_size: int = CELL,
        overlap: int = OVERLAP,
        blob_r: int = BLOB_R,
    ) -> None:
        """Draw a merged blob-pixel cluster onto *surface*.

        Each cell in *cells* is a (col, row) offset.  *ox*, *oy* is the
        pixel origin of cell (0, 0).  Cells overlap by *overlap* pixels
        so adjacent blobs melt together.
        """
        step = cell_size - overlap
        for col, row in cells:
            rect = pygame.Rect(
                ox + col * step,
                oy + row * step,
                cell_size,
                cell_size,
            )
            pygame.draw.rect(surface, color, rect, border_radius=blob_r)

    # ------------------------------------------------------------------
    # Card helpers
    # ------------------------------------------------------------------

    def _blank(self, w: int, h: int) -> pygame.Surface:
        card = pygame.Surface((w, h), pygame.SRCALPHA)
        half = h // 2
        pygame.draw.rect(
            card, self.card, pygame.Rect(0, 0, w, half - 1),
            border_top_left_radius=CORNER_RADIUS,
            border_top_right_radius=CORNER_RADIUS,
        )
        pygame.draw.rect(
            card, self.card, pygame.Rect(0, half + 1, w, half - 1),
            border_bottom_left_radius=CORNER_RADIUS,
            border_bottom_right_radius=CORNER_RADIUS,
        )
        return card

    def _split_lines(self, card: pygame.Surface, w: int, h: int) -> None:
        half = h // 2
        hl = tuple(min(255, c + 18) for c in self.card)
        sh = tuple(max(0, c - 12) for c in self.card)
        pygame.draw.line(card, hl, (4, half - 2), (w - 4, half - 2), 1)
        pygame.draw.line(card, sh, (4, half + 2), (w - 4, half + 2), 1)

    # ------------------------------------------------------------------
    # Eye card (blob-pixel style)
    # ------------------------------------------------------------------

    def _eye_card(
        self, w: int, h: int, is_right: bool, phase: RequestPhase, now: float,
    ) -> pygame.Surface:
        card = self._blank(w, h)
        step = CELL - OVERLAP

        # Eye center position on card
        cx = w // 2
        eye_cy = int(h * 0.32)

        # Sclera grid dimensions (5 wide, 5 tall)
        sclera_w = 5 * step + OVERLAP
        sclera_h = 5 * step + OVERLAP
        sx = cx - sclera_w // 2
        sy = eye_cy - sclera_h // 2

        # Blink logic
        period = 2.5 if phase == RequestPhase.THINKING else 4.0
        blink = (now % period) < 0.12

        if blink:
            # Closed — single horizontal bar of blobs
            blink_sy = eye_cy - CELL // 2
            self._draw_blobs(card, EYE_BLINK, sx, blink_sy, self.eye_white)
        else:
            # Sclera
            self._draw_blobs(card, EYE_SCLERA, sx, sy, self.eye_white)

            # Pupil drift — shift the 2x2 block within the sclera
            if phase in (RequestPhase.READING, RequestPhase.RETURNING):
                drift_col = round(math.sin(now * 0.3) * 1.2)
            else:
                drift_col = round(math.sin(now * 0.7) * 0.8)

            look_bias = 1 if not is_right else -1
            pcol = 1 + drift_col + look_bias  # center-ish in the 5-wide grid
            pcol = max(0, min(3, pcol))  # clamp so 2x2 stays in bounds
            prow = 1  # vertically centered-ish

            self._draw_blobs(card, PUPIL_SHAPE, sx + pcol * step, sy + prow * step, self.pupil)

        self._split_lines(card, w, h)
        return card

    # ------------------------------------------------------------------
    # Mouth half-card (blob-pixel style)
    # ------------------------------------------------------------------

    def _mouth_half(
        self,
        w: int,
        h: int,
        is_right: bool,
        phase: RequestPhase,
        now: float,
        mouth_cy: int,
    ) -> pygame.Surface:
        card = self._blank(w, h)
        step = CELL - OVERLAP

        # Pick mouth shape based on phase
        if phase == RequestPhase.THINKING:
            # Pulse between narrow and wide
            mouth = MOUTH_THINK_WIDE if (now % 1.0) < 0.5 else MOUTH_THINK_NARROW
        elif phase == RequestPhase.SPEAKING:
            frame_idx = int(now * 4.5) % len(MOUTH_SPEAK_FRAMES)
            mouth = MOUTH_SPEAK_FRAMES[frame_idx]
        else:
            mouth = MOUTH_IDLE

        # Render full mouth onto a temp surface, then blit the correct half
        # Find bounding box of the mouth pattern
        min_c = min(c for c, r in mouth)
        max_c = max(c for c, r in mouth)
        min_r = min(r for c, r in mouth)
        max_r = max(r for c, r in mouth)

        grid_w = (max_c - min_c + 1) * step + OVERLAP
        grid_h = (max_r - min_r + 1) * step + OVERLAP

        temp = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
        # Shift cells so min_c, min_r maps to (0, 0)
        shifted = {(c - min_c, r - min_r) for c, r in mouth}
        self._draw_blobs(temp, shifted, 0, 0, self.mouth)

        half_w = grid_w // 2
        dy = mouth_cy - grid_h // 2

        if is_right:
            # Right half of mouth → flush against card's left edge
            card.blit(temp, (0, dy), area=pygame.Rect(half_w, 0, grid_w - half_w, grid_h))
        else:
            # Left half of mouth → flush against card's right edge
            card.blit(temp, (w - half_w, dy), area=pygame.Rect(0, 0, half_w, grid_h))

        # Nose hint — two small blob cells near the shared edge
        nose_y = h // 2 + int(h * 0.05)
        if not is_right:
            nose_x = w - CELL - 2
        else:
            nose_x = 2
        self._draw_blobs(card, NOSE_DOTS, nose_x, nose_y, self.outline, cell_size=7, overlap=2, blob_r=3)

        self._split_lines(card, w, h)
        return card
