from typing import Literal

from pydantic import BaseModel, Field


class ProcessMessageResult(BaseModel):
    type: Literal["Support", "Feedback", "Spam", "Other"]


class ProcessSupportResult(BaseModel):
    type: Literal["Bug", "TechnicalQuestion"]
    reason: str


class ProcessFeedbackResult(BaseModel):
    isPositive: bool
    reason: str


class ProcessOtherResult(BaseModel):
    summary: str
    reason: str


class SupportBugResult(BaseModel):
    severity: Literal["high", "medium", "low"]
    description: str
    reason: str


class ProcessEmailRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)


class EmailDraft(BaseModel):
    department: str
    recipient: str
    subject: str
    body: str


class ProcessEmailResponse(BaseModel):
    status: Literal["drafted", "not_routed"]
    classification: str
    route: str | None = None
    reason: str | None = None
    email: EmailDraft | None = None
