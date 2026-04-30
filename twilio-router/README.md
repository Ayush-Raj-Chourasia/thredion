# twilio-router

Standalone central webhook for Twilio.

## Endpoints

- `GET /api/health`
- `GET /api/webhook`
- `POST /api/webhook`

## Purpose

Use this deployment as the single Twilio webhook URL. It can forward messages to multiple backend projects based on route prefix or explicit form fields.

## Environment variables

- `TWILIO_ROUTER_DEFAULT_NAME`
- `TWILIO_ROUTER_DEFAULT_URL`
- `TWILIO_ROUTER_TARGETS_JSON`
- `TWILIO_VALIDATE_SIGNATURE`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WEBHOOK_AUTH_TOKEN`
- `TWILIO_ROUTER_TIMEOUT_MS`
- `TWILIO_ROUTER_FALLBACK_REPLY`

## Example target list

```json
[
  { "name": "thredion", "url": "https://alphacalculus-thredion-api.hf.space/api/whatsapp/webhook", "aliases": ["main", "default"] },
  { "name": "project-b", "url": "https://project-b.example.com/api/webhook" }
]
```

The live router URL is:

- `https://twilio-router.vercel.app/api/webhook`