"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { uploadCall } from "../lib/api";

export default function HomePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const data = await uploadCall(file);
      router.push(`/calls/${data.call_id}`);
    } catch {
      setError("Failed to upload call. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith("audio/")) {
      setFile(droppedFile);
      setError("");
    } else {
      setError("Please drop an audio file (.mp3, .wav).");
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const acceptedTypes = ".mp3,.wav,audio/*";

  return (
    <main className="container">
      <div className="animate-fade-in-up" style={{
        maxWidth: 520,
        margin: "4rem auto 0",
        textAlign: "center",
      }}>
        <h1 style={{ fontSize: 32, marginBottom: 8 }}>
          Analyze Your Clinical Calls
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 15, marginBottom: 32 }}>
          Upload an audio file to get real-time transcription, patient sentiment, and clinical insights (SOAP).
        </p>

        <form onSubmit={onSubmit}>
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${isDragOver ? "var(--accent)" : "var(--border)"}`,
              borderRadius: "var(--radius-lg)",
              padding: "2.5rem 1.5rem",
              background: isDragOver ? "var(--accent-subtle)" : "var(--surface)",
              cursor: "pointer",
              transition: "all var(--transition)",
              marginBottom: 20,
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={acceptedTypes}
              onChange={(e) => {
                const selected = e.target.files?.[0] || null;
                setFile(selected);
                setError("");
              }}
              required
              style={{ display: "none" }}
            />

            {file ? (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                <div style={{ fontWeight: 500, fontSize: 14 }}>{file.name}</div>
                <div style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                <div style={{ fontWeight: 500, fontSize: 14 }}>
                  Drop your audio file here, or click to browse
                </div>
                <div style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
                  Supports .mp3 and .wav files
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="error-banner animate-fade-in" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <button className="btn" disabled={loading || !file} type="submit" style={{ width: "100%", padding: "0.75rem 1.25rem" }}>
            {loading ? (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                <span className="animate-spin" style={{
                  display: "inline-block",
                  width: 16,
                  height: 16,
                  border: "2px solid rgba(255,255,255,0.3)",
                  borderTopColor: "white",
                  borderRadius: "50%",
                }} />
                Uploading...
              </span>
            ) : (
              "Upload and Analyze"
            )}
          </button>
        </form>

        <div style={{ marginTop: 16 }}>
          <a href="/calls" className="btn btn-secondary" style={{ width: "100%" }}>
            View Past Calls
          </a>
        </div>
      </div>
    </main>
  );
}
