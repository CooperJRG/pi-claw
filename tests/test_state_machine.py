from datetime import datetime, timedelta

from openclaw_display.models import AssistantState, DisplayCard
from openclaw_display.state_machine import DisplayStateMachine


class StubEvents:
    def __init__(self) -> None:
        self.state = AssistantState.IDLE
        self.card = None

    def get_state(self, now: datetime) -> AssistantState:
        return self.state

    def get_card(self, now: datetime):
        return self.card


def test_state_machine_clears_expired_cards() -> None:
    events = StubEvents()
    machine = DisplayStateMachine(events)

    now = datetime.now()
    events.card = DisplayCard(title="t", body="b", expires_at=now + timedelta(seconds=1))

    snapshot = machine.tick(now)
    assert snapshot.card is not None

    events.card = None
    snapshot2 = machine.tick(now + timedelta(seconds=2))
    assert snapshot2.card is None
