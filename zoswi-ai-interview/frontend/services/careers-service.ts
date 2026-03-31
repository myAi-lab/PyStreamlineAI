import { apiRequest } from "@/lib/api/client";
import type { CareersMatchResponse, TokenPair } from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function runCareersMatch(
  tokens: AuthTokens,
  payload: {
    role_query: string;
    preferred_location: string;
    visa_status: string;
    sponsorship_required: boolean;
    selected_position_types: string[];
    posted_within_days: number;
    max_results: number;
    resume_id?: string | null;
    target_job_description?: string;
  }
): Promise<CareersMatchResponse> {
  return apiRequest<CareersMatchResponse>("/api/v1/careers/match", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

