from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .course_delivery import DeliveryAssessment, DeviceStatus, assess_delivery
from .infrai_realtime import InfraiError, InfraiRealtime

app = FastAPI(title="Course device status service")


class PublishedStatus(BaseModel):
    channel: str
    assessment: DeliveryAssessment
    published: bool


class DashboardTokenRequest(BaseModel):
    educator_id: str = Field(min_length=1, max_length=80)
    course_id: str = Field(min_length=1, max_length=80)


def realtime_client() -> InfraiRealtime:
    return InfraiRealtime()


def channel_for(course_id: str) -> str:
    return f"course.{course_id}.devices"


@app.post("/device-status", response_model=PublishedStatus)
def record_device_status(
    status: DeviceStatus, client: Annotated[InfraiRealtime, Depends(realtime_client)]
) -> PublishedStatus:
    assessment = assess_delivery(status)
    channel = channel_for(status.course_id)
    data = {
        "course_id": status.course_id,
        "learner_id": status.learner_id,
        "device_id": status.device_id,
        "connected": status.connected,
        "progress_percent": status.progress_percent,
        "observed_at": status.observed_at.isoformat(),
        "deadline_at": status.deadline_at.isoformat(),
        "delivery_state": assessment.state.value,
        "reason": assessment.reason,
    }
    try:
        client.create_channel(channel)
        client.publish_status(channel, data, str(status.event_id))
    except InfraiError as exc:
        raise HTTPException(status_code=_client_status(exc.status_code), detail=exc.detail) from exc
    return PublishedStatus(channel=channel, assessment=assessment, published=True)


@app.post("/dashboard-token")
def dashboard_token(
    request: DashboardTokenRequest,
    client: Annotated[InfraiRealtime, Depends(realtime_client)],
) -> dict[str, Any]:
    channel = channel_for(request.course_id)
    try:
        return client.issue_dashboard_token(request.educator_id, channel)
    except InfraiError as exc:
        raise HTTPException(status_code=_client_status(exc.status_code), detail=exc.detail) from exc


@app.get("/educator-presence")
def educator_presence(
    course_id: Annotated[str, Query(min_length=1, max_length=80)],
    client: Annotated[InfraiRealtime, Depends(realtime_client)],
) -> dict[str, Any]:
    try:
        return client.get_presence(channel_for(course_id))
    except InfraiError as exc:
        raise HTTPException(status_code=_client_status(exc.status_code), detail=exc.detail) from exc


def _client_status(status_code: int) -> int:
    return status_code if 400 <= status_code < 500 else 502
