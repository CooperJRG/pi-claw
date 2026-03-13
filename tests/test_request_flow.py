from datetime import datetime, timedelta

from openclaw_display.models import RequestPhase
from openclaw_display.providers import MockRequestFlowProvider


def _at(seconds: float) -> datetime:
    """Return a datetime whose timestamp mod cycle lands at the right phase."""
    # Use a base time that's safe on all platforms
    base = datetime(2025, 1, 1)
    return base + timedelta(seconds=seconds)


def test_request_flow_cycles_through_expected_phases() -> None:
    provider = MockRequestFlowProvider()

    # The mock cycle is 45s: 24s idle, 4s thinking, 3s speaking, 12s reading, 2s returning.
    # We need timestamps where (ts % 45) falls in each phase range.
    base_ts = _at(0).timestamp()
    # Find offset to align with a cycle boundary
    offset = provider._cycle - (base_ts % provider._cycle)

    def at_phase(secs_into_cycle: float) -> datetime:
        return _at(offset + secs_into_cycle)

    # Idle phase: 0 - 24s
    idle = provider.get_request_visual(at_phase(10.0))
    assert idle is None

    # Thinking phase: 24 - 28s
    thinking = provider.get_request_visual(at_phase(25.0))
    assert thinking is not None
    assert thinking.phase == RequestPhase.THINKING

    # Speaking phase: 28 - 31s
    speaking = provider.get_request_visual(at_phase(29.0))
    assert speaking is not None
    assert speaking.phase == RequestPhase.SPEAKING

    # Reading phase: 31 - 43s
    reading = provider.get_request_visual(at_phase(36.0))
    assert reading is not None
    assert reading.phase == RequestPhase.READING
    assert reading.scroll_progress > 0

    # Returning phase: 43 - 45s
    returning = provider.get_request_visual(at_phase(43.5))
    assert returning is not None
    assert returning.phase == RequestPhase.RETURNING
