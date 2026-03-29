import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { flushSync } from "react-dom";
import {
  clearAuthSession,
  fetchAuthMe,
  getStoredToken,
  getStoredUser,
  loginRequest,
  setAuthSession,
  signupRequest,
} from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken());
  const [user, setUser] = useState(() => getStoredUser());
  const [bootstrapping, setBootstrapping] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      const t = getStoredToken();
      if (!t) {
        setBootstrapping(false);
        return;
      }
      const me = await fetchAuthMe();
      if (cancelled) return;
      if (me.data?.user_id) {
        setUser({
          user_id: me.data.user_id,
          email: me.data.email,
          name: me.data.name,
        });
        setAuthSession(t, {
          user_id: me.data.user_id,
          email: me.data.email,
          name: me.data.name,
        });
      } else {
        clearAuthSession();
        setToken(null);
        setUser(null);
      }
      setBootstrapping(false);
    }
    boot();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await loginRequest(email, password);
    if (res.error) return { error: typeof res.error === "string" ? res.error : res.error?.detail || "Login failed" };
    const d = res.data;
    const u = { user_id: d.user_id, email: d.email, name: d.name };
    // Persist first, then flush React state so ProtectedRoute / <Navigate> see auth immediately (avoids race with router).
    setAuthSession(d.access_token, u);
    flushSync(() => {
      setToken(d.access_token);
      setUser(u);
    });
    return { error: null };
  }, []);

  const signup = useCallback(async (name, email, password) => {
    const res = await signupRequest(name, email, password);
    if (res.error) {
      const msg =
        typeof res.error === "string"
          ? res.error
          : Array.isArray(res.error)
            ? res.error.map((x) => x.msg).join(", ")
            : res.error?.detail || "Signup failed";
      return { error: msg };
    }
    const d = res.data;
    const u = { user_id: d.user_id, email: d.email, name: d.name };
    setAuthSession(d.access_token, u);
    flushSync(() => {
      setToken(d.access_token);
      setUser(u);
    });
    return { error: null };
  }, []);

  const logout = useCallback(() => {
    clearAuthSession();
    setToken(null);
    setUser(null);
  }, []);

  const isAuthenticated = useMemo(() => {
    if (bootstrapping) return false;
    if (token && user?.user_id) return true;
    // Same tick as login/signup: localStorage is updated before React state may be visible everywhere
    const t = getStoredToken();
    const u = getStoredUser();
    return Boolean(t && (u?.user_id || u?.id));
  }, [bootstrapping, token, user]);

  const value = useMemo(() => {
    const su = getStoredUser();
    return {
      token,
      user,
      userId: user?.user_id || su?.user_id || su?.id || null,
      bootstrapping,
      login,
      signup,
      logout,
      isAuthenticated,
    };
  }, [token, user, bootstrapping, login, signup, logout, isAuthenticated]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
