"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  getClientAccessToken,
  getRecruiterAccessState,
  getRecruiterReplay,
  getRecruiterScorecard,
  postRecruiterReview
} from "../../../../lib/api";

type Props = {
  params: { id: string };
};

export default function RecruiterInterviewReviewPage({ params }: Props) {
  const sessionId = String(params.id || "").trim();
  const [scorecard, setScorecard] = useState<any>(null);
  const [replay, setReplay] = useState<any>(null);
  const [decision, setDecision] = useState("Hire");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [savedMessage, setSavedMessage] = useState("");

  useEffect(() => {
    let mounted = true;
    const token = getClientAccessToken();
    const access = getRecruiterAccessState(token || undefined);
    if (!access.allowed) {
      if (mounted) {
        setScorecard(null);
        setReplay(null);
        setError(access.message || "Recruiter access is restricted.");
      }
      return () => {
        mounted = false;
      };
    }
    Promise.all([getRecruiterScorecard(sessionId, token || undefined), getRecruiterReplay(sessionId, token || undefined)])
      .then(([scorePayload, replayPayload]) => {
        if (!mounted) {
          return;
        }
        setScorecard(scorePayload);
        setReplay(replayPayload);
      })
      .catch((err) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Unable to load interview review.");
        }
      });
    return () => {
      mounted = false;
    };
  }, [sessionId]);

  async function submitReview() {
    setError("");
    setSavedMessage("");
    try {
      const token = getClientAccessToken();
      const access = getRecruiterAccessState(token || undefined);
      if (!access.allowed) {
        setError(access.message || "Recruiter access is restricted.");
        return;
      }
      await postRecruiterReview(
        sessionId,
        {
          decision,
          notes,
          override_recommendation: false
        },
        token || undefined
      );
      setSavedMessage("Reviewer note saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit review.");
    }
  }

  const finalAssessment = scorecard?.final_assessment || {};
  const transcriptRows = Array.isArray(replay?.transcripts) ? replay.transcripts : [];

  return (
    <main className="relative mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <section className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-[var(--font-display)] text-3xl font-semibold text-slate-100">Interview Replay and Scorecard</h1>
          <div className="flex flex-wrap gap-2">
            <Link href="/recruiter/queue" className="rounded-lg border border-white/20 px-3 py-2 text-sm text-slate-200">
              Interview Queue
            </Link>
            <Link href="/recruiter/exports" className="rounded-lg border border-white/20 px-3 py-2 text-sm text-slate-200">
              Export Results
            </Link>
          </div>
        </div>

        {error ? <p className="mt-4 rounded-lg bg-rose-500/20 px-3 py-2 text-sm text-rose-100">{error}</p> : null}
        {savedMessage ? <p className="mt-4 rounded-lg bg-emerald-500/20 px-3 py-2 text-sm text-emerald-100">{savedMessage}</p> : null}

        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          <article className="rounded-xl border border-white/10 bg-white/5 p-4">
            <h2 className="text-lg font-semibold text-slate-100">Scorecard View</h2>
            <p className="mt-2 text-sm text-slate-200">Overall Score: {typeof finalAssessment.overall_score === "number" ? finalAssessment.overall_score.toFixed(1) : "N/A"}</p>
            <p className="mt-1 text-sm text-slate-200">Recommendation: {finalAssessment.recommendation || "N/A"}</p>
            <p className="mt-1 text-sm text-slate-200">Competency Coverage: {typeof finalAssessment.competency_coverage === "number" ? `${finalAssessment.competency_coverage}%` : "N/A"}</p>
            <p className="mt-3 text-sm text-slate-300">{finalAssessment.summary_text || "No summary available."}</p>
          </article>

          <article className="rounded-xl border border-white/10 bg-white/5 p-4">
            <h2 className="text-lg font-semibold text-slate-100">Reviewer Notes</h2>
            <label className="mt-3 block text-sm text-slate-200">Decision</label>
            <select value={decision} onChange={(event) => setDecision(event.target.value)} className="soft-input mt-1">
              <option>Strong Hire</option>
              <option>Hire</option>
              <option>Leaning No</option>
              <option>No Hire</option>
            </select>
            <label className="mt-3 block text-sm text-slate-200">Notes</label>
            <textarea value={notes} onChange={(event) => setNotes(event.target.value)} className="soft-input mt-1 min-h-28" />
            <button onClick={submitReview} className="mt-3 rounded-lg border border-cyan-300/30 bg-cyan-400/90 px-4 py-2 text-sm font-semibold text-slate-900">
              Save Review
            </button>
          </article>
        </div>

        <section className="mt-6 rounded-xl border border-white/10 bg-white/5 p-4">
          <h2 className="text-lg font-semibold text-slate-100">Interview Replay</h2>
          <div className="mt-3 max-h-[420px] overflow-y-auto space-y-2">
            {transcriptRows.map((line: any, index: number) => (
              <div key={`${line.sequence_no || index}`} className="rounded-lg border border-white/10 bg-slate-950/40 p-3 text-sm text-slate-200">
                <p className="text-xs uppercase tracking-wide text-slate-400">{line.speaker}</p>
                <p className="mt-1">{line.text}</p>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
