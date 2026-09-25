from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class DeliveryState(str, Enum):
    ON_TRACK = "on_track"
    ATTENTION_REQUIRED = "attention_required"


@dataclass
class DeviceStatus:
    event_id: UUID
    course_id: str
    learner_id: str
    device_id: str
    connected: bool
    progress_percent: int
    observed_at: datetime
    deadline_at: datetime

    def __post_init__(self) -> None:
        for value in (self.course_id, self.learner_id, self.device_id):
            if not 1 <= len(value) <= 80:
                raise ValueError("course, learner, and device IDs must be 1-80 characters")
        if not 0 <= self.progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100")


@dataclass
class DeliveryAssessment:
    state: DeliveryState
    reason: str


def assess_delivery(status: DeviceStatus) -> DeliveryAssessment:
    observed = _utc(status.observed_at)
    deadline = _utc(status.deadline_at)
    if status.progress_percent == 100:
        return DeliveryAssessment(state=DeliveryState.ON_TRACK, reason="course_complete")
    if observed >= deadline:
        return DeliveryAssessment(
            state=DeliveryState.ATTENTION_REQUIRED, reason="deadline_reached"
        )
    if not status.connected:
        return DeliveryAssessment(
            state=DeliveryState.ATTENTION_REQUIRED, reason="device_offline"
        )
    return DeliveryAssessment(state=DeliveryState.ON_TRACK, reason="active_before_deadline")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
