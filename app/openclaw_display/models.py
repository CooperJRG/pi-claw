from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssistantState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    SPEAKING = "speaking"
    OFFLINE = "offline"


class RequestPhase(str, Enum):
    THINKING = "thinking"
    SPEAKING = "speaking"
    READING = "reading"
    RETURNING = "returning"


@dataclass
class WeatherInfo:
    temperature: str
    condition: str


@dataclass
class Notification:
    text: str


@dataclass
class InfoPanel:
    """A titled panel of items shown at the bottom of the display."""
    title: str
    items: list[str]


@dataclass
class RequestVisual:
    phase: RequestPhase
    response_text: str
    phase_progress: float
    scroll_progress: float
