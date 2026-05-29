import { useRef, useEffect } from "react";
import type { TranscriptSegment } from "../lib/types";

interface TranscriptViewerProps {
  segments: TranscriptSegment[];
  isLoading?: boolean;
}

const speakerColors = [
  { bg: "#f0f9ff", text: "#0369a1", border: "#bae6fd" },
  { bg: "#fdf4ff", text: "#a21caf", border: "#e9d5ff" },
  { bg: "#f0fdf4", text: "#15803d", border: "#bbf7d0" },
  { bg: "#fff7ed", text: "#c2410c", border: "#fed7aa" },
];

function getSpeakerStyle(speaker: string) {
  let hash = 0;
  for (let i = 0; i < speaker.length; i++) {
    hash = speaker.charCodeAt(i) + ((hash << 5) - hash);
  }
  return speakerColors[Math.abs(hash) % speakerColors.length];
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function TranscriptViewer({ segments, isLoading }: TranscriptViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [segments]);

  return (
    <div>
      <h4>Live Transcript</h4>
      <div
        ref={containerRef}
        style={{
          maxHeight: 480,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 8,
          paddingRight: 4,
        }}
      >
        {segments.length === 0 && !isLoading && (
          <p style={{ color: "var(--text-tertiary)", fontSize: 14, textAlign: "center", padding: "2rem 0" }}>
            Waiting for transcript...
          </p>
        )}
        {segments.map((segment, i) => {
          const style = getSpeakerStyle(segment.speaker);
          return (
            <div
              key={i}
              className="animate-fade-in"
              style={{
                display: "flex",
                gap: 10,
                alignItems: "flex-start",
                padding: "0.625rem 0.75rem",
                background: "var(--surface-hover)",
                borderRadius: "var(--radius-md)",
                fontSize: 14,
                lineHeight: 1.6,
              }}
            >
              <span style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                padding: "0.15rem 0.5rem",
                background: style.bg,
                color: style.text,
                border: `1px solid ${style.border}`,
                borderRadius: 9999,
                fontSize: 11,
                fontWeight: 600,
                whiteSpace: "nowrap",
                flexShrink: 0,
              }}>
                {segment.speaker}
              </span>
              <span style={{ color: "var(--text-tertiary)", fontSize: 11, flexShrink: 0, paddingTop: 2 }}>
                {formatTime(segment.start_time)}
              </span>
              <span style={{ color: "var(--text-primary)" }}>{segment.text}</span>
            </div>
          );
        })}
        {isLoading && (
          <div style={{ display: "flex", gap: 8, alignItems: "center", padding: "0.5rem 0" }}>
            <span className="animate-pulse" style={{ fontSize: 14, color: "var(--text-tertiary)" }}>
              Transcribing...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
