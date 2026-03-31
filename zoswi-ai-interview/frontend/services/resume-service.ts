import { apiRequest } from "@/lib/api/client";
import type { Resume, ResumeAnalysis, ResumeDetail, ResumeProcessResponse, TokenPair } from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function uploadResume(tokens: AuthTokens, file: File): Promise<ResumeProcessResponse> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<ResumeProcessResponse>("/api/v1/resumes/upload", {
    method: "POST",
    body,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function analyzeResumeText(
  tokens: AuthTokens,
  payload: {
    raw_text: string;
    file_name?: string;
  }
): Promise<ResumeProcessResponse> {
  return apiRequest<ResumeProcessResponse>("/api/v1/resumes/analyze-text", {
    method: "POST",
    body: payload,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function listResumes(tokens: AuthTokens): Promise<Resume[]> {
  return apiRequest<Resume[]>("/api/v1/resumes", {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function getResume(tokens: AuthTokens, resumeId: string): Promise<ResumeDetail> {
  return apiRequest<ResumeDetail>(`/api/v1/resumes/${resumeId}`, {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function getResumeAnalysis(tokens: AuthTokens, resumeId: string): Promise<ResumeAnalysis> {
  return apiRequest<ResumeAnalysis>(`/api/v1/resumes/${resumeId}/analysis`, {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

