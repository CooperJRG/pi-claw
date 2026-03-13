from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
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
    summary: str
    temperature_c: float
    high_c: float
    low_c: float


@dataclass
class NowPlayingInfo:
    title: str
    artist: str
    source: str


@dataclass
class ReminderInfo:
    label: str
    due_at: datetime


@dataclass
class DisplayCard:
    title: str
    body: str
    expires_at: datetime

    @classmethod
    def from_duration(cls, title: str, body: str, duration_sec: int) -> "DisplayCard":
        return cls(title=title, body=body, expires_at=datetime.now() + timedelta(seconds=duration_sec))


@dataclass
class RequestVisual:
    phase: RequestPhase
    response_text: str
    phase_progress: float
    response_scroll_px: float
