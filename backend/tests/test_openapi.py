"""Contract tests for the public FastAPI/OpenAPI surface."""

from fastapi.testclient import TestClient

from app import main


def client() -> TestClient:
    return TestClient(main.app)


def test_openapi_exposes_health_and_email_processing_contract() -> None:
    """The generated OpenAPI document exposes the two public API operations."""
    specification = client().get("/openapi.json").json()

    assert specification["info"]["title"] == "Customer Service Workflow API"
    assert specification["info"]["version"] == "1.0.0"
    assert {tag["name"] for tag in specification["tags"]} == {"System", "Email workflow"}
    assert set(specification["paths"]) >= {"/health", "/api/process-email"}
    assert "get" in specification["paths"]["/health"]
    process_operation = specification["paths"]["/api/process-email"]["post"]
    assert process_operation["requestBody"]["required"] is True
    assert "200" in process_operation["responses"]
    assert process_operation["tags"] == ["Email workflow"]


def test_swagger_and_redoc_documentation_are_available() -> None:
    """Interactive Swagger UI and ReDoc are exposed by the application."""
    swagger = client().get("/docs")
    redoc = client().get("/redoc")

    assert swagger.status_code == 200
    assert "swagger-ui" in swagger.text
    assert redoc.status_code == 200
    assert "redoc" in redoc.text.lower()


def test_process_email_returns_a_draft_from_a_workflow(monkeypatch) -> None:
    """A routed workflow result preserves the documented response contract."""
    class FakeAnalyzer:
        pass

    class FakeWorkflow:
        async def ainvoke(self, state):
            assert state == {"email": "Login is broken"}
            return {
                "classification": "Support",
                "route": "bug-high",
                "reason": "The issue affects all users.",
                "draft": {
                    "department": "Incident Response",
                    "recipient": "incident-response@example.com",
                    "subject": "[Bug High] Incoming customer email",
                    "body": "Please investigate.",
                },
            }

    monkeypatch.setattr(main, "EmailAnalyzer", FakeAnalyzer)
    monkeypatch.setattr(main, "build_workflow", lambda _: FakeWorkflow())

    response = client().post("/api/process-email", json={"message": "Login is broken"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "drafted",
        "classification": "Support",
        "route": "bug-high",
        "reason": "The issue affects all users.",
        "email": {
            "department": "Incident Response",
            "recipient": "incident-response@example.com",
            "subject": "[Bug High] Incoming customer email",
            "body": "Please investigate.",
        },
    }


def test_process_email_reports_configuration_errors(monkeypatch) -> None:
    """Missing API credentials are returned as a safe, actionable 503 response."""
    def missing_credentials():
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    monkeypatch.setattr(main, "EmailAnalyzer", missing_credentials)
    response = client().post("/api/process-email", json={"message": "Need help"})

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENAI_API_KEY is not configured."


def test_cors_preflight_allows_only_documented_methods() -> None:
    """CORS preflight advertises the restricted GET, POST, OPTIONS method set."""
    response = client().options(
        "/api/process-email",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    allowed = {method.strip() for method in response.headers["access-control-allow-methods"].split(",")}
    assert allowed == {"GET", "POST", "OPTIONS"}
