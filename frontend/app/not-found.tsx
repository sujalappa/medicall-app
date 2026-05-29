import Link from "next/link";

export default function NotFound() {
  return (
    <main className="container">
      <div className="animate-fade-in-up" style={{
        maxWidth: 480,
        margin: "4rem auto 0",
        textAlign: "center",
      }}>
        <div style={{
          fontSize: 72,
          fontWeight: 700,
          color: "var(--text-tertiary)",
          letterSpacing: "-0.04em",
          lineHeight: 1,
          marginBottom: 8,
        }}>
          404
        </div>
        <h1 style={{ marginBottom: 8 }}>Page not found</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 24 }}>
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link href="/" className="btn">
          Go Home
        </Link>
      </div>
    </main>
  );
}
