import { apiRequest } from "@/lib/api/client";
import type { ModelConfig, TokenPair, Usage } from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function fetchUsage(tokens: AuthTokens): Promise<Usage> {
  return apiRequest<Usage>("/api/v1/platform/me/usage", {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function fetchModelConfig(tokens: AuthTokens): Promise<ModelConfig> {
  return apiRequest<ModelConfig>("/api/v1/models/config", {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function submitFeedback(
  tokens: AuthTokens,
  payload: { category: string; message: string }
): Promise<{ accepted: boolean }> {
  return apiRequest<{ accepted: boolean }>("/api/v1/platform/feedback", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

