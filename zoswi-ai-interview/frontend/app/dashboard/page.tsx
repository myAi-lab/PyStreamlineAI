"use client";

import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { OverviewCards } from "@/components/dashboard/overview-cards";
import { RecentInterviews } from "@/components/dashboard/recent-interviews";
import { RecentResumes } from "@/components/dashboard/recent-resumes";
import { useAuth } from "@/lib/auth/auth-context";
import { listInterviewSessions } from "@/services/interview-service";
import { fetchUsage } from "@/services/platform-service";
import { listResumes } from "@/services/resume-service";
import { listWorkspaceSessions } from "@/services/workspace-service";
import type { InterviewSession, Resume, Usage } from "@/types/api";

export default function DashboardHomePage() {
  const { accessToken, refreshToken, applyRefreshedTokens, user } = useAuth();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [workspaceCount, setWorkspaceCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        const [usageData, resumeData, sessionData, workspaceSessions] = await Promise.all([
          fetchUsage({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens }),
          listResumes({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens }),
          listInterviewSessions({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens }),
          listWorkspaceSessions({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens })
        ]);
        if (!active) return;
        setUsage(usageData);
        setResumes(resumeData);
        setSessions(sessionData);
        setWorkspaceCount(workspaceSessions.length);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Could not load dashboard");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();

    return () => {
      active = false;
    };
  }, [accessToken, applyRefreshedTokens, refreshToken]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <Alert variant="error">{error}</Alert>;
  }

  const cards = [
    { label: "Chats", value: workspaceCount, note: "Workspace sessions" },
    { label: "Resumes", value: usage?.total_resumes ?? 0, note: "Uploaded or pasted resumes" },
    { label: "Analyses", value: usage?.total_resume_analyses ?? 0, note: "AI resume intelligence runs" },
    { label: "Sessions", value: usage?.total_sessions ?? 0, note: "Interview sessions created" },
    { label: "Completed", value: usage?.completed_sessions ?? 0, note: "Completed interview sessions" }
  ];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">Welcome, {user?.full_name}</h1>
        <p className="mt-1 text-sm text-slate-400">
          Track career intelligence activity and interviewer readiness signals.
        </p>
      </div>
      <OverviewCards items={cards} />
      <div className="grid gap-4 lg:grid-cols-2">
        <RecentResumes resumes={resumes} />
        <RecentInterviews sessions={sessions} />
      </div>
    </div>
  );
}
