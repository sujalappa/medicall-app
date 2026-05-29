"use client";

import { useState } from "react";
import { askQuestion } from "../lib/api";

interface QAFormProps {
  callId: string;
}

export function QAForm({ callId }: QAFormProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setAnswer("");
    try {
      const out = await askQuestion(callId, question);
      setAnswer(out.answer);
    } catch {
      setError("Failed to get an answer. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h4>Ask About This Call</h4>
      <form onSubmit={onAsk} style={{ display: "flex", gap: 8 }}>
        <input
          className="input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="When did the customer mention pricing?"
          disabled={loading}
        />
        <button className="btn" disabled={loading || !question.trim()} type="submit">
          {loading ? (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <span className="animate-spin" style={{
                display: "inline-block",
                width: 14,
                height: 14,
                border: "2px solid rgba(255,255,255,0.3)",
                borderTopColor: "white",
                borderRadius: "50%",
              }} />
              Thinking...
            </span>
          ) : "Ask"}
        </button>
      </form>

      {error && (
        <div className="error-banner" style={{ marginTop: 12 }}>
          {error}
        </div>
      )}

      {answer && (
        <div className="animate-fade-in" style={{
          marginTop: 12,
          padding: "0.875rem 1rem",
          background: "var(--surface-hover)",
          borderRadius: "var(--radius-md)",
          fontSize: 14,
          lineHeight: 1.7,
          color: "var(--text-secondary)",
          borderLeft: "3px solid var(--accent)",
        }}>
          {answer}
        </div>
      )}
    </div>
  );
}
