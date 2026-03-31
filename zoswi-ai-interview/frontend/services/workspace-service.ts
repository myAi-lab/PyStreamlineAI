import { apiRequest } from "@/lib/api/client";
import type {
  RecentScoreItem,
  TokenPair,
  WorkspaceMessageSendResponse,
  WorkspaceSession,
  WorkspaceSessionDetail
} from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function createWorkspaceSession(
  tokens: AuthTokens,
  payload: { title?: string }
): Promise<WorkspaceSession> {
  return apiRequest<WorkspaceSession>("/api/v1/workspace/sessions", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function listWorkspaceSessions(tokens: AuthTokens): Promise<WorkspaceSession[]> {
  return apiRequest<WorkspaceSession[]>("/api/v1/workspace/sessions", {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function getWorkspaceSession(
  tokens: AuthTokens,
  sessionId: string
): Promise<WorkspaceSessionDetail> {
  return apiRequest<WorkspaceSessionDetail>(`/api/v1/workspace/sessions/${sessionId}`, {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function updateWorkspaceSession(
  tokens: AuthTokens,
  sessionId: string,
  title: string
): Promise<WorkspaceSession> {
  return apiRequest<WorkspaceSession>(`/api/v1/workspace/sessions/${sessionId}`, {
    method: "PATCH",
    body: { title },
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function sendWorkspaceMessage(
  tokens: AuthTokens,
  payload: { sessionId: string; message: string }
): Promise<WorkspaceMessageSendResponse> {
  return apiRequest<WorkspaceMessageSendResponse>(`/api/v1/workspace/sessions/${payload.sessionId}/messages`, {
    method: "POST",
    body: { message: payload.message },
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function listRecentScores(tokens: AuthTokens): Promise<RecentScoreItem[]> {
  return apiRequest<RecentScoreItem[]>("/api/v1/workspace/recent-scores", {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}
