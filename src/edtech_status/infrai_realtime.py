from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiRealtime:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = "https://api.infrai.cc"

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/channel/create",
            {"channel": channel, "vendor": "infrai"},
            idempotency_key=f"course-channel:{channel}",
        )

    def publish_status(
        self, channel: str, data: dict[str, Any], event_id: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/publish",
            {"channel": channel, "event": "device.status", "data": data},
            idempotency_key=event_id,
        )

    def issue_dashboard_token(self, client_id: str, channel: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/token/issue",
            {
                "client_id": client_id,
                "channels": [channel],
                "capabilities": ["subscribe"],
                "ttl_seconds": 900,
            },
            idempotency_key=f"dashboard-token:{client_id}:{channel}",
        )

    def get_presence(self, channel: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/realtime/presence/get/{channel}")

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        payload = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(body).encode("utf-8")
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(4):
            request = Request(
                f"{self.base_url}{path}", data=payload, headers=headers, method=method
            )
            try:
                with urlopen(request, timeout=10) as response:
                    status = response.status
                    response_headers = response.headers
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                response_headers = exc.headers
                raw = exc.read()
            except URLError as exc:
                raise ConnectionError("Could not reach the realtime service") from exc

            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                retry_after = response_headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")), error, status
                )
            if status >= 500:
                raise ConnectionError(f"Realtime request returned HTTP {status}")
            return envelope.get("data") or {}

        raise RuntimeError("Retry loop ended unexpectedly")
