import type { InterviewResultResponse, StartInterviewResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL ??
  API_BASE_URL.replace("https://", "wss://").replace("http://", "ws://");

type StartInterviewPayload = {
  candidate_name: string;
  role: string;
  interview_type: "mixed" | "technical" | "behavioral";
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.error ?? response.statusText ?? "Request failed");
  }
  return (await response.json()) as T;
}

export function startInterview(payload: StartInterviewPayload) {
  return request<StartInterviewResponse>("/start-interview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export function getInterviewResult(sessionId: string) {
  const params = new URLSearchParams({ session_id: sessionId });
  return request<InterviewResultResponse>(`/interview-result?${params.toString()}`, {
    method: "GET",
    cache: "no-store"
  });
}

export function getInterviewWebSocketUrl(path = "/ws/interview") {
  return `${WS_BASE_URL}${path}`;
}
