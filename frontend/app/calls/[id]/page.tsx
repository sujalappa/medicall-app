"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { streamCall, fetchInsights } from "../../../lib/api";
import { useSetConnection } from "../../../components/connection-context";
import { ConnectionStatus } from "../../../components/connection-status";
import { TranscriptViewer } from "../../../components/transcript-viewer";
import { ClinicalSummaryPanel } from "../../../components/clinical-summary-panel";
import { PatientSentimentTimeline } from "../../../components/patient-sentiment-timeline";
import { QAForm } from "../../../components/qa-form";
import type { TranscriptSegment, Insights, ConnectionStatus as ConnectionStatusType } from "../../../lib/types";

export default function CallDashboard() {
  const params = useParams<{ id: string }>();
  const callId = params.id;
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [progress, setProgress] = useState(0);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [connection, setConnection] = useState<ConnectionStatusType>("connecting");
  const [insightsLoading, setInsightsLoading] = useState(false);
  const setGlobalConnection = useSetConnection();

  useEffect(() => {
    if (!callId) return;
    const seqKey = `medicall:lastSeq:${callId}`;
    let ws: WebSocket | null = null;
    let closedByUnmount = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let completed = false;

    const loadInsights = async () => {
      try {
        setInsightsLoading(true);
        const data = await fetchInsights(callId);
        if (data) {
          setInsights(data);
          setProgress(100);
          completed = true;
        }
      } catch {
        // insights not ready yet
      } finally {
        setInsightsLoading(false);
      }
    };

    const connect = (isRetry: boolean) => {
      if (completed) return;
      const sinceSeq = Number(window.localStorage.getItem(seqKey) || "0");
      setConnection(isRetry ? "reconnecting" : "connecting");
      ws = streamCall(
        callId,
        async (event) => {
          if (typeof event.seq === "number") {
            window.localStorage.setItem(seqKey, String(event.seq));
          }
          if (event.type === "status") {
            setProgress(event.progress || 0);
            // If we reconnect and backend says it's already completed
            if (event.status === "completed" && !completed) {
              completed = true;
              await loadInsights();
            }
          }
          if (event.type === "transcript_segment" && event.segment) {
            setProgress(event.progress || 0);
            if (!event.is_partial) {
              setSegments((s) => {
                const last = s[s.length - 1];
                if (
                  last &&
                  last.start_time === event.segment!.start_time &&
                  last.end_time === event.segment!.end_time &&
                  last.text === event.segment!.text
                ) {
                  return s;
                }
                return [...s, event.segment!];
              });
            }
          }
          if (event.type === "completed" && !completed) {
            completed = true;
            await loadInsights();
          }
        },
        sinceSeq
      );

      ws.onopen = () => {
        setConnection("connected");
        setGlobalConnection("connected");
      };
      ws.onclose = () => {
        if (closedByUnmount) {
          setConnection("closed");
          setGlobalConnection("closed");
          return;
        }
        // If we haven't gotten insights yet, try fetching them directly
        // (the backend may have finished while we were disconnected)
        if (!completed) {
          loadInsights().then(() => {
            if (completed) {
              setConnection("closed");
              setGlobalConnection("closed");
              return;
            }
            // Still not done, keep retrying websocket
            setConnection("reconnecting");
            setGlobalConnection("reconnecting");
            retryTimer = setTimeout(() => connect(true), 2000);
          });
        } else {
          setConnection("closed");
          setGlobalConnection("closed");
        }
      };
    };

    connect(false);
    setGlobalConnection("connecting");
    return () => {
      closedByUnmount = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
      setGlobalConnection(null);
    };
  }, [callId, setGlobalConnection]);

  const sentimentChart = useMemo(() => insights?.patient_sentiment || [], [insights]);
  const isProcessing = progress < 100;

  return (
    <main className="container">
        <div className="animate-fade-in-up">
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <h1>Call Analysis</h1>
              <ConnectionStatus status={connection} />
            </div>

            {isProcessing && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Processing call</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)" }}>{progress}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 16,
          }}>
            <section className="card">
              <TranscriptViewer segments={segments} isLoading={isProcessing} />
            </section>

            <section className="card">
              <ClinicalSummaryPanel insights={insights} isLoading={insightsLoading} />
            </section>
          </div>

          <section className="card animate-fade-in" style={{ marginTop: 16 }}>
            <PatientSentimentTimeline data={sentimentChart} />
          </section>

          <section className="card animate-fade-in" style={{ marginTop: 16 }}>
            <QAForm callId={callId} />
          </section>
        </div>
      </main>
    );
  }
