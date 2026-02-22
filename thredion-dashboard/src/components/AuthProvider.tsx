"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getAuthToken, setAuthToken, clearAuth, getMe } from "@/lib/api";

interface AuthUser {
  id: number;
  phone: string;
  name: string;
  created_at: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  loading: true,
  login: () => {},
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount, check for existing token
  useEffect(() => {
    const stored = getAuthToken();
    if (stored) {
      setToken(stored);

      // Try to load cached user immediately (so refresh feels instant)
      if (typeof window !== "undefined") {
        try {
          const cached = localStorage.getItem("thredion_user");
          if (cached) setUser(JSON.parse(cached));
        } catch { /* ignore */ }
      }

      // Validate the token by calling /auth/me
      getMe()
        .then((u) => {
          setUser(u);
          if (typeof window !== "undefined")
            localStorage.setItem("thredion_user", JSON.stringify(u));
        })
        .catch((err) => {
          // Only clear auth if the backend explicitly rejected (401)
          // Don't clear on network errors — keep the session alive
          if (err.message?.includes("Session expired") || err.message?.includes("401")) {
            clearAuth();
            setToken(null);
            setUser(null);
          }
          // else: backend might be temporarily down, keep the cached session
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = (newToken: string, newUser: AuthUser) => {
    setAuthToken(newToken);
    setToken(newToken);
    setUser(newUser);
    if (typeof window !== "undefined") {
      localStorage.setItem("thredion_user", JSON.stringify(newUser));
    }
  };

  const logout = () => {
    clearAuth();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
