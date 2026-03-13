from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from random import Random

from .models import AssistantState, DisplayCard, NowPlayingInfo, ReminderInfo, WeatherInfo


class WeatherProvider(ABC):
    @abstractmethod
    def get_weather(self) -> WeatherInfo | None:
        raise NotImplementedError


class NowPlayingProvider(ABC):
    @abstractmethod
    def get_now_playing(self) -> NowPlayingInfo | None:
        raise NotImplementedError


class ReminderProvider(ABC):
    @abstractmethod
    def get_next_reminder(self) -> ReminderInfo | None:
        raise NotImplementedError


class AssistantEventProvider(ABC):
    @abstractmethod
    def get_state(self, now: datetime) -> AssistantState:
        raise NotImplementedError

    @abstractmethod
    def get_card(self, now: datetime) -> DisplayCard | None:
        raise NotImplementedError


class MockWeatherProvider(WeatherProvider):
    def get_weather(self) -> WeatherInfo:
        return WeatherInfo(summary="Partly Cloudy", temperature_c=21.0, high_c=24.0, low_c=17.0)


class MockNowPlayingProvider(NowPlayingProvider):
    def get_now_playing(self) -> NowPlayingInfo:
        return NowPlayingInfo(title="Here Comes the Sun", artist="The Beatles", source="Mock Spotify")


class MockReminderProvider(ReminderProvider):
    def get_next_reminder(self) -> ReminderInfo:
        return ReminderInfo(label="Call Sam", due_at=datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1, minutes=15))


class MockAssistantEventProvider(AssistantEventProvider):
    """Cycle assistant states and occasional cards for local demo reliability."""

    def __init__(self) -> None:
        self._rng = Random(42)
        self._last_card_minute: int | None = None

    def get_state(self, now: datetime) -> AssistantState:
        slot = (now.minute // 1) % 8
        if slot in (1,):
            return AssistantState.THINKING
        if slot in (2,):
            return AssistantState.SPEAKING
        if slot in (6,):
            return AssistantState.OFFLINE
        return AssistantState.IDLE

    def get_card(self, now: datetime) -> DisplayCard | None:
        if now.minute % 5 == 0 and self._last_card_minute != now.minute and self._rng.random() > 0.4:
            self._last_card_minute = now.minute
            return DisplayCard.from_duration(
                title="OpenClaw Update",
                body="Hydration reminder: have a glass of water.",
                duration_sec=25,
            )
        return None
