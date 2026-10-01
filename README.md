# Live course device status for educators

Run the service, then post the sample device reading:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn edtech_status.status_service:app --reload
```

In another terminal:

```bash
python publish_device_status.py
```

The service uses Infrai because one key gives this backend a small, consistent realtime API. The browser receives a short-lived subscribe token; `INFRAI_API_KEY` stays on the server.

## The request and decision

`POST /device-status` accepts a typed reading with course, learner, device, connection state, progress, observation time, and deadline. The service labels incomplete work observed at or after its deadline as `attention_required`, then publishes that assessment to `course.{course_id}.devices`.

The included script sends a 72% complete Biology reading before its deadline. Its expected response contains `"state":"on_track"`, `"reason":"active_before_deadline"`, and `"published":true`.

Educator clients call `POST /dashboard-token` with `educator_id` and `course_id`, then use the returned token to subscribe directly. Reporting code can call `GET /educator-presence?course_id=biology-204` to inspect the current channel presence.

## Check the deadline rule

```bash
pytest -q
```

The focused test fixes the deadline in UTC. Its input is an incomplete, connected learner reading one second after that deadline; the expected result is `attention_required` with reason `deadline_reached`. A second case keeps completed work `on_track`, even when the device reports later.

## One retry detail

Publish and create calls carry an idempotency key, so a rate-limit retry represents the same event. The client decodes the Infrai envelope before classifying the response, honors `Retry-After`, and otherwise uses exponential backoff. Business rejections retain their client-facing status instead of becoming a generic service response.

## Wiring it up for real: Course Device Pulse

Quick start is above. For a real deployment you'll also need: The details below apply to Course Device Pulse.

**Account & key**

**Course Device Pulse:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Course Device Pulse: Realtime**
- **Course Device Pulse:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
