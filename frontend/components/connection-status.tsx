import type { ConnectionStatus as ConnectionStatusType } from "../lib/types";

interface ConnectionStatusProps {
  status: ConnectionStatusType;
}

const statusConfig: Record<ConnectionStatusType, { label: string; color: string; bgColor: string }> = {
  connected: { label: "Live", color: "#15803d", bgColor: "#22c55e" },
  connecting: { label: "Connecting", color: "#b45309", bgColor: "#f59e0b" },
  reconnecting: { label: "Reconnecting", color: "#b45309", bgColor: "#f59e0b" },
  closed: { label: "Disconnected", color: "#dc2626", bgColor: "#ef4444" },
  completed: { label: "Analysis Complete", color: "#15803d", bgColor: "#22c55e" },
};

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const config = statusConfig[status];

  return (
    <span className="badge" style={{
      background: config.bgColor + "15",
      color: config.color,
      gap: 6,
    }}>
      <span style={{
        display: "inline-block",
        width: 6,
        height: 6,
        borderRadius: "50%",
        background: config.bgColor,
        animation: status === "connecting" || status === "reconnecting" ? "pulse 1.5s ease-in-out infinite" : "none",
      }} />
      {config.label}
    </span>
  );
}
