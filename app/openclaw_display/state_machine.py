from __future__ import annotations

from datetime import datetime

from .models import AssistantState, RequestPhase, RequestVisual
from .providers import RequestFlowProvider


class DisplayStateMachine:
    def __init__(self, request_flow: RequestFlowProvider) -> None:
        self._request_flow = request_flow

    def tick(self, now: datetime) -> tuple[AssistantState, RequestVisual | None]:
        visual = self._request_flow.get_request_visual(now)
        if visual is None:
            return AssistantState.IDLE, None
        if visual.phase == RequestPhase.THINKING:
            return AssistantState.THINKING, visual
        return AssistantState.SPEAKING, visual
