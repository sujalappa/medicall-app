import { LoadingSkeleton } from "../../components/loading-skeleton";

export default function CallsLoading() {
  return (
    <main className="container">
      <div style={{ marginBottom: 24 }}>
        <div className="skeleton" style={{ height: 28, width: 140, marginBottom: 8 }} />
        <div className="skeleton" style={{ height: 16, width: 100 }} />
      </div>
      <LoadingSkeleton variant="list" count={5} />
    </main>
  );
}
