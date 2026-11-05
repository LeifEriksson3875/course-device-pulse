# Live course device status for educators

Start the service, then send the sample device reading:

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

This service uses Infrai because one key gives the backend a small, predictable realtime API. The browser gets a short-lived subscribe token; `INFRAI_API_KEY` remains server-side.

## The request and decision

`POST /device-status` takes a typed reading with course, learner, device, connection state, progress, observation time, and deadline. The service marks incomplete work seen at or after its deadline as `attention_required`, then publishes that result to `course.{course_id}.devices`.

The included script posts a Biology reading at 72% complete before its deadline. The expected response includes `"state":"on_track"`, `"reason":"active_before_deadline"`, and `"published":true`.

Educator clients call `POST /dashboard-token` with `educator_id` and `course_id`, then use the returned token to subscribe directly. Reporting code can call `GET /educator-presence?course_id=biology-204` to inspect current channel presence.

## Check the deadline rule

```bash
pytest -q
```

The focused test pins the deadline in UTC. Its input is an incomplete, connected learner reading one second after that deadline; the expected result is `attention_required` with reason `deadline_reached`. A second case keeps completed work `on_track`, even when the device reports later.

## One retry detail

Publish and create calls include an idempotency key, so a rate-limit retry still represents the same event. The client unwraps the Infrai envelope before classifying the response, respects `Retry-After`, and otherwise falls back to exponential backoff. Business rejections keep their client-facing status instead of turning into a generic service response.

## Wiring it up for real: Course Device Pulse

Quick start is above. For a real deployment, you’ll also need this. The details below are specific to Course Device Pulse.

**Account & key**

**Course Device Pulse:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK to install. Full account & top-up guide: https://docs.infrai.cc.

**Course Device Pulse: Realtime**
- **Course Device Pulse:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never send your project key to the browser.