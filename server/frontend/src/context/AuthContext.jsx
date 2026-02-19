import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { API } from "../App";

const AuthContext = createContext(null);

const TOKEN_KEY = "miner_dashboard_token";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async (token) => {
    if (!token) return null;
    try {
      const r = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) return null;
      return await r.json();
    } catch {
      return null;
    }
  }, []);

  const initAuth = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    const u = await fetchUser(token);
    if (u) {
      setUser(u);
    } else {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    }
    setLoading(false);
  }, [fetchUser]);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const login = async (email, password) => {
    const r = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!r.ok) {
      const data = await r.json().catch(() => ({}));
      throw new Error(data.detail || "Login failed");
    }
    const { access_token } = await r.json();
    localStorage.setItem(TOKEN_KEY, access_token);
    const u = await fetchUser(access_token);
    setUser(u);
    return u;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };

  const getToken = () => localStorage.getItem(TOKEN_KEY);

  const value = {
    user,
    loading,
    login,
    logout,
    getToken,
    isAdmin: user?.role === "admin",
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
