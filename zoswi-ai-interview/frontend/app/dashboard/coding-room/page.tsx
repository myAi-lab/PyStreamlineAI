"use client";

import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { TextArea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth/auth-context";
import { listCodingStages, getCodingStarterCode, runCodingHiddenCheck, evaluateCodingStage } from "@/services/coding-room-service";
import { getResume, listResumes } from "@/services/resume-service";
import type {
  CodingEvaluationResponse,
  CodingHiddenCheckResponse,
  CodingRoomStage,
  InterviewMode
} from "@/types/api";

const languageOptions = ["python", "java", "javascript", "typescript", "go", "c++"] as const;

export default function CodingRoomPage() {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [roleTarget, setRoleTarget] = useState("Software Engineer");
  const [interviewMode, setInterviewMode] = useState<InterviewMode>("mixed");
  const [language, setLanguage] = useState<(typeof languageOptions)[number]>("python");
  const [stages, setStages] = useState<CodingRoomStage[]>([]);
  const [stageIndex, setStageIndex] = useState(1);
  const [code, setCode] = useState("");
  const [resumeContext, setResumeContext] = useState("");
  const [hiddenCheck, setHiddenCheck] = useState<CodingHiddenCheckResponse | null>(null);
  const [evaluation, setEvaluation] = useState<CodingEvaluationResponse | null>(null);
  const [loadingStages, setLoadingStages] = useState(true);
  const [loadingStarter, setLoadingStarter] = useState(false);
  const [checkingHidden, setCheckingHidden] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeStage = stages[stageIndex - 1];

  useEffect(() => {
    let active = true;
    void (async () => {
      if (!accessToken) return;
      setLoadingStages(true);
      setError(null);
      try {
        const stagePayload = await listCodingStages(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          { role_target: roleTarget, interview_mode: interviewMode }
        );
        if (!active) return;
        setStages(stagePayload.stages);
        setStageIndex(1);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Unable to load coding stages");
      } finally {
        if (active) setLoadingStages(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, applyRefreshedTokens, interviewMode, refreshToken, roleTarget]);

  useEffect(() => {
    let active = true;
    void (async () => {
      if (!accessToken) return;
      try {
        const resumes = await listResumes({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens });
        if (!active || !resumes[0]) return;
        const detail = await getResume(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          resumes[0].id
        );
        if (!active) return;
        setResumeContext(detail.raw_text.slice(0, 8000));
      } catch {
        if (!active) return;
        setResumeContext("");
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, applyRefreshedTokens, refreshToken]);

  useEffect(() => {
    let active = true;
    if (!accessToken || !activeStage) return;
    setLoadingStarter(true);
    setHiddenCheck(null);
    setEvaluation(null);
    void (async () => {
      try {
        const starter = await getCodingStarterCode(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          {
            stage_index: stageIndex,
            language,
            role_target: roleTarget
          }
        );
        if (!active) return;
        setCode(starter.code);
      } catch (starterError) {
        if (!active) return;
        setError(starterError instanceof Error ? starterError.message : "Unable to load starter code");
      } finally {
        if (active) setLoadingStarter(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, activeStage, applyRefreshedTokens, language, refreshToken, roleTarget, stageIndex]);

  async function runHiddenChecks() {
    if (!accessToken) return;
    setCheckingHidden(true);
    setError(null);
    try {
      const response = await runCodingHiddenCheck(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {
          stage_index: stageIndex,
          language,
          role_target: roleTarget,
          code,
          resume_context: resumeContext
        }
      );
      setHiddenCheck(response);
    } catch (checkError) {
      setError(checkError instanceof Error ? checkError.message : "Hidden check failed");
    } finally {
      setCheckingHidden(false);
    }
  }

  async function runEvaluation() {
    if (!accessToken) return;
    setEvaluating(true);
    setError(null);
    try {
      const response = await evaluateCodingStage(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {
          stage_index: stageIndex,
          language,
          role_target: roleTarget,
          code,
          resume_context: resumeContext
        }
      );
      setEvaluation(response);
    } catch (evaluationError) {
      setError(evaluationError instanceof Error ? evaluationError.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }

  if (loadingStages) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">AI Coding Room</h1>
        <p className="text-sm text-slate-400">
          Three-stage interview simulation with starter code, hidden checks, and structured evaluation snapshots.
        </p>
      </div>

      {error ? <Alert variant="error">{error}</Alert> : null}

      <Card>
        <h3 className="text-lg font-semibold text-white">Session Setup</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <label className="space-y-1">
            <span className="text-sm text-slate-300">Target Role</span>
            <input
              className="h-10 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100 outline-none focus:border-brand-400"
              value={roleTarget}
              onChange={(event) => setRoleTarget(event.target.value)}
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-300">Interview Mode</span>
            <Select value={interviewMode} onChange={(event) => setInterviewMode(event.target.value as InterviewMode)}>
              <option value="mixed">Mixed</option>
              <option value="technical">Technical</option>
              <option value="behavioral">Behavioral</option>
            </Select>
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-300">Language</span>
            <Select value={language} onChange={(event) => setLanguage(event.target.value as (typeof languageOptions)[number])}>
              {languageOptions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </label>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[300px_1fr]">
        <Card>
          <h3 className="text-lg font-semibold text-white">Stages</h3>
          <div className="mt-3 space-y-2">
            {stages.map((stage) => {
              const selected = stage.stage_index === stageIndex;
              return (
                <button
                  key={stage.stage_index}
                  type="button"
                  onClick={() => setStageIndex(stage.stage_index)}
                  className={`w-full rounded-lg border p-3 text-left transition ${
                    selected
                      ? "border-brand-500 bg-brand-500/15"
                      : "border-slate-700 bg-slate-900/55 hover:border-slate-500"
                  }`}
                >
                  <p className="text-sm font-semibold text-slate-100">{stage.title}</p>
                  <p className="mt-1 text-xs text-slate-400">{stage.skill_focus}</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {stage.difficulty} | {stage.time_limit_min} min
                  </p>
                </button>
              );
            })}
          </div>
        </Card>

        <Card>
          {activeStage ? (
            <>
              <h3 className="text-lg font-semibold text-white">{activeStage.title}</h3>
              <p className="mt-2 text-sm text-slate-300">{activeStage.challenge}</p>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                <div className="rounded-lg border border-slate-700 bg-slate-900/55 p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-400">Requirements</p>
                  <div className="mt-2 space-y-1 text-sm text-slate-300">
                    {activeStage.requirements.map((item) => (
                      <p key={item}>- {item}</p>
                    ))}
                  </div>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-900/55 p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-400">Hints</p>
                  <div className="mt-2 space-y-1 text-sm text-slate-300">
                    {activeStage.hint_starters.map((item) => (
                      <p key={item}>- {item}</p>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <p className="mb-2 text-sm font-medium text-slate-300">Code Editor</p>
                {loadingStarter ? (
                  <div className="inline-flex items-center gap-2 text-sm text-slate-300">
                    <Spinner /> Loading starter code...
                  </div>
                ) : (
                  <TextArea value={code} onChange={(event) => setCode(event.target.value)} rows={18} />
                )}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={() => void runHiddenChecks()} disabled={checkingHidden}>
                  {checkingHidden ? "Running checks..." : "Run Hidden Checks"}
                </Button>
                <Button onClick={() => void runEvaluation()} disabled={evaluating} variant="secondary">
                  {evaluating ? "Evaluating..." : "Evaluate Stage"}
                </Button>
              </div>

              {hiddenCheck ? (
                <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/55 p-3">
                  <p className="text-sm font-semibold text-slate-100">
                    Hidden checks: {hiddenCheck.passed}/{hiddenCheck.total}
                  </p>
                  <p className="mt-1 text-sm text-slate-300">{hiddenCheck.summary}</p>
                  {hiddenCheck.failed_cases.length > 0 ? (
                    <div className="mt-2 text-xs text-slate-400">
                      {hiddenCheck.failed_cases.map((item) => (
                        <p key={item}>- {item}</p>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}

              {evaluation ? (
                <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/55 p-3">
                  <p className="text-sm font-semibold text-slate-100">
                    Stage score: {evaluation.score}% ({evaluation.verdict})
                  </p>
                  <div className="mt-2 grid gap-2 md:grid-cols-2">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-400">Strengths</p>
                      <div className="mt-1 text-sm text-slate-300">
                        {evaluation.strengths.map((item) => (
                          <p key={item}>- {item}</p>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-400">Improvements</p>
                      <div className="mt-1 text-sm text-slate-300">
                        {evaluation.improvements.map((item) => (
                          <p key={item}>- {item}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-slate-300">Next step: {evaluation.next_step}</p>
                </div>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-slate-400">No coding stages are currently available.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
