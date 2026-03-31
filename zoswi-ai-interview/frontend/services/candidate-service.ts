import { apiRequest } from "@/lib/api/client";
import type { CandidateProfile, TokenPair } from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function fetchCandidateProfile(tokens: AuthTokens): Promise<CandidateProfile> {
  return apiRequest<CandidateProfile>("/api/v1/candidate/profile", {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function updateCandidateProfile(
  tokens: AuthTokens,
  payload: {
    headline: string | null;
    years_experience: number | null;
    target_roles: string[];
    location: string | null;
    role_contact_email: string | null;
    role_profile: Record<string, string>;
  }
): Promise<CandidateProfile> {
  return apiRequest<CandidateProfile>("/api/v1/candidate/profile", {
    method: "PUT",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}
