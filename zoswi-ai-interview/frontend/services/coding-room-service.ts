import { apiRequest } from "@/lib/api/client";
import type {
  CodingEvaluationResponse,
  CodingHiddenCheckResponse,
  CodingRoomStagesResponse,
  CodingStarterCodeResponse,
  InterviewMode,
  TokenPair
} from "@/types/api";

type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  onTokenRefresh: (tokens: TokenPair) => void;
};

export async function listCodingStages(
  tokens: AuthTokens,
  payload: { role_target: string; interview_mode: InterviewMode }
): Promise<CodingRoomStagesResponse> {
  const params = new URLSearchParams({
    role_target: payload.role_target,
    interview_mode: payload.interview_mode
  });
  return apiRequest<CodingRoomStagesResponse>(`/api/v1/coding-room/stages?${params.toString()}`, {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    onTokenRefresh: tokens.onTokenRefresh
  });
}

export async function getCodingStarterCode(
  tokens: AuthTokens,
  payload: { stage_index: number; language: string; role_target: string }
): Promise<CodingStarterCodeResponse> {
  const params = new URLSearchParams({
    language: payload.language,
    role_target: payload.role_target
  });
  return apiRequest<CodingStarterCodeResponse>(
    `/api/v1/coding-room/stages/${payload.stage_index}/starter-code?${params.toString()}`,
    {
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      onTokenRefresh: tokens.onTokenRefresh
    }
  );
}

export async function runCodingHiddenCheck(
  tokens: AuthTokens,
  payload: {
    stage_index: number;
    language: string;
    role_target: string;
    code: string;
    resume_context?: string;
    job_description_context?: string;
  }
): Promise<CodingHiddenCheckResponse> {
  const params = new URLSearchParams({
    language: payload.language,
    role_target: payload.role_target
  });
  return apiRequest<CodingHiddenCheckResponse>(
    `/api/v1/coding-room/stages/${payload.stage_index}/hidden-check?${params.toString()}`,
    {
      method: "POST",
      body: {
        language: payload.language,
        code: payload.code,
        resume_context: payload.resume_context ?? "",
        job_description_context: payload.job_description_context ?? ""
      },
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      onTokenRefresh: tokens.onTokenRefresh
    }
  );
}

export async function evaluateCodingStage(
  tokens: AuthTokens,
  payload: {
    stage_index: number;
    language: string;
    role_target: string;
    code: string;
    resume_context?: string;
    job_description_context?: string;
  }
): Promise<CodingEvaluationResponse> {
  const params = new URLSearchParams({
    language: payload.language,
    role_target: payload.role_target
  });
  return apiRequest<CodingEvaluationResponse>(
    `/api/v1/coding-room/stages/${payload.stage_index}/evaluate?${params.toString()}`,
    {
      method: "POST",
      body: {
        language: payload.language,
        code: payload.code,
        resume_context: payload.resume_context ?? "",
        job_description_context: payload.job_description_context ?? ""
      },
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      onTokenRefresh: tokens.onTokenRefresh
    }
  );
}

