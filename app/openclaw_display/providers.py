from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .models import InfoPanel, Notification, RequestPhase, RequestVisual, WeatherInfo


class WeatherProvider(ABC):
    @abstractmethod
    def get_weather(self) -> WeatherInfo | None:
        raise NotImplementedError


class NotificationProvider(ABC):
    @abstractmethod
    def get_notifications(self) -> list[Notification]:
        raise NotImplementedError


class InfoPanelProvider(ABC):
    @abstractmethod
    def get_panels(self) -> list[InfoPanel]:
        raise NotImplementedError


class RequestFlowProvider(ABC):
    @abstractmethod
    def get_request_visual(self, now: datetime) -> RequestVisual | None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mock implementations for demo / offline mode
# ---------------------------------------------------------------------------


class MockWeatherProvider(WeatherProvider):
    def get_weather(self) -> WeatherInfo:
        return WeatherInfo(temperature="21\u00b0", condition="Partly Cloudy")


class MockNotificationProvider(NotificationProvider):
    _sets: list[list[Notification]] = [
        [
            Notification("Bitcoin rallies past $100k as markets surge"),
            Notification("Call Sam at 3:15 PM"),
        ],
        [
            Notification("Partly cloudy skies expected through the weekend"),
            Notification("Grocery pickup ready at 5:00 PM"),
        ],
    ]

    def get_notifications(self) -> list[Notification]:
        idx = (datetime.now().minute // 3) % len(self._sets)
        return self._sets[idx]


class MockInfoPanelProvider(InfoPanelProvider):
    def get_panels(self) -> list[InfoPanel]:
        idx = (datetime.now().minute // 3) % 2
        if idx == 0:
            return [
                InfoPanel(
                    title="NEWS",
                    items=[
                        "Bitcoin rallies past $100k",
                        "Markets close up 1.2%",
                        "Partly cloudy weekend ahead",
                    ],
                ),
                InfoPanel(
                    title="REMINDERS",
                    items=[
                        "Call Sam at 3:15 PM",
                        "Grocery pickup at 5:00 PM",
                    ],
                ),
            ]
        return [
            InfoPanel(
                title="NEWS",
                items=[
                    "Tech earnings beat estimates",
                    "Local transit delays expected",
                ],
            ),
            InfoPanel(
                title="REMINDERS",
                items=[
                    "Dentist appt tomorrow 9 AM",
                    "Submit expense report by EOD",
                    "Water the plants",
                ],
            ),
        ]


class MockRequestFlowProvider(RequestFlowProvider):
    """Cycles through a dummy request flow every ~45 seconds."""

    def __init__(self) -> None:
        self._cycle = 45.0
        self._idle = 24.0
        self._think = 4.0
        self._speak = 3.0
        self._read = 12.0
        self._ret = 2.0
        self._response = (
            "Good morning! Today\u2019s forecast is mild at 21 degrees "
            "with partly cloudy skies. You have one reminder: call "
            "Sam at 3:15 PM. Headlines are quiet today \u2014 markets "
            "are up slightly and no severe weather alerts in your area. "
            "Would you like me to set a reminder for anything else?"
        )

    def get_request_visual(self, now: datetime) -> RequestVisual | None:
        t = now.timestamp() % self._cycle
        if t < self._idle:
            return None

        t -= self._idle

        if t < self._think:
            return RequestVisual(
                phase=RequestPhase.THINKING,
                response_text=self._response,
                phase_progress=t / self._think,
                scroll_progress=0.0,
            )
        t -= self._think

        if t < self._speak:
            return RequestVisual(
                phase=RequestPhase.SPEAKING,
                response_text=self._response,
                phase_progress=t / self._speak,
                scroll_progress=0.0,
            )
        t -= self._speak

        if t < self._read:
            p = t / self._read
            return RequestVisual(
                phase=RequestPhase.READING,
                response_text=self._response,
                phase_progress=p,
                scroll_progress=p,
            )
        t -= self._read

        return RequestVisual(
            phase=RequestPhase.RETURNING,
            response_text=self._response,
            phase_progress=min(t / self._ret, 1.0),
            scroll_progress=1.0,
        )
