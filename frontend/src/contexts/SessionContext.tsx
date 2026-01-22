import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";
import { LayoutType, DEFAULT_LAYOUT, LAYOUT_CONFIGS } from "../types/layout";

interface SessionContextType {
  /** Current session ID */
  sessionId: string | null;
  /** Selected layout type */
  layoutType: LayoutType;
  /** Layout configuration for current layout */
  layoutConfig: (typeof LAYOUT_CONFIGS)[LayoutType];
  /** Set session ID */
  setSessionId: (id: string | null) => void;
  /** Set layout type */
  setLayoutType: (layout: LayoutType) => void;
  /** Reset session to initial state */
  resetSession: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

interface SessionProviderProps {
  children: ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [sessionId, setSessionIdState] = useState<string | null>(() => {
    // Restore from sessionStorage if available
    return sessionStorage.getItem("sessionId");
  });

  const [layoutType, setLayoutTypeState] = useState<LayoutType>(() => {
    // Restore from sessionStorage if available
    const stored = sessionStorage.getItem("layoutType");
    return (stored as LayoutType) || DEFAULT_LAYOUT;
  });

  const setSessionId = useCallback((id: string | null) => {
    setSessionIdState(id);
    if (id) {
      sessionStorage.setItem("sessionId", id);
    } else {
      sessionStorage.removeItem("sessionId");
    }
  }, []);

  const setLayoutType = useCallback((layout: LayoutType) => {
    setLayoutTypeState(layout);
    sessionStorage.setItem("layoutType", layout);
  }, []);

  const resetSession = useCallback(() => {
    setSessionIdState(null);
    setLayoutTypeState(DEFAULT_LAYOUT);
    sessionStorage.removeItem("sessionId");
    sessionStorage.removeItem("layoutType");
  }, []);

  const layoutConfig = LAYOUT_CONFIGS[layoutType];

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        layoutType,
        layoutConfig,
        setSessionId,
        setLayoutType,
        resetSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
}
