from datetime import datetime

from openclaw_display.models import RequestPhase
from openclaw_display.providers import MockRequestFlowProvider


def test_request_flow_cycles_through_expected_phases() -> None:
    provider = MockRequestFlowProvider()
    base = datetime.fromtimestamp(0)

    thinking = provider.get_request_visual(base)
    assert thinking is not None
    assert thinking.phase == RequestPhase.THINKING

    speaking = provider.get_request_visual(datetime.fromtimestamp(5))
    assert speaking is not None
    assert speaking.phase == RequestPhase.SPEAKING

    reading = provider.get_request_visual(datetime.fromtimestamp(10))
    assert reading is not None
    assert reading.phase == RequestPhase.READING
    assert reading.response_scroll_px > 0

    returning = provider.get_request_visual(datetime.fromtimestamp(22))
    assert returning is not None
    assert returning.phase == RequestPhase.RETURNING

    idle = provider.get_request_visual(datetime.fromtimestamp(30))
    assert idle is None
