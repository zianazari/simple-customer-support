import { FormEvent, KeyboardEvent, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Result = {
  status: "drafted" | "not_routed";
  classification: string;
  route?: string;
  reason?: string;
  email?: { department: string; recipient: string; subject: string; body: string };
};
type Message = { role: "user" | "assistant"; content: string; result?: Result; time?: number };

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const EXAMPLES = [
  "I can’t log in after resetting my password.",
  "The new dashboard is fantastic—thank you!",
  "Our checkout page returns a 500 error for every customer.",
];

function MarkIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 4.5h16v10L17 19H7l-3-4.5v-10Z" />
      <path d="M4 14.5h5.3a1 1 0 0 1 .9.55L11 17h2l.8-1.95a1 1 0 0 1 .9-.55H20" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function pad(n: number) {
  return String(n).padStart(3, "0");
}

function classSlug(value: string) {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-");
}

function formatTime(ts?: number) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Paste an incoming customer email below. It will be classified, routed to the right queue, and — where a handoff is needed — a draft note will be prepared for that team." },
  ]);
  const [waiting, setWaiting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || waiting) return;
    setMessages((items) => [...items, { role: "user", content: text, time: Date.now() }]);
    setInput("");
    setWaiting(true);
    try {
      const response = await fetch(`${API_URL}/api/process-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const result: Result | { detail?: string } = await response.json();
      if (!response.ok) throw new Error((result as { detail?: string }).detail ?? "Request failed");
      const typed = result as Result;
      const content = typed.status === "drafted"
        ? `Classified as ${typed.classification}. Handoff prepared for ${typed.email?.department}.`
        : `Classified as ${typed.classification}. No department handoff required.`;
      setMessages((items) => [...items, { role: "assistant", content, result: typed, time: Date.now() }]);
    } catch (error) {
      setMessages((items) => [...items, { role: "assistant", content: `Couldn’t process that ticket: ${(error as Error).message}`, time: Date.now() }]);
    } finally {
      setWaiting(false);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  const ticketCount = messages.filter((message) => message.role === "user").length;
  let ticketN = 0;

  return <main className="app-shell">
    <section className="console" aria-label="Customer service email triage console">
      <header className="console-header">
        <div className="brand">
          <span className="brand-mark"><MarkIcon /></span>
          <div className="brand-text">
            <p className="brand-eyebrow">Atlas Operations</p>
            <h1>Inbox Triage</h1>
          </div>
        </div>
        <div className="header-meta">
          <span className="env-tag">PRODUCTION</span>
          <span className="live-tag"><i /> Live</span>
        </div>
      </header>

      <div className="toolbar">
        <div>
          <h2>Ticket queue</h2>
          <p>Paste an incoming customer email to classify, route, and draft the internal handoff.</p>
        </div>
        <div className="queue-count"><strong>{pad(ticketCount)}</strong><span>Processed</span></div>
      </div>

      <div className="thread" aria-live="polite">
        {messages.map((message, index) => {
          if (message.role === "assistant" && index === 0) {
            return <p key={index} className="system-note">{message.content}</p>;
          }

          if (message.role === "user") {
            ticketN += 1;
            return (
              <article key={index} className="ticket-entry">
                <div className="ticket-meta">
                  <span className="ticket-id">TCK-{pad(ticketN)}</span>
                  <span className="ticket-time">{formatTime(message.time)}</span>
                  <span className="ticket-tag-in">Incoming</span>
                </div>
                <div className="ticket-body">{message.content}</div>
              </article>
            );
          }

          return (
            <article key={index} className="routing-entry">
              <p className="routing-summary">{message.content}</p>
              {message.result && <div className="routing-line">
                <strong className={`pill pill-${classSlug(message.result.classification)}`}>{message.result.classification}</strong>
                {message.result.status === "drafted" && <span className="routing-arrow"><ArrowIcon /> {message.result.email?.department}</span>}
              </div>}
              {message.result?.reason && <p className="routing-reason">{message.result.reason}</p>}
              {message.result?.status === "not_routed" && <p className="routing-note">Logged for records — no handoff needed.</p>}
              {message.result?.email && <div className="handoff">
                <div className="handoff-head">
                  <span className="handoff-label">Internal handoff</span>
                  <span className="handoff-dept">{message.result.email.department}</span>
                </div>
                <dl>
                  <div><dt>To</dt><dd>{message.result.email.recipient}</dd></div>
                  <div><dt>Subject</dt><dd>{message.result.email.subject}</dd></div>
                </dl>
                <pre>{message.result.email.body}</pre>
              </div>}
            </article>
          );
        })}
        {waiting && <div className="processing-row"><span className="processing-dots"><i /><i /><i /></span>Classifying and routing…</div>}
      </div>

      {messages.length === 1 && <div className="samples">
        <span className="samples-label">Sample tickets</span>
        <div className="samples-list">
          {EXAMPLES.map((example) => <button key={example} type="button" className="sample-chip" onClick={() => setInput(example)}>{example}</button>)}
        </div>
      </div>}

      <form className="composer" onSubmit={submit}>
        <div className="composer-field">
          <textarea aria-label="Incoming customer email" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleComposerKeyDown} placeholder="Paste an incoming customer email…" rows={3} maxLength={20000} />
          <span className="char-count">{input.length.toLocaleString()} / 20,000</span>
        </div>
        <button className="route-button" disabled={waiting || !input.trim()}>
          <span>{waiting ? "Routing" : "Route email"}</span>
          <ArrowIcon />
        </button>
      </form>
      <p className="hint-row">Press <kbd>Enter</kbd> to route · <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line</p>
    </section>
  </main>;
}

createRoot(document.getElementById("root")!).render(<App />);