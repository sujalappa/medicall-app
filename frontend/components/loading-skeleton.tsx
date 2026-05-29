interface LoadingSkeletonProps {
  variant?: "text" | "card" | "list" | "chart";
  count?: number;
}

export function LoadingSkeleton({ variant = "text", count = 1 }: LoadingSkeletonProps) {
  if (variant === "text") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="skeleton"
            style={{
              height: 16,
              width: i === count - 1 ? "60%" : "100%",
            }}
          />
        ))}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="card" style={{ padding: 20 }}>
            <div className="skeleton" style={{ height: 20, width: "40%", marginBottom: 12 }} />
            <div className="skeleton" style={{ height: 14, width: "100%", marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 14, width: "75%" }} />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "list") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "0.75rem 1rem",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <div className="skeleton" style={{ height: 14, width: 14, borderRadius: "50%", flexShrink: 0 }} />
            <div className="skeleton" style={{ height: 14, width: "50%" }} />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "chart") {
    return (
      <div className="card" style={{ height: 260 }}>
        <div className="skeleton" style={{ height: 16, width: "30%", marginBottom: 16 }} />
        <div className="skeleton" style={{ height: "70%", width: "100%" }} />
      </div>
    );
  }

  return null;
}
