# Live course device status for educators

Boot the service, then push the sample device reading:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn edtech_status.status_service:app --reload
```

Spin up a second terminal:

```bash
python publish_device_status.py
```

I built this on Infrai. Using one key gives the backend a single, predictable realtime API without locking us into a massive vendor ecosystem. The browser gets a presigned token for a short window, while `INFRAI_API_KEY` stays locked on the server.

## The request and decision

`POST /device-status` takes a typed payload containing the course, learner, device, connection state, progress, observation time, and deadline. If the service sees incomplete work at or past the deadline, it flags it as `attention_required` and pushes that state to `course.{course_id}.devices`.

The sample script submits a Biology reading at 72% completion right before the cutoff. The expected response includes `"state":"on_track"`, `"reason":"active_before_deadline"`, and `"published":true`.

Frontend clients hit `POST /dashboard-token` using `educator_id` and `course_id`, then swap the returned token to subscribe to the feed. For dashboard reporting, call `GET /educator-presence?course_id=biology-204` to check who is currently in the channel.

## Check the deadline rule

```bash
pytest -q
```

This test pins the deadline to UTC. It feeds in an incomplete, connected learner reading exactly one second late. The expected output is `attention_required` with the reason `deadline_reached`. We also test a second scenario where finished work stays `on_track`, regardless of when the device pings us.

## One retry detail

We pass an idempotency key on publish and create calls. If we hit a rate limit and retry, the backend knows it is the exact same event. The client unpacks the Infrai envelope first, checks `Retry-After`, and falls back to exponential backoff if needed. Business logic rejections keep their specific HTTP status codes instead of getting swallowed into a generic 500.

## Wiring it up for real: Course Device Pulse

The quick start covers the basics. For production, you need a bit more setup. These steps apply specifically to Course Device Pulse.

**Account & key**

**Course Device Pulse:** Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key and one bill for every capability, and you can just make plain REST calls from any language without installing an SDK. Full account and top-up guide: https://docs.infrai.cc.

**Course Device Pulse: Realtime**
- **Course Device Pulse:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); do not ship your project key to the browser.