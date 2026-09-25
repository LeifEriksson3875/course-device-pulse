from datetime import datetime, timedelta, timezone
from uuid import UUID

from edtech_status.course_delivery import DeliveryState, DeviceStatus, assess_delivery


def test_incomplete_course_at_deadline_requires_educator_attention() -> None:
    deadline = datetime(2026, 9, 6, 9, 0, tzinfo=timezone.utc)
    status = DeviceStatus(
        event_id=UUID("80e4d59d-01a7-4e9e-92c3-da37322097a7"),
        course_id="biology-204",
        learner_id="learner-17",
        device_id="chromebook-17",
        connected=True,
        progress_percent=72,
        observed_at=deadline + timedelta(seconds=1),
        deadline_at=deadline,
    )

    result = assess_delivery(status)

    assert result.state is DeliveryState.ATTENTION_REQUIRED
    assert result.reason == "deadline_reached"


def test_completed_course_stays_on_track_after_deadline() -> None:
    deadline = datetime(2026, 9, 6, 9, 0, tzinfo=timezone.utc)
    status = DeviceStatus(
        event_id=UUID("38a8e184-c581-4460-8a87-108aaad16fe9"),
        course_id="biology-204",
        learner_id="learner-22",
        device_id="tablet-22",
        connected=False,
        progress_percent=100,
        observed_at=deadline + timedelta(hours=3),
        deadline_at=deadline,
    )

    result = assess_delivery(status)

    assert result.state is DeliveryState.ON_TRACK
    assert result.reason == "course_complete"
