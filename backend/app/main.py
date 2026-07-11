import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import ProcessEmailRequest, ProcessEmailResponse
from app.services.llm import EmailAnalyzer, LLMServiceError
from app.workflow.graph import build_workflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(
    title="Customer Service Workflow API",
    summary="Analyze incoming customer email and prepare a department handoff.",
    description=(
        "This API runs incoming customer messages through a LangGraph workflow. "
        "It classifies the message and returns an internal department-email draft when routing is required."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "System", "description": "Service status and operational checks."},
        {"name": "Email workflow", "description": "Analyze and route incoming customer email."},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"], summary="Check service health")
async def health():
    return {"status": "ok", "openai_configured": bool(settings.openai_api_key)}


@app.post(
    "/api/process-email",
    response_model=ProcessEmailResponse,
    tags=["Email workflow"],
    summary="Process an incoming customer email",
    responses={
        401: {"description": "OpenAI rejected the configured API key."},
        422: {"description": "The submitted email payload is invalid."},
        429: {"description": "OpenAI rate limit reached."},
        502: {"description": "OpenAI could not process the request."},
        503: {"description": "OpenAI is unavailable or not configured."},
    },
)
async def process_email(request: ProcessEmailRequest):
    try:
        workflow = build_workflow(EmailAnalyzer())
        result = await workflow.ainvoke({"email": request.message})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Workflow failed")
        raise HTTPException(status_code=502, detail="Unable to process this email.") from exc

    if "draft" not in result:
        return ProcessEmailResponse(status="not_routed", classification=result["classification"], reason=result.get("reason"))
    return ProcessEmailResponse(status="drafted", classification=result["classification"], route=result["route"], reason=result.get("reason"), email=result["draft"])
