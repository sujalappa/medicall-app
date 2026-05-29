"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="container">
      <div className="animate-fade-in-up" style={{
        maxWidth: 480,
        margin: "4rem auto 0",
        textAlign: "center",
      }}>
        <div style={{
          width: 56,
          height: 56,
          borderRadius: "50%",
          background: "var(--danger-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 16px",
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        </div>
        <h1 style={{ marginBottom: 8 }}>Something went wrong</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 24 }}>
          An unexpected error occurred. Please try again.
        </p>
        <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
          <button className="btn" onClick={reset}>
            Try Again
          </button>
          <Link href="/" className="btn btn-secondary">
            Go Home
          </Link>
        </div>
      </div>
    </main>
  );
}
