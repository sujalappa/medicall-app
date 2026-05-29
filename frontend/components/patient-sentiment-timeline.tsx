import type { SentimentPoint } from "../lib/types";

interface PatientSentimentTimelineProps {
  data: SentimentPoint[];
}

export function PatientSentimentTimeline({ data }: PatientSentimentTimelineProps) {
  if (!data || data.length === 0) {
    return (
      <div>
        <h4>Patient Sentiment Timeline</h4>
        <p style={{ color: "var(--text-tertiary)", fontSize: 14 }}>Waiting for timeline data...</p>
      </div>
    );
  }

  // Find min and max timestamps to normalize X axis
  const minT = Math.min(...data.map((d) => d.timestamp));
  const maxT = Math.max(...data.map((d) => d.timestamp));
  const range = maxT - minT || 1;

  return (
    <div>
      <h4>Patient Sentiment Timeline</h4>
      <div style={{ position: "relative", height: 160, marginTop: 20 }}>
        {/* Y-axis labels */}
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, display: "flex", flexDirection: "column", justifyContent: "space-between", fontSize: 11, color: "var(--text-tertiary)" }}>
          <span>Positive / Relieved</span>
          <span>Neutral</span>
          <span>Negative / Distressed</span>
        </div>

        {/* Chart area */}
        <div style={{ position: "absolute", left: 110, right: 0, top: 0, bottom: 0, borderLeft: "1px solid var(--border)", borderBottom: "1px solid var(--border)" }}>
          {/* Zero line */}
          <div style={{ position: "absolute", left: 0, right: 0, top: "50%", borderTop: "1px dashed var(--border)" }} />
          
          {data.map((point, i) => {
            const xPercent = ((point.timestamp - minT) / range) * 100;
            // score ranges from -1 to +1.
            // +1 is top (0%), -1 is bottom (100%), 0 is middle (50%)
            const yPercent = 50 - (point.score * 50);

            // Determine color based on speaker
            const color = point.speaker === "Physician" ? "var(--accent)" : 
                          point.score < 0 ? "var(--danger)" : "var(--success)";

            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: `${xPercent}%`,
                  top: `${yPercent}%`,
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: color,
                  transform: "translate(-50%, -50%)",
                  boxShadow: "0 0 0 2px var(--surface)",
                }}
                title={`[${point.timestamp}s] ${point.speaker}: ${point.label} (${point.score.toFixed(2)})`}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
