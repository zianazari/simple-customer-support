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
type Message = { role: "user" | "assistant"; content: string; result?: Result };

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const EXAMPLES = [
  "I can’t log in after resetting my password.",
  "The new dashboard is fantastic—thank you!",
  "Our checkout page returns a 500 error for every customer.",
];

function Sparkle() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 2 1.7 6.3L20 10l-6.3 1.7L12 18l-1.7-6.3L4 10l6.3-1.7L12 2Zm7 13 .8 3.2L23 19l-3.2.8L19 23l-.8-3.2L15 19l3.2-.8L19 15Z" /></svg>;
}

function SendIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 3 10.5 13.5M21 3l-6.7 18-3.8-7.5L3 9.7 21 3Z" /></svg>;
}

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! Paste an incoming customer email and I’ll analyze it, route it, and prepare the right internal handoff." },
  ]);
  const [waiting, setWaiting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || waiting) return;
    setMessages((items) => [...items, { role: "user", content: text }]);
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
        ? `I’ve routed this as ${typed.classification}. The handoff draft is ready for ${typed.email?.department}.`
        : `I’ve classified this as ${typed.classification}. It doesn’t need a department handoff.`;
      setMessages((items) => [...items, { role: "assistant", content, result: typed }]);
    } catch (error) {
      setMessages((items) => [...items, { role: "assistant", content: `I couldn’t process that email: ${(error as Error).message}` }]);
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

  return <main className="app-shell">
    <section className="workspace" aria-label="Customer service email assistant">
      <header className="topbar">
        <div className="brand-mark"><Sparkle /></div>
        <div className="title-block"><p className="eyebrow">CUSTOMER OPERATIONS</p><h1>Service Desk</h1></div>
        <div className="online"><span></span> Workflow online</div>
      </header>

      <div className="conversation">
        <div className="conversation-heading">
          <div><h2>Email triage assistant</h2><p>Analyze, prioritize, and route incoming customer messages.</p></div>
          <span className="secure">● Secure processing</span>
        </div>

        <div className="messages" aria-live="polite">
          {messages.map((message, index) => <article key={index} className={`message ${message.role}`}>
            {message.role === "assistant" && <div className="avatar"><Sparkle /></div>}
            <div className="bubble">
              <p>{message.content}</p>
              {message.result && <div className="analysis">
                <div className="analysis-row"><span className="label">Classification</span><strong className={`route ${message.result.classification.toLowerCase()}`}>{message.result.classification}</strong></div>
                {message.result.reason && <p className="reason">{message.result.reason}</p>}
              </div>}
              {message.result?.email && <div className="draft-card">
                <div className="draft-title"><span>✦</span><strong>Department handoff ready</strong></div>
                <dl><div><dt>To</dt><dd>{message.result.email.recipient}</dd></div><div><dt>Subject</dt><dd>{message.result.email.subject}</dd></div></dl>
                <pre>{message.result.email.body}</pre>
              </div>}
            </div>
          </article>)}
          {waiting && <article className="message assistant loading"><div className="avatar"><Sparkle /></div><div className="bubble"><div className="thinking"><i></i><i></i><i></i><span>Analyzing and choosing the right route…</span></div></div></article>}
        </div>

        {messages.length === 1 && <div className="examples"><span>Try an example</span>{EXAMPLES.map((example) => <button key={example} type="button" onClick={() => setInput(example)}>{example}</button>)}</div>}
      </div>

      <form className="composer" onSubmit={submit}>
        <div className="input-wrap"><textarea aria-label="Incoming customer email" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleComposerKeyDown} placeholder="Paste an incoming customer email…" rows={3} maxLength={20000} /><span>{input.length.toLocaleString()} / 20,000</span></div>
        <button className="send-button" disabled={waiting || !input.trim()}><span>{waiting ? "Processing" : "Analyze email"}</span><SendIcon /></button>
      </form>
      <p className="privacy-note">Press <kbd>Enter</kbd> to analyze · <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line</p>
    </section>
  </main>;
}

createRoot(document.getElementById("root")!).render(<App />);
