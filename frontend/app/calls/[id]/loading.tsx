import { LoadingSkeleton } from "../../../components/loading-skeleton";

export default function DashboardLoading() {
  return (
    <main className="container">
      <div style={{ marginBottom: 24 }}>
        <div className="skeleton" style={{ height: 28, width: 180, marginBottom: 8 }} />
        <div className="skeleton" style={{ height: 6, width: "100%", borderRadius: 9999 }} />
      </div>
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 16,
      }}>
        <div className="card" style={{ minHeight: 320 }}>
          <div className="skeleton" style={{ height: 16, width: "30%", marginBottom: 16 }} />
          <LoadingSkeleton variant="text" count={4} />
        </div>
        <div className="card" style={{ minHeight: 320 }}>
          <div className="skeleton" style={{ height: 16, width: "30%", marginBottom: 16 }} />
          <LoadingSkeleton variant="text" count={3} />
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <LoadingSkeleton variant="chart" />
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <div className="skeleton" style={{ height: 16, width: "30%", marginBottom: 12 }} />
        <div className="skeleton" style={{ height: 40, width: "100%" }} />
      </div>
    </main>
  );
}
