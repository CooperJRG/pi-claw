from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import AssistantState, DisplayCard
from .providers import AssistantEventProvider


@dataclass
class DisplaySnapshot:
    state: AssistantState
    card: DisplayCard | None


class DisplayStateMachine:
    def __init__(self, events: AssistantEventProvider) -> None:
        self._events = events
        self._active_card: DisplayCard | None = None

    def tick(self, now: datetime) -> DisplaySnapshot:
        if self._active_card and now >= self._active_card.expires_at:
            self._active_card = None

        new_card = self._events.get_card(now)
        if new_card is not None:
            self._active_card = new_card

        state = self._events.get_state(now)
        return DisplaySnapshot(state=state, card=self._active_card)
