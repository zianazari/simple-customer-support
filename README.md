# Customer Service Workflow

A web-based email-triage application that classifies customer messages, routes actionable work to the appropriate department, and prepares an internal handoff email. It combines a Python/FastAPI backend, LangGraph workflow, OpenAI structured outputs, and a TypeScript/React chat interface.

## Features

- Routes Support, Feedback, Spam, and Other messages through a LangGraph state machine.
- Classifies support messages as bugs or technical questions; bugs receive a severity level.
- Evaluates feedback sentiment and creates department-specific draft emails for routed work.
- Uses Pydantic schemas and strict JSON-schema model responses for reliable workflow decisions.
- Provides structured application logging and safe, actionable API error messages.
- Includes a dark, responsive chat interface with animated processing feedback, example messages, and message/draft cards.
- Sends a message with `Enter`; use `Shift + Enter` to add a new line.

The service prepares drafts only—it does not send external email. See [the workflow](docs/workflow.md), [architecture](docs/architecture.md), and [API reference](docs/api.md).

## Interactive API documentation

With the backend running, open [Swagger UI](http://localhost:8000/docs) to explore and send requests, or [ReDoc](http://localhost:8000/redoc) for a reference-style view. The raw OpenAPI document is available at `http://localhost:8000/openapi.json`.

## API at a glance

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns service status and API-key configuration state. |
| `POST` | `/api/process-email` | Runs an email through the LangGraph routing workflow. |

Cross-origin requests are restricted to configured origins and the `GET`, `POST`, and `OPTIONS` methods. See the full [API reference](docs/api.md) for request and response examples.

## Run locally

Prerequisites: Python 3.11+ and Node.js 20+.

1. Create your local configuration file and add your OpenAI API key:

   ```bash
   cp .env.example .env
   ```

2. Run the backend:

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

3. In another terminal, run the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Open the Vite URL, normally `http://localhost:5173`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | Required OpenAI API key. Keep it only in local `.env`. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model used by the workflow nodes. |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated browser origins allowed to call the API. |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL used by the frontend. |

Restart the backend after changing `.env`. Application logs are written to standard output. Replace the example department email addresses in `backend/app/workflow/graph.py` before deploying.

## Project structure

```text
backend/
  app/              FastAPI app, configuration, schemas, LLM adapter, LangGraph workflow
  tests/            OpenAPI and API contract tests
  requirements.txt  Runtime dependencies
frontend/
  src/              TypeScript React chat interface and styling
docs/               Workflow, architecture, and API documentation
```

## Verification

```bash
cd backend && .venv/bin/python -m compileall -q app
cd ../frontend && npm run build
```

## API contract tests

The backend includes OpenAPI contract tests in `backend/tests/test_openapi.py`. They mock the workflow boundary, so they never call OpenAI or require a real API key.

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```
