from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from random import Random

from .models import AssistantState, DisplayCard, NowPlayingInfo, ReminderInfo, RequestPhase, RequestVisual, WeatherInfo


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


class RequestFlowProvider(ABC):
    @abstractmethod
    def get_request_visual(self, now: datetime) -> RequestVisual | None:
        raise NotImplementedError


class MockWeatherProvider(WeatherProvider):
    def get_weather(self) -> WeatherInfo:
        return WeatherInfo(summary="Partly Cloudy", temperature_c=21.0, high_c=24.0, low_c=17.0)


class MockNowPlayingProvider(NowPlayingProvider):
    def get_now_playing(self) -> NowPlayingInfo:
        return NowPlayingInfo(title="Here Comes the Sun", artist="The Beatles", source="Mock Spotify")


class MockReminderProvider(ReminderProvider):
    def get_next_reminder(self) -> ReminderInfo:
        due = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1, minutes=15)
        return ReminderInfo(label="Call Sam", due_at=due)


class MockAssistantEventProvider(AssistantEventProvider):
    """Mostly idle status with occasional offline simulation."""

    def __init__(self) -> None:
        self._rng = Random(42)
        self._last_card_minute: int | None = None

    def get_state(self, now: datetime) -> AssistantState:
        if now.minute % 17 == 0 and now.second < 8:
            return AssistantState.OFFLINE
        return AssistantState.IDLE

    def get_card(self, now: datetime) -> DisplayCard | None:
        if now.minute % 5 == 0 and self._last_card_minute != now.minute and self._rng.random() > 0.5:
            self._last_card_minute = now.minute
            return DisplayCard.from_duration(
                title="OpenClaw Update",
                body="Hydration reminder: have a glass of water.",
                duration_sec=20,
            )
        return None


class MockRequestFlowProvider(RequestFlowProvider):
    """Deterministic dummy requests to demo face + response transitions."""

    def __init__(self) -> None:
        self._cycle_sec = 48.0
        self._thinking_sec = 4.0
        self._speaking_sec = 3.0
        self._reading_sec = 14.0
        self._return_sec = 2.0
        self._response = (
            "Good morning! Forecast is mild and partly cloudy. "
            "You have one reminder at 3:15 PM to call Sam. "
            "If you want, I can also show today's headlines next."
        )

    def get_request_visual(self, now: datetime) -> RequestVisual | None:
        t = now.timestamp() % self._cycle_sec
        if t > (self._thinking_sec + self._speaking_sec + self._reading_sec + self._return_sec):
            return None

        if t <= self._thinking_sec:
            return RequestVisual(
                phase=RequestPhase.THINKING,
                response_text=self._response,
                phase_progress=t / self._thinking_sec,
                response_scroll_px=0.0,
            )

        t -= self._thinking_sec
        if t <= self._speaking_sec:
            return RequestVisual(
                phase=RequestPhase.SPEAKING,
                response_text=self._response,
                phase_progress=t / self._speaking_sec,
                response_scroll_px=0.0,
            )

        t -= self._speaking_sec
        if t <= self._reading_sec:
            progress = t / self._reading_sec
            return RequestVisual(
                phase=RequestPhase.READING,
                response_text=self._response,
                phase_progress=progress,
                response_scroll_px=progress * 220.0,
            )

        t -= self._reading_sec
        return RequestVisual(
            phase=RequestPhase.RETURNING,
            response_text=self._response,
            phase_progress=t / self._return_sec,
            response_scroll_px=220.0,
        )
