import type { UserPublic } from "@/types/api";

const ACCESS_TOKEN_KEY = "zoswi_access_token";
const REFRESH_TOKEN_KEY = "zoswi_refresh_token";
const USER_KEY = "zoswi_user";

function isBrowser() {
  return typeof window !== "undefined";
}

function setCookie(name: string, value: string, maxAgeSeconds: number) {
  if (!isBrowser()) return;
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax`;
}

function clearCookie(name: string) {
  if (!isBrowser()) return;
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function persistAuthSession(payload: {
  accessToken: string;
  refreshToken: string;
  user: UserPublic;
  accessTtlMinutes: number;
}) {
  if (!isBrowser()) return;
  localStorage.setItem(ACCESS_TOKEN_KEY, payload.accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, payload.refreshToken);
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  setCookie("zoswi_access_token", payload.accessToken, payload.accessTtlMinutes * 60);
}

export function getStoredAccessToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): UserPublic | null {
  if (!isBrowser()) return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserPublic;
  } catch {
    return null;
  }
}

export function clearAuthSession() {
  if (!isBrowser()) return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  clearCookie("zoswi_access_token");
}

