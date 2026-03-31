"use client";

import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { ResumeAnalysisCard } from "@/components/resume/resume-analysis-card";
import { ResumeIngestionPanel } from "@/components/resume/resume-ingestion-panel";
import { useAuth } from "@/lib/auth/auth-context";
import { getResumeAnalysis, listResumes } from "@/services/resume-service";
import type { Resume, ResumeAnalysis, ResumeProcessResponse } from "@/types/api";
import { formatDateTime } from "@/lib/utils/date";

export default function DashboardResumePage() {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function reloadResumes() {
    if (!accessToken) return;
    const resumeList = await listResumes({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens });
    setResumes(resumeList);
    if (!selectedResumeId && resumeList[0]) {
      setSelectedResumeId(resumeList[0].id);
    }
  }

  async function loadAnalysis(resumeId: string) {
    if (!accessToken) return;
    try {
      const next = await getResumeAnalysis(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        resumeId
      );
      setAnalysis(next);
      setNotice(null);
    } catch (analysisError) {
      setAnalysis(null);
      setNotice(
        analysisError instanceof Error
          ? analysisError.message
          : "Analysis is processing. Check again shortly."
      );
    }
  }

  useEffect(() => {
    let active = true;
    async function load() {
      if (!accessToken) return;
      setLoading(true);
      try {
        await reloadResumes();
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Failed to load resumes");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [accessToken, refreshToken]);

  useEffect(() => {
    if (!selectedResumeId) {
      setAnalysis(null);
      return;
    }
    void loadAnalysis(selectedResumeId);
  }, [selectedResumeId]);

  async function handleProcessed(processed: ResumeProcessResponse) {
    setNotice(
      `Resume accepted. Analysis job queued: ${processed.job_id ?? "sync"}. Refresh to retrieve results.`
    );
    await reloadResumes();
    setSelectedResumeId(processed.resume.id);
  }

  if (loading) {
    return (
      <div className="flex min-h-[30vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">Resume Intelligence</h1>
        <p className="text-sm text-slate-400">
          Upload or paste resumes and review AI-structured strengths, weaknesses, and suggestions.
        </p>
      </div>

      {error ? <Alert variant="error">{error}</Alert> : null}
      {notice ? <Alert variant="info">{notice}</Alert> : null}

      <ResumeIngestionPanel onProcessed={handleProcessed} />

      <Card>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Resume Records</h3>
          <Button variant="ghost" onClick={() => void reloadResumes()}>
            Refresh
          </Button>
        </div>
        <div className="mt-4 space-y-2">
          {resumes.length === 0 ? (
            <p className="text-sm text-slate-400">No resumes yet.</p>
          ) : (
            resumes.map((resume) => (
              <button
                key={resume.id}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  selectedResumeId === resume.id
                    ? "border-brand-500 bg-brand-500/10"
                    : "border-slate-700 bg-slate-900/55 hover:border-slate-500"
                }`}
                onClick={() => setSelectedResumeId(resume.id)}
              >
                <p className="text-sm font-medium text-slate-100">{resume.file_name ?? "Pasted resume"}</p>
                <p className="text-xs text-slate-400">
                  {resume.parse_status} · {formatDateTime(resume.created_at)}
                </p>
              </button>
            ))
          )}
        </div>
      </Card>

      <ResumeAnalysisCard analysis={analysis} />
    </div>
  );
}

