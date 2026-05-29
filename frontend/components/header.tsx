"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ConnectionStatus } from "./connection-status";
import { useConnection } from "./connection-context";

export function Header() {
  const pathname = usePathname();
  const { status } = useConnection();

  const isActive = (path: string) => {
    if (path === "/" && pathname === "/") return true;
    if (path !== "/" && pathname?.startsWith(path)) return true;
    return false;
  };

  return (
    <header style={{
      position: "sticky",
      top: 0,
      zIndex: 50,
      background: "rgba(255, 255, 255, 0.85)",
      backdropFilter: "blur(12px)",
      borderBottom: "1px solid var(--border)",
    }}>
      <div style={{
        maxWidth: 1120,
        margin: "0 auto",
        padding: "0 1.5rem",
        height: 56,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <Link href="/" style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontWeight: 700,
          fontSize: 18,
          letterSpacing: "-0.03em",
          color: "var(--text-primary)",
        }}>
          <span style={{
            display: "inline-block",
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: "var(--accent)",
          }} />
          MediCall
        </Link>

        <nav style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <Link
            href="/"
            style={{
              padding: "0.375rem 0.75rem",
              borderRadius: "var(--radius-sm)",
              fontSize: 14,
              fontWeight: 500,
              color: isActive("/") ? "var(--text-primary)" : "var(--text-secondary)",
              background: isActive("/") ? "var(--surface-hover)" : "transparent",
              transition: "all var(--transition)",
            }}
          >
            Upload
          </Link>
          <Link
            href="/calls"
            style={{
              padding: "0.375rem 0.75rem",
              borderRadius: "var(--radius-sm)",
              fontSize: 14,
              fontWeight: 500,
              color: isActive("/calls") ? "var(--text-primary)" : "var(--text-secondary)",
              background: isActive("/calls") ? "var(--surface-hover)" : "transparent",
              transition: "all var(--transition)",
            }}
          >
            Past Calls
          </Link>
          {status && (
            <div style={{ marginLeft: 12, paddingLeft: 12, borderLeft: "1px solid var(--border)" }}>
              <ConnectionStatus status={status} />
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
