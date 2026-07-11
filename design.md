# Product Design

## Goal

Turn an incoming customer email into a consistent internal handoff. The system analyzes the message with an OpenAI model, follows the routing rules in [docs/workflow.md](docs/workflow.md), and displays the outcome in a chat-style web interface.

## Technology

| Area | Choice |
| --- | --- |
| Backend | Python, FastAPI, Pydantic |
| Workflow and state | LangGraph |
| Model | OpenAI `gpt-4o-mini` by default |
| Frontend | React, TypeScript, Vite |
| Observability | Python standard logging |

## Model tasks

Every model node receives the original email as a human message and returns a structured Pydantic result.

| Node | Output |
| --- | --- |
| `process_message` | `Support`, `Feedback`, `Spam`, or `Other` |
| `process_support` | `Bug` or `TechnicalQuestion`, plus a reason |
| `process_feedback` | Positive/negative sentiment, plus a reason |
| `process_other` | Summary and reason; no handoff is drafted |
| `support_bug` | `high`, `medium`, or `low` severity, description, and reason |

## User experience

The interface is a responsive dark chat workspace. It offers sample messages, an animated analysis state, classification and reasoning details, and a formatted internal-handoff draft. The composer supports `Enter` to send and `Shift + Enter` for a newline.

## Delivery boundary

The final workflow node drafts an email addressed to the mapped department. It does not send email. A production deployment should replace example recipients and add an approved mail provider after the draft node.
