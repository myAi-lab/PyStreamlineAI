"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { apiRequest } from "@/lib/api/client";
import { clearAuthSession, getStoredAccessToken, getStoredRefreshToken, getStoredUser, persistAuthSession } from "@/lib/auth/token-store";
import type { AuthPayload, TokenPair, UserPublic } from "@/types/api";

type LoginInput = {
  email: string;
  password: string;
};

type SignupInput = LoginInput & {
  full_name: string;
  role: "candidate" | "student" | "recruiter";
  years_experience?: number;
  role_contact_email?: string;
  profile_data?: Record<string, string>;
};

type AuthContextValue = {
  user: UserPublic | null;
  accessToken: string | null;
  refreshToken: string | null;
  initialized: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginInput) => Promise<void>;
  signup: (payload: SignupInput) => Promise<void>;
  exchangeOAuthBridgeToken: (bridgeToken: string) => Promise<void>;
  logout: () => void;
  applyRefreshedTokens: (tokens: TokenPair) => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const storedUser = getStoredUser();
    const storedAccess = getStoredAccessToken();
    const storedRefresh = getStoredRefreshToken();
    setUser(storedUser);
    setAccessToken(storedAccess);
    setRefreshToken(storedRefresh);
    setInitialized(true);
  }, []);

  useEffect(() => {
    function onUnauthorized() {
      setUser(null);
      setAccessToken(null);
      setRefreshToken(null);
      clearAuthSession();
    }

    window.addEventListener("zoswi:auth:unauthorized", onUnauthorized);
    return () => {
      window.removeEventListener("zoswi:auth:unauthorized", onUnauthorized);
    };
  }, []);

  function persist(userValue: UserPublic, tokenPair: TokenPair) {
    setUser(userValue);
    setAccessToken(tokenPair.access_token);
    setRefreshToken(tokenPair.refresh_token);
    persistAuthSession({
      user: userValue,
      accessToken: tokenPair.access_token,
      refreshToken: tokenPair.refresh_token,
      accessTtlMinutes: tokenPair.access_token_expires_minutes
    });
  }

  async function login(payload: LoginInput) {
    const response = await apiRequest<AuthPayload>("/api/v1/auth/login", {
      method: "POST",
      body: payload
    });
    persist(response.user, response.tokens);
  }

  async function signup(payload: SignupInput) {
    const response = await apiRequest<AuthPayload>("/api/v1/auth/signup", {
      method: "POST",
      body: payload
    });
    persist(response.user, response.tokens);
  }

  async function exchangeOAuthBridgeToken(bridgeToken: string) {
    const response = await apiRequest<AuthPayload>("/api/v1/auth/oauth/exchange", {
      method: "POST",
      body: { bridge_token: bridgeToken }
    });
    persist(response.user, response.tokens);
  }

  function logout() {
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    clearAuthSession();
  }

  function applyRefreshedTokens(tokens: TokenPair) {
    if (!user) return;
    persist(user, tokens);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      refreshToken,
      initialized,
      isAuthenticated: Boolean(user && accessToken),
      login,
      signup,
      exchangeOAuthBridgeToken,
      logout,
      applyRefreshedTokens
    }),
    [accessToken, initialized, refreshToken, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
