from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    width: int = 720
    height: int = 720
    fps: int = 20
    fullscreen: bool = False
    title: str = "OpenClaw Smart Display"


@dataclass
class ThemeConfig:
    # Macintosh-inspired warm palette
    background: tuple[int, int, int] = (241, 237, 228)
    flap_bg: tuple[int, int, int] = (38, 36, 33)
    flap_text: tuple[int, int, int] = (245, 241, 232)
    flap_split: tuple[int, int, int] = (58, 55, 50)
    text_primary: tuple[int, int, int] = (42, 40, 36)
    text_secondary: tuple[int, int, int] = (130, 126, 118)
    border: tuple[int, int, int] = (200, 196, 188)
    notif_bg: tuple[int, int, int] = (228, 224, 216)
    face_iris: tuple[int, int, int] = (78, 92, 108)
    face_eye: tuple[int, int, int] = (232, 228, 220)
    face_pupil: tuple[int, int, int] = (22, 24, 28)
    face_mouth: tuple[int, int, int] = (210, 198, 182)
    bubble_bg: tuple[int, int, int] = (250, 248, 242)
    bubble_border: tuple[int, int, int] = (180, 176, 168)
    # Retro window chrome
    win_titlebar: tuple[int, int, int] = (42, 40, 36)
    win_titlebar_text: tuple[int, int, int] = (232, 228, 220)
    win_border: tuple[int, int, int] = (62, 58, 52)
    win_btn_close: tuple[int, int, int] = (180, 80, 70)
    win_btn_dim: tuple[int, int, int] = (120, 116, 108)
    # Terminal panel (warm Macintosh / E-Ink tones)
    terminal_bg: tuple[int, int, int] = (250, 248, 242)
    terminal_text: tuple[int, int, int] = (42, 40, 36)
    terminal_prompt: tuple[int, int, int] = (100, 96, 88)
    terminal_dim: tuple[int, int, int] = (170, 166, 158)


@dataclass
class DisplayConfig:
    app: AppConfig = field(default_factory=AppConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)


def _tuple_color(value: Any, default: tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, list) and len(value) == 3:
        return tuple(int(v) for v in value)
    return default


def load_config(path: str | Path | None = None) -> DisplayConfig:
    if path is None:
        return DisplayConfig()

    config_path = Path(path)
    if not config_path.exists():
        return DisplayConfig()

    data = yaml.safe_load(config_path.read_text()) or {}
    app_data = data.get("app", {})
    theme_data = data.get("theme", {})

    defaults = DisplayConfig()
    app = AppConfig(
        width=int(app_data.get("width", defaults.app.width)),
        height=int(app_data.get("height", defaults.app.height)),
        fps=int(app_data.get("fps", defaults.app.fps)),
        fullscreen=bool(app_data.get("fullscreen", defaults.app.fullscreen)),
        title=str(app_data.get("title", defaults.app.title)),
    )

    theme = ThemeConfig()
    for name in ThemeConfig.__dataclass_fields__:
        if name in theme_data:
            setattr(theme, name, _tuple_color(theme_data[name], getattr(theme, name)))

    return DisplayConfig(app=app, theme=theme)
