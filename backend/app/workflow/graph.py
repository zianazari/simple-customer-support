import logging
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.schemas import (
    ProcessFeedbackResult,
    ProcessMessageResult,
    ProcessOtherResult,
    ProcessSupportResult,
    SupportBugResult,
)
from app.services.llm import EmailAnalyzer

logger = logging.getLogger(__name__)

PROCESS_MESSAGE_PROMPT = """You are an expert email-analyzer AI. You are given emails and you give them one of the available labels.
You answer with a json of this structure:
{type: 'Support' | 'Feedback' | 'Spam' | 'Other'}"""
PROCESS_SUPPORT_PROMPT = """You are an expert support request analyser AI.
You are given a support request and you give them one of the available labels.
You answer with a json of this structure: {
  type: 'Bug' | 'TechnicalQuestion',
  reason: string
}"""
PROCESS_FEEDBACK_PROMPT = """You are an expert sentiment analysis AI.
You process feedback a company received and have to decide if it was positive or negative.
You answer with a json of this structure: {
  isPositive: boolean,
  reason: string
}"""
PROCESS_OTHER_PROMPT = """You are an expert email-analyzer AI. You are given emails and you provide a brief summary and the reason for categorizing it as 'Other'.
You answer with a json of this structure: {
  summary: string,
  reason: string
}"""
SUPPORT_BUG_PROMPT = """You are an expert bug report handler AI.
You are given a bug report and decide a severity level and create a detailed description for the support staff.
You answer with a json of this structure: {
  severity: "high" | "medium" | "low",
  description: string,
  reason: string
}"""


class WorkflowState(TypedDict, total=False):
    email: str
    classification: Literal["Support", "Feedback", "Spam", "Other"]
    support: ProcessSupportResult
    feedback: ProcessFeedbackResult
    other: ProcessOtherResult
    bug: SupportBugResult
    route: str
    draft: dict[str, str]
    reason: str


DEPARTMENTS = {
    "feedback-positive": ("Customer Experience", "customer-experience@example.com"),
    "feedback-negative": ("Customer Experience", "customer-experience@example.com"),
    "support-question": ("Technical Support", "technical-support@example.com"),
    "bug-low": ("Support Engineering", "support-engineering@example.com"),
    "bug-medium": ("Support Engineering", "support-engineering@example.com"),
    "bug-high": ("Incident Response", "incident-response@example.com"),
}


def build_workflow(analyzer: EmailAnalyzer):
    async def process_message(state: WorkflowState):
        result = await analyzer.analyze(PROCESS_MESSAGE_PROMPT, state["email"], ProcessMessageResult)
        logger.info("Email classified as %s", result.type)
        return {"classification": result.type}

    async def process_support(state: WorkflowState):
        result = await analyzer.analyze(PROCESS_SUPPORT_PROMPT, state["email"], ProcessSupportResult)
        return {"support": result, "reason": result.reason}

    async def process_feedback(state: WorkflowState):
        result = await analyzer.analyze(PROCESS_FEEDBACK_PROMPT, state["email"], ProcessFeedbackResult)
        return {"feedback": result, "reason": result.reason}

    async def process_other(state: WorkflowState):
        result = await analyzer.analyze(PROCESS_OTHER_PROMPT, state["email"], ProcessOtherResult)
        logger.info("Other email not routed: %s", result.reason)
        return {"other": result, "reason": result.reason}

    async def support_bug(state: WorkflowState):
        result = await analyzer.analyze(SUPPORT_BUG_PROMPT, state["email"], SupportBugResult)
        return {"bug": result, "reason": result.reason}

    def set_route(route: str):
        def node(_: WorkflowState):
            return {"route": route}
        return node

    def draft_email(state: WorkflowState):
        route = state["route"]
        department, recipient = DEPARTMENTS[route]
        subject = f"[{route.replace('-', ' ').title()}] Incoming customer email"
        details = state.get("reason", "No additional analysis was provided.")
        if bug := state.get("bug"):
            details = f"Severity: {bug.severity}\nDescription: {bug.description}\nReason: {bug.reason}"
        body = f"Please review the following customer email:\n\n{state['email']}\n\nAnalysis:\n{details}"
        logger.info("Drafted email for %s", department)
        return {"draft": {"department": department, "recipient": recipient, "subject": subject, "body": body}}

    def message_route(state: WorkflowState):
        return {"Support": "process_support", "Feedback": "process_feedback", "Other": "process_other", "Spam": END}[state["classification"]]

    def support_route(state: WorkflowState):
        return "support_bug" if state["support"].type == "Bug" else "support_question"

    def feedback_route(state: WorkflowState):
        return "feedback_positive" if state["feedback"].isPositive else "feedback_negative"

    def bug_route(state: WorkflowState):
        return f"bug_{state['bug'].severity}"

    graph = StateGraph(WorkflowState)
    graph.add_node("process_message", process_message)
    graph.add_node("process_support", process_support)
    graph.add_node("process_feedback", process_feedback)
    graph.add_node("process_other", process_other)
    graph.add_node("support_bug", support_bug)
    graph.add_node("support_question", set_route("support-question"))
    graph.add_node("feedback_positive", set_route("feedback-positive"))
    graph.add_node("feedback_negative", set_route("feedback-negative"))
    graph.add_node("bug_low", set_route("bug-low"))
    graph.add_node("bug_medium", set_route("bug-medium"))
    graph.add_node("bug_high", set_route("bug-high"))
    graph.add_node("draft_email", draft_email)
    graph.add_edge(START, "process_message")
    graph.add_conditional_edges("process_message", message_route)
    graph.add_conditional_edges("process_support", support_route)
    graph.add_conditional_edges("process_feedback", feedback_route)
    graph.add_edge("process_other", END)
    graph.add_conditional_edges("support_bug", bug_route)
    for node in ("support_question", "feedback_positive", "feedback_negative", "bug_low", "bug_medium", "bug_high"):
        graph.add_edge(node, "draft_email")
    graph.add_edge("draft_email", END)
    return graph.compile()
