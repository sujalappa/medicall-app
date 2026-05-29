import Link from "next/link";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: { label: string; href: string };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "3rem 1rem",
      textAlign: "center",
    }}>
      <div style={{
        width: 56,
        height: 56,
        borderRadius: "50%",
        background: "var(--surface-hover)",
        border: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 16,
        color: "var(--text-tertiary)",
      }}>
        {icon}
      </div>
      <h3 style={{ marginBottom: 6, fontSize: 16 }}>{title}</h3>
      <p style={{ color: "var(--text-tertiary)", fontSize: 14, maxWidth: 320, marginBottom: action ? 20 : 0 }}>
        {description}
      </p>
      {action && (
        <Link href={action.href} className="btn">
          {action.label}
        </Link>
      )}
    </div>
  );
}
