from datetime import datetime

from openclaw_display.models import AssistantState, RequestPhase, RequestVisual
from openclaw_display.providers import RequestFlowProvider
from openclaw_display.state_machine import DisplayStateMachine


class StubRequestFlow(RequestFlowProvider):
    def __init__(self) -> None:
        self.visual: RequestVisual | None = None

    def get_request_visual(self, now: datetime) -> RequestVisual | None:
        return self.visual


def test_idle_when_no_request() -> None:
    stub = StubRequestFlow()
    machine = DisplayStateMachine(stub)
    state, visual = machine.tick(datetime.now())
    assert state == AssistantState.IDLE
    assert visual is None


def test_thinking_state() -> None:
    stub = StubRequestFlow()
    stub.visual = RequestVisual(
        phase=RequestPhase.THINKING,
        response_text="hello",
        phase_progress=0.5,
        scroll_progress=0.0,
    )
    machine = DisplayStateMachine(stub)
    state, visual = machine.tick(datetime.now())
    assert state == AssistantState.THINKING
    assert visual is not None


def test_speaking_state_for_non_thinking_phases() -> None:
    stub = StubRequestFlow()
    for phase in (RequestPhase.SPEAKING, RequestPhase.READING, RequestPhase.RETURNING):
        stub.visual = RequestVisual(
            phase=phase,
            response_text="hello",
            phase_progress=0.5,
            scroll_progress=0.0,
        )
        machine = DisplayStateMachine(stub)
        state, _ = machine.tick(datetime.now())
        assert state == AssistantState.SPEAKING, f"Expected SPEAKING for {phase}"
