from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from uuid import uuid4


def main() -> None:
    now = datetime.now(timezone.utc)
    body = {
        "event_id": str(uuid4()),
        "course_id": "biology-204",
        "learner_id": "learner-17",
        "device_id": "chromebook-17",
        "connected": True,
        "progress_percent": 72,
        "observed_at": now.isoformat(),
        "deadline_at": (now + timedelta(days=2)).isoformat(),
    }
    service_url = os.environ.get("STATUS_SERVICE_URL", "http://127.0.0.1:8000")
    request = Request(
        f"{service_url}/device-status",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        print(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
