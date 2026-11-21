"use client";

import { createContext, useContext, useEffect, useState } from "react";

import { type ApiClient, ApiError, createApiClient, toApiError } from "@/lib/api/client";
import type { User, UserRegister } from "@/lib/api/types";

import { SessionTokens } from "./session-tokens";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthState {
  status: Status;
  user: User | null;
  api: ApiClient;
  login(email: string, password: string): Promise<void>;
  register(body: UserRegister): Promise<void>;
  logout(): Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [user, setUser] = useState<User | null>(null);
  // Created once per provider. The access token lives only in memory; the refresh
  // token is an httpOnly cookie handled by /api/session.
  const [tokens] = useState(
    () =>
      new SessionTokens(() => {
        setUser(null);
        setStatus("anonymous");
      }),
  );
  const [api] = useState(() => createApiClient(tokens));

  async function loadUser() {
    setUser(await api.get<User>("/auth/me"));
    setStatus("authenticated");
  }

  // Silent login: if the refresh cookie is still valid, restore the session.
  useEffect(() => {
    let active = true;
    tokens.refreshAccessToken().then(async (token) => {
      if (!token || !active) return;
      try {
        const me = await api.get<User>("/auth/me");
        if (active) {
          setUser(me);
          setStatus("authenticated");
        }
      } catch {
        if (active) setStatus("anonymous");
      }
    });
    return () => {
      active = false;
    };
  }, [tokens, api]);

  async function login(email: string, password: string) {
    const res = await fetch("/api/session", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw await toApiError(res);
    tokens.setAccessToken(((await res.json()) as { access_token: string }).access_token);
    await loadUser();
  }

  async function register(body: UserRegister) {
    await api.post<User>("/auth/register", body);
    await login(body.email, body.password);
  }

  async function logout() {
    await fetch("/api/session", { method: "DELETE" }).catch(() => undefined);
    tokens.setAccessToken(null);
    setUser(null);
    setStatus("anonymous");
  }

  return (
    <AuthContext.Provider value={{ status, user, api, login, register, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export { ApiError };
