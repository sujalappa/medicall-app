"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { ConnectionStatus as ConnectionStatusType } from "../lib/types";

interface ConnectionContextValue {
  status: ConnectionStatusType | null;
  setStatus: (status: ConnectionStatusType | null) => void;
}

const ConnectionContext = createContext<ConnectionContextValue>({
  status: null,
  setStatus: () => {},
});

export function ConnectionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ConnectionStatusType | null>(null);
  return (
    <ConnectionContext.Provider value={{ status, setStatus }}>
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection() {
  return useContext(ConnectionContext);
}

export function useSetConnection() {
  const { setStatus } = useContext(ConnectionContext);
  return useCallback(
    (s: ConnectionStatusType | null) => setStatus(s),
    [setStatus]
  );
}
