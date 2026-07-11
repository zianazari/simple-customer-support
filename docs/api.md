# API

Base URL during local development: `http://localhost:8000`.

## Interactive documentation

FastAPI serves the generated OpenAPI contract and interactive documentation:

| URL | Purpose |
| --- | --- |
| `/docs` | Swagger UI: explore endpoints and submit test requests. |
| `/redoc` | ReDoc: read the reference documentation. |
| `/openapi.json` | Raw OpenAPI 3 document for tools and client generation. |

## CORS

The API accepts cross-origin requests from `CORS_ORIGINS` (default `http://localhost:5173`). The allowed methods are `GET`, `POST`, and `OPTIONS`.

## `GET /health`

Returns application status and whether an OpenAI key was configured. It never returns the key.

```json
{ "status": "ok", "openai_configured": true }
```

## `POST /api/process-email`

Processes one incoming email through the LangGraph workflow.

Request body:

```json
{ "message": "I cannot sign in after resetting my password." }
```

`message` must be non-empty and no longer than 20,000 characters.

Successful routed response:

```json
{
  "status": "drafted",
  "classification": "Support",
  "route": "support-question",
  "reason": "The customer needs help accessing their account.",
  "email": {
    "department": "Technical Support",
    "recipient": "technical-support@example.com",
    "subject": "[Support Question] Incoming customer email",
    "body": "..."
  }
}
```

Spam and Other classifications complete successfully but do not create a handoff:

```json
{ "status": "not_routed", "classification": "Spam", "reason": null, "email": null }
```

### Errors

| Status | Meaning |
| --- | --- |
| `401` | OpenAI rejected the configured API key. |
| `422` | Request body does not meet validation requirements. |
| `429` | OpenAI rate limit was reached. |
| `502` | OpenAI could not process the request or returned an invalid structured result. |
| `503` | No API key is configured, or OpenAI cannot be reached. |

## Contract tests

`backend/tests/test_openapi.py` verifies the generated `/openapi.json` contract, expected operations, a successful routed response, configuration-error behavior, and restricted CORS preflight methods. The tests mock the LangGraph workflow boundary and do not call OpenAI.
