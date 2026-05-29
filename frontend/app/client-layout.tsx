"use client";

import type { ReactNode } from "react";
import { ConnectionProvider } from "../components/connection-context";
import { Header } from "../components/header";

export function ClientLayout({ children }: { children: ReactNode }) {
  return (
    <ConnectionProvider>
      <Header />
      {children}
    </ConnectionProvider>
  );
}
