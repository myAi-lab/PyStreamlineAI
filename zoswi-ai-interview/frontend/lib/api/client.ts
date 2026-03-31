import type { ApiEnvelope, ApiErrorEnvelope, TokenPair } from "@/types/api";
import { clearAuthSession } from "@/lib/auth/token-store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
  accessToken?: string | null;
  refreshToken?: string | null;
  onTokenRefresh?: (tokens: TokenPair) => void;
};

export class APIClientError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown> | undefined;

  constructor({
    message,
    code,
    status,
    details
  }: {
    message: string;
    code: string;
    status: number;
    details?: Record<string, unknown>;
  }) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function parseError(response: Response): Promise<APIClientError> {
  const fallbackMessage = `Request failed with status ${response.status}`;
  try {
    const payload = (await response.json()) as ApiErrorEnvelope;
    return new APIClientError({
      message: payload.error?.message ?? fallbackMessage,
      code: payload.error?.code ?? "request_failed",
      status: response.status,
      details: payload.error?.details
    });
  } catch {
    return new APIClientError({
      message: fallbackMessage,
      code: "request_failed",
      status: response.status
    });
  }
}

async function refreshAccessToken(refreshToken: string): Promise<TokenPair> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  const payload = (await response.json()) as ApiEnvelope<TokenPair>;
  return payload.data;
}

function emitUnauthorized() {
  clearAuthSession();
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("zoswi:auth:unauthorized"));
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const requestInit: RequestInit = {
    method: options.method ?? "GET",
    headers: { ...(options.headers ?? {}) }
  };

  if (options.accessToken) {
    requestInit.headers = {
      ...requestInit.headers,
      Authorization: `Bearer ${options.accessToken}`
    };
  }

  if (options.body instanceof FormData) {
    requestInit.body = options.body;
  } else if (options.body !== undefined) {
    requestInit.body = JSON.stringify(options.body);
    requestInit.headers = {
      ...requestInit.headers,
      "Content-Type": "application/json"
    };
  }

  const response = await fetch(`${API_BASE_URL}${path}`, requestInit);
  if (response.status === 401 && options.refreshToken && options.onTokenRefresh) {
    try {
      const tokens = await refreshAccessToken(options.refreshToken);
      options.onTokenRefresh(tokens);
      return apiRequest<T>(path, {
        ...options,
        accessToken: tokens.access_token
      });
    } catch (refreshError) {
      emitUnauthorized();
      throw refreshError;
    }
  }

  if (response.status === 401) {
    emitUnauthorized();
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  const payload = (await response.json()) as ApiEnvelope<T>;
  return payload.data;
}

export function apiBaseUrl() {
  return API_BASE_URL;
}
