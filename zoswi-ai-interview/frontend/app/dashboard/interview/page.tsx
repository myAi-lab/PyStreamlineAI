"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { SessionCreateForm } from "@/components/interview/session-create-form";
import { SessionList } from "@/components/interview/session-list";
import { useAuth } from "@/lib/auth/auth-context";
import { createLiveInterviewLaunchUrl, listInterviewSessions } from "@/services/interview-service";
import type { InterviewMode, InterviewSession } from "@/types/api";

export default function DashboardInterviewPage() {
  const { accessToken, refreshToken, applyRefreshedTokens, user } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [launchError, setLaunchError] = useState<string | null>(null);
  const [launching, setLaunching] = useState(false);
  const [candidateName, setCandidateName] = useState("");
  const [targetRole, setTargetRole] = useState("Software Engineer");
  const [requirementType, setRequirementType] = useState<InterviewMode>("mixed");
  const [launchUrl, setLaunchUrl] = useState<string | null>(null);

  async function reloadSessions() {
    if (!accessToken) return;
    const data = await listInterviewSessions({
      accessToken,
      refreshToken,
      onTokenRefresh: applyRefreshedTokens
    });
    setSessions(data);
  }

  useEffect(() => {
    let active = true;
    async function load() {
      if (!accessToken) return;
      setLoading(true);
      try {
        const data = await listInterviewSessions({
          accessToken,
          refreshToken,
          onTokenRefresh: applyRefreshedTokens
        });
        if (!active) return;
        setSessions(data);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Failed to load sessions");
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
    if (!candidateName && user?.full_name) {
      setCandidateName(user.full_name);
    }
  }, [user?.full_name]);

  async function handleGenerateLaunchUrl() {
    if (!accessToken) return;
    setLaunchError(null);
    setLaunching(true);
    try {
      const result = await createLiveInterviewLaunchUrl(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {
          candidate_name: candidateName.trim(),
          target_role: targetRole.trim(),
          requirement_type: requirementType
        }
      );
      setLaunchUrl(result.launch_url);
    } catch (launchUrlError) {
      setLaunchError(launchUrlError instanceof Error ? launchUrlError.message : "Could not generate launch URL");
    } finally {
      setLaunching(false);
    }
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
        <h1 className="text-2xl font-semibold text-white">Interview Workspace</h1>
        <p className="text-sm text-slate-400">Create, run, and monitor structured AI interviews.</p>
      </div>
      {error ? <Alert variant="error">{error}</Alert> : null}
      {launchError ? <Alert variant="error">{launchError}</Alert> : null}

      <Card>
        <h3 className="text-lg font-semibold text-white">Live Interview Launch</h3>
        <p className="mt-1 text-sm text-slate-400">
          Generate a signed launch URL for the live interview room, similar to the previous Streamlit flow.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <label className="space-y-1">
            <span className="text-sm text-slate-300">Candidate Name</span>
            <Input
              value={candidateName}
              onChange={(event) => setCandidateName(event.target.value)}
              placeholder="Candidate full name"
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-300">Target Role</span>
            <Input value={targetRole} onChange={(event) => setTargetRole(event.target.value)} placeholder="Target role" />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-300">Interview Type</span>
            <Select
              value={requirementType}
              onChange={(event) => setRequirementType(event.target.value as InterviewMode)}
            >
              <option value="mixed">Mixed</option>
              <option value="technical">Technical</option>
              <option value="behavioral">Behavioral</option>
            </Select>
          </label>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Button
            onClick={() => void handleGenerateLaunchUrl()}
            disabled={launching || !candidateName.trim() || !targetRole.trim()}
          >
            {launching ? "Generating..." : "Generate Launch URL"}
          </Button>
          {launchUrl ? (
            <a
              href={launchUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex rounded-lg border border-brand-500/40 bg-brand-500/10 px-3 py-2 text-sm font-medium text-brand-100 transition hover:border-brand-400"
            >
              Open Live Interview
            </a>
          ) : null}
        </div>
        {launchUrl ? (
          <p className="mt-3 break-all rounded-lg border border-slate-700 bg-slate-900/50 p-2 text-xs text-slate-300">
            {launchUrl}
          </p>
        ) : null}
      </Card>

      <SessionCreateForm
        onCreated={(session) => {
          void reloadSessions();
          router.push(`/dashboard/interview/${session.id}`);
        }}
      />
      <SessionList sessions={sessions} />
    </div>
  );
}
