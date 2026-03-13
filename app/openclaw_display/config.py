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
    card_duration_sec: int = 20


@dataclass
class ThemeConfig:
    background: tuple[int, int, int] = (20, 24, 32)
    card_background: tuple[int, int, int] = (34, 39, 50)
    accent: tuple[int, int, int] = (128, 186, 255)
    text_primary: tuple[int, int, int] = (240, 242, 247)
    text_secondary: tuple[int, int, int] = (160, 171, 191)
    warning: tuple[int, int, int] = (255, 180, 130)


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

    app = AppConfig(
        width=int(app_data.get("width", 720)),
        height=int(app_data.get("height", 720)),
        fps=int(app_data.get("fps", 20)),
        fullscreen=bool(app_data.get("fullscreen", False)),
        title=str(app_data.get("title", "OpenClaw Smart Display")),
        card_duration_sec=int(app_data.get("card_duration_sec", 20)),
    )

    theme = ThemeConfig(
        background=_tuple_color(theme_data.get("background"), (20, 24, 32)),
        card_background=_tuple_color(theme_data.get("card_background"), (34, 39, 50)),
        accent=_tuple_color(theme_data.get("accent"), (128, 186, 255)),
        text_primary=_tuple_color(theme_data.get("text_primary"), (240, 242, 247)),
        text_secondary=_tuple_color(theme_data.get("text_secondary"), (160, 171, 191)),
        warning=_tuple_color(theme_data.get("warning"), (255, 180, 130)),
    )

    return DisplayConfig(app=app, theme=theme)
