import Link from "next/link";
import { fetchCalls } from "../../lib/api";
import { EmptyState } from "../../components/empty-state";

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function CallsPage() {
  let calls: Call[] = [];
  try {
    calls = await fetchCalls();
  } catch {
    calls = [];
  }

  return (
    <main className="container">
      <div className="animate-fade-in-up">
        <div style={{ marginBottom: 24 }}>
          <h1>Past Calls</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, marginTop: 4 }}>
            {calls.length === 0 ? "No calls analyzed yet" : `${calls.length} call${calls.length > 1 ? "s" : ""} analyzed`}
          </p>
        </div>

        {calls.length === 0 ? (
          <div className="card">
            <EmptyState
              icon={
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              }
              title="No calls yet"
              description="Upload your first sales call to get started with real-time analysis."
              action={{ label: "Upload a Call", href: "/" }}
            />
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {calls.map((c, i) => (
              <Link
                key={c.id}
                href={`/calls/${c.id}`}
                className="animate-fade-in"
                style={{
                  animationDelay: `${i * 50}ms`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "1rem 1.25rem",
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-md)",
                  transition: "all var(--transition)",
                  textDecoration: "none",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0, flex: 1 }}>
                  <div style={{
                    width: 36,
                    height: 36,
                    borderRadius: "var(--radius-sm)",
                    background: "var(--accent-subtle)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    </svg>
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 500, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.filename}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-tertiary)", marginTop: 2 }}>
                      {formatDate(c.created_at)}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                  <span className="badge badge-neutral">{c.language}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
