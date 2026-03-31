"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { InterviewWindow } from "@/components/interview/InterviewWindow";
import { TurnEvaluationCard } from "@/components/interview/turn-evaluation-card";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { TextArea } from "@/components/ui/textarea";
import { useInterviewWS } from "@/hooks/useInterviewWS";
import { useAuth } from "@/lib/auth/auth-context";
import { cn } from "@/lib/utils/cn";
import {
  getInterviewSession,
  respondInterviewTurn,
  startInterviewSession
} from "@/services/interview-service";
import type {
  InterviewRespondResponse,
  InterviewSessionDetail,
  InterviewStartResponse,
  InterviewTurn
} from "@/types/api";

type InterviewChatProps = {
  sessionId: string;
  fullScreen?: boolean;
};

function upsertTurn(turns: InterviewTurn[], turn: InterviewTurn) {
  const existing = turns.findIndex((item) => item.id === turn.id);
  if (existing < 0) {
    return [...turns, turn].sort((a, b) => a.turn_index - b.turn_index);
  }
  return turns.map((item) => (item.id === turn.id ? turn : item));
}

export function InterviewChat({ sessionId, fullScreen = false }: InterviewChatProps) {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const { connected, status: wsStatus, lastMessage, send, error: wsError } = useInterviewWS({
    sessionId,
    token: accessToken,
    enabled: Boolean(accessToken)
  });
  const [detail, setDetail] = useState<InterviewSessionDetail | null>(null);
  const [response, setResponse] = useState<InterviewRespondResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showSessionData, setShowSessionData] = useState(!fullScreen);
  const transcriptBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setShowSessionData(!fullScreen);
  }, [fullScreen]);

  async function loadSession() {
    if (!accessToken) return;
    setLoading(true);
    try {
      const data = await getInterviewSession(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        sessionId
      );
      setDetail(data);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load session");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSession();
  }, [accessToken, refreshToken, sessionId]);

  useEffect(() => {
    transcriptBottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [detail?.turns.length]);

  function applyStartPayload(payload: InterviewStartResponse) {
    setDetail((previous) => {
      if (!previous) {
        return {
          session: payload.session,
          turns: [payload.first_turn],
          summary: null
        };
      }
      return {
        ...previous,
        session: payload.session,
        turns: upsertTurn(previous.turns, payload.first_turn)
      };
    });
  }

  function applyResponsePayload(payload: InterviewRespondResponse) {
    setResponse(payload);
    setDetail((previous) => {
      if (!previous) {
        return null;
      }
      const withEvaluated = upsertTurn(previous.turns, payload.evaluated_turn);
      const withNext = payload.next_turn ? upsertTurn(withEvaluated, payload.next_turn) : withEvaluated;
      return {
        ...previous,
        session: payload.session,
        turns: withNext
      };
    });
  }

  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.type === "session_started") {
      applyStartPayload(lastMessage.payload as InterviewStartResponse);
    }
    if (lastMessage.type === "turn_processed") {
      applyResponsePayload(lastMessage.payload as InterviewRespondResponse);
      setAnswer("");
      setSubmitting(false);
    }
    if (lastMessage.type === "error") {
      const payload = lastMessage.payload as { message?: string };
      setError(payload.message ?? "Realtime interaction failed");
      setSubmitting(false);
    }
  }, [lastMessage]);

  async function handleStart() {
    setError(null);
    setSubmitting(true);
    if (connected && send({ type: "start" })) {
      return;
    }
    try {
      const started = await startInterviewSession(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        sessionId
      );
      applyStartPayload(started);
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Could not start session");
    } finally {
      setSubmitting(false);
    }
  }

  async function submitAnswerText(rawAnswer: string) {
    setError(null);
    const cleanAnswer = rawAnswer.trim();
    if (!cleanAnswer) {
      setError("Answer cannot be empty");
      return;
    }

    setSubmitting(true);

    if (connected && send({ type: "respond", answer: cleanAnswer })) {
      return;
    }

    try {
      const turnResponse = await respondInterviewTurn(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        { sessionId, answer: cleanAnswer }
      );
      applyResponsePayload(turnResponse);
      setAnswer("");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Turn submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitAnswerText(answer);
  }

  if (loading) {
    return (
      <div className="flex min-h-[30vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!detail) {
    return <Alert variant="error">{error ?? "Session not available"}</Alert>;
  }

  const latestPendingQuestion =
    [...detail.turns].reverse().find((turn) => !turn.candidate_message)?.interviewer_message ??
    detail.turns.at(-1)?.interviewer_message ??
    null;

  const sessionDetails = (
    <div className={cn("grid gap-4", fullScreen ? "mt-3 xl:grid-cols-[1fr_320px]" : "xl:grid-cols-[1fr_320px]")}>
      <Card className={cn("flex flex-col", fullScreen ? "min-h-[34vh]" : "min-h-[56vh]")}>
        <div className="flex items-center justify-between border-b border-slate-700 pb-3">
          <div>
            <h2 className="text-lg font-semibold text-white">Interview Transcript</h2>
            <p className="text-sm text-slate-400">
              {detail.session.session_mode} - session status: {detail.session.status}
            </p>
          </div>
          <Badge>{connected ? "Realtime connected" : "REST fallback"}</Badge>
        </div>

        <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1">
          {detail.turns.length === 0 ? (
            <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-sm text-slate-300">
              Start the interview session to receive the first question.
            </div>
          ) : (
            detail.turns.map((turn) => (
              <div key={turn.id} className="space-y-2 rounded-xl border border-slate-700 bg-slate-900/55 p-4">
                <p className="text-xs uppercase tracking-wide text-brand-100">Interviewer</p>
                <p className="text-sm text-slate-100">{turn.interviewer_message}</p>
                <p className="mt-3 text-xs uppercase tracking-wide text-slate-400">Candidate</p>
                <p className="text-sm text-slate-300">
                  {turn.candidate_message ?? <span className="text-slate-500">Awaiting response...</span>}
                </p>
              </div>
            ))
          )}
          <div ref={transcriptBottomRef} />
        </div>

        {error ? <Alert variant="error" className="mt-3">{error}</Alert> : null}

        <div className="mt-4 border-t border-slate-700 pt-3">
          {detail.turns.length === 0 ? (
            <p className="text-sm text-slate-400">
              Use the <span className="font-semibold text-slate-200">Start Interview</span> button in the live controls.
            </p>
          ) : (
            <form className="space-y-3" onSubmit={handleSubmit}>
              <TextArea
                value={answer}
                rows={4}
                onChange={(event) => setAnswer(event.target.value)}
                placeholder="Manual fallback answer input..."
              />
              <Button type="submit" disabled={submitting || detail.session.status === "completed"}>
                {submitting ? (
                  <span className="inline-flex items-center gap-2">
                    <Spinner /> Submitting...
                  </span>
                ) : detail.session.status === "completed" ? (
                  "Session Completed"
                ) : (
                  "Submit Answer"
                )}
              </Button>
            </form>
          )}
        </div>
      </Card>

      <div className="space-y-4">
        <TurnEvaluationCard response={response} />
        {detail.summary ? (
          <Card>
            <h4 className="text-sm font-semibold text-white">Final Recommendation</h4>
            <p className="mt-2 text-sm text-slate-300">{detail.summary.summary}</p>
            <p className="mt-2 text-sm text-brand-100">
              Score: {detail.summary.final_score.toFixed(1)} - {detail.summary.recommendation}
            </p>
          </Card>
        ) : null}
      </div>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="flex h-full flex-col">
        <InterviewWindow
          latestQuestion={latestPendingQuestion}
          roleTarget={detail.session.role_target}
          sessionMode={detail.session.session_mode}
          sessionStatus={detail.session.status}
          wsStatus={wsStatus}
          wsError={wsError}
          disabled={detail.session.status === "completed"}
          isProcessing={submitting}
          onStartInterview={handleStart}
          onSubmitAnswer={submitAnswerText}
          fullScreen
        />

        <div className="border-t border-slate-800 bg-slate-950/90 px-4 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="secondary" onClick={() => setShowSessionData((previous) => !previous)}>
              {showSessionData ? "Hide Transcript Panel" : "Show Transcript Panel"}
            </Button>
            <Badge>{connected ? "Realtime connected" : "REST fallback"}</Badge>
            {error ? <span className="text-xs text-rose-200">{error}</span> : null}
          </div>
          {showSessionData ? sessionDetails : null}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <InterviewWindow
        latestQuestion={latestPendingQuestion}
        roleTarget={detail.session.role_target}
        sessionMode={detail.session.session_mode}
        sessionStatus={detail.session.status}
        wsStatus={wsStatus}
        wsError={wsError}
        disabled={detail.session.status === "completed"}
        isProcessing={submitting}
        onStartInterview={handleStart}
        onSubmitAnswer={submitAnswerText}
      />
      {sessionDetails}
    </div>
  );
}
