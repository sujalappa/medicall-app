const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

import type { Call, Insights, QAResponse, StreamEvent } from "./types";

export async function uploadCall(file: File): Promise<{ call_id: string }> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API}/calls/upload`, { method: "POST", body });
  if (!res.ok) {
    throw new Error("Upload failed");
  }
  return res.json();
}

export async function fetchCalls(): Promise<Call[]> {
  const res = await fetch(`${API}/calls`, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchInsights(callId: string): Promise<Insights | null> {
  const res = await fetch(`${API}/calls/${callId}/insights`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function askQuestion(callId: string, question: string): Promise<QAResponse> {
  const res = await fetch(`${API}/calls/${callId}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Q&A failed");
  return res.json();
}

export function streamCall(callId: string, onEvent: (event: StreamEvent) => void, sinceSeq = 0): WebSocket {
  const wsBase = API.replace("http://", "ws://").replace("https://", "wss://");
  const ws = new WebSocket(`${wsBase}/calls/${callId}/stream?since_seq=${sinceSeq}`);
  ws.onmessage = (e) => onEvent(JSON.parse(e.data));
  return ws;
}
