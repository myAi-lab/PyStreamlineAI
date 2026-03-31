import { apiRequest } from "@/lib/api/client";
import type {
  ImmigrationBriefResponse,
  ImmigrationRefreshResponse,
  ImmigrationSearchResponse,
  TokenPair
} from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function searchImmigrationUpdates(
  tokens: AuthTokens,
  payload: { query: string; visa_categories: string[]; limit: number; force_refresh: boolean }
): Promise<ImmigrationSearchResponse> {
  return apiRequest<ImmigrationSearchResponse>("/api/v1/immigration/search", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function refreshImmigrationUpdates(tokens: AuthTokens): Promise<ImmigrationRefreshResponse> {
  return apiRequest<ImmigrationRefreshResponse>("/api/v1/immigration/refresh", {
    method: "POST",
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function buildImmigrationBrief(
  tokens: AuthTokens,
  payload: { query: string; visa_categories: string[]; limit: number }
): Promise<ImmigrationBriefResponse> {
  return apiRequest<ImmigrationBriefResponse>("/api/v1/immigration/brief", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

