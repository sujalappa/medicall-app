import type { Insights } from "../lib/types";

interface ClinicalSummaryPanelProps {
  insights: Insights | null;
  isLoading: boolean;
}

export function ClinicalSummaryPanel({ insights, isLoading }: ClinicalSummaryPanelProps) {
  if (isLoading) {
    return (
      <div>
        <h4>Clinical Summary</h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="skeleton" style={{ height: 64, width: "100%" }} />
          <div className="skeleton" style={{ height: 48, width: "80%" }} />
          <div className="skeleton" style={{ height: 48, width: "90%" }} />
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div>
        <h4>Clinical Summary</h4>
        <p style={{ color: "var(--text-tertiary)", fontSize: 14, textAlign: "center", padding: "2rem 0" }}>
          Waiting for analysis to complete...
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <h4>SOAP Note</h4>
      {insights.soap_note && Object.keys(insights.soap_note).length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {insights.soap_note.subjective && (
            <div>
              <strong>Subjective:</strong>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>{insights.soap_note.subjective}</p>
            </div>
          )}
          {insights.soap_note.objective && (
            <div>
              <strong>Objective:</strong>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>{insights.soap_note.objective}</p>
            </div>
          )}
          {insights.soap_note.assessment && (
            <div>
              <strong>Assessment:</strong>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>{insights.soap_note.assessment}</p>
            </div>
          )}
          {insights.soap_note.plan && (
            <div>
              <strong>Plan:</strong>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>{insights.soap_note.plan}</p>
            </div>
          )}
        </div>
      ) : (
        <p style={{ fontSize: 14, color: "var(--text-tertiary)" }}>No SOAP Note available.</p>
      )}

      {insights.symptoms && insights.symptoms.length > 0 && (
        <div>
          <h4>Symptoms</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {insights.symptoms.map((symp, i) => (
              <div
                key={i}
                style={{
                  padding: "0.625rem 0.75rem",
                  background: "var(--danger-subtle)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: 14,
                  borderLeft: "3px solid var(--danger)",
                }}
              >
                {symp.text}
                {symp.duration && <span style={{ marginLeft: 8, fontSize: 12, color: "var(--text-tertiary)" }}>({symp.duration})</span>}
                {symp.severity && <span style={{ marginLeft: 8, fontSize: 12, fontWeight: "bold" }}>- {symp.severity}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {insights.prescriptions && insights.prescriptions.length > 0 && (
        <div>
          <h4>Prescriptions / Orders</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {insights.prescriptions.map((item, i) => (
              <div
                key={i}
                style={{
                  padding: "0.625rem 0.75rem",
                  background: "var(--accent-subtle)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: 14,
                  borderLeft: "3px solid var(--accent)",
                }}
              >
                {item.text}
              </div>
            ))}
          </div>
        </div>
      )}

      {insights.follow_ups && insights.follow_ups.length > 0 && (
        <div>
          <h4>Follow-ups</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {insights.follow_ups.map((item, i) => (
              <div
                key={i}
                style={{
                  padding: "0.625rem 0.75rem",
                  background: "var(--success-subtle)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: 14,
                  borderLeft: "3px solid var(--success)",
                }}
              >
                {item.text}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
