import { apiRequest } from "@/lib/api/client";
import type {
  InterviewMode,
  InterviewRespondResponse,
  InterviewSession,
  InterviewSessionDetail,
  InterviewStartResponse,
  InterviewSummary,
  LiveInterviewLaunchResponse,
  TokenPair
} from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function createInterviewSession(
  tokens: AuthTokens,
  payload: { role_target: string; session_mode: InterviewMode }
): Promise<InterviewSession> {
  return apiRequest<InterviewSession>("/api/v1/interviews/sessions", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function listInterviewSessions(tokens: AuthTokens): Promise<InterviewSession[]> {
  return apiRequest<InterviewSession[]>("/api/v1/interviews/sessions", {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function getInterviewSession(
  tokens: AuthTokens,
  sessionId: string
): Promise<InterviewSessionDetail> {
  return apiRequest<InterviewSessionDetail>(`/api/v1/interviews/sessions/${sessionId}`, {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function startInterviewSession(
  tokens: AuthTokens,
  sessionId: string
): Promise<InterviewStartResponse> {
  return apiRequest<InterviewStartResponse>(`/api/v1/interviews/sessions/${sessionId}/start`, {
    method: "POST",
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function respondInterviewTurn(
  tokens: AuthTokens,
  payload: { sessionId: string; answer: string }
): Promise<InterviewRespondResponse> {
  return apiRequest<InterviewRespondResponse>(
    `/api/v1/interviews/sessions/${payload.sessionId}/respond`,
    {
      method: "POST",
      body: { answer: payload.answer },
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      onTokenRefresh: tokens.onTokenRefresh
    }
  );
}

export async function getInterviewSummary(
  tokens: AuthTokens,
  sessionId: string
): Promise<InterviewSummary> {
  return apiRequest<InterviewSummary>(`/api/v1/interviews/sessions/${sessionId}/summary`, {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function createLiveInterviewLaunchUrl(
  tokens: AuthTokens,
  payload: { candidate_name: string; target_role: string; requirement_type: InterviewMode }
): Promise<LiveInterviewLaunchResponse> {
  return apiRequest<LiveInterviewLaunchResponse>("/api/v1/interviews/live/launch-url", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}
