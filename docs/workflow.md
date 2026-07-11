# Email Routing Workflow

The application implements this LangGraph workflow. Every route begins with `process-message`, which places the first classification in shared state.

```mermaid
flowchart TD
    Start([Start]) --> PM[process-message]
    PM -->|Support| PS[process-support]
    PM -->|Feedback| PF[process-feedback]
    PM -->|Other| PO[process-other]
    PM -->|Spam| End([End])
    PS -->|Bug| SB[support-bug]
    PS -->|Technical Question| SQ[support-question]
    SB -->|Low| BL[bug-severity-low]
    SB -->|Medium| BM[bug-severity-medium]
    SB -->|High| BH[bug-severity-high]
    PF -->|Positive| FP[feedback-positive]
    PF -->|Negative| FN[feedback-negative]
    SQ --> DE[draft-email]
    BL --> DE
    BM --> DE
    BH --> DE
    FP --> DE
    FN --> DE
    PO --> End
    DE --> End
```

## Outcome rules

| Route | Department |
| --- | --- |
| Positive or negative feedback | Customer Experience |
| Technical question | Technical Support |
| Low or medium bug | Support Engineering |
| High-severity bug | Incident Response |
| Spam or Other | No draft is created |

`process-other` generates a summary and reason for internal analysis, then ends without routing. Spam ends immediately. All other actionable routes arrive at `draft-email`, which creates an internal email draft for the mapped department.
