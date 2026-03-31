"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";
import { getInterviewSummary, listInterviewSessions } from "@/services/interview-service";
import type { InterviewSession, InterviewSummary } from "@/types/api";
import { formatDateTime } from "@/lib/utils/date";

export default function DashboardHistoryPage() {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [summaries, setSummaries] = useState<Record<string, InterviewSummary>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      if (!accessToken) return;
      setLoading(true);
      try {
        const sessionData = await listInterviewSessions({
          accessToken,
          refreshToken,
          onTokenRefresh: applyRefreshedTokens
        });
        if (!active) return;
        setSessions(sessionData);

        const completed = sessionData.filter((item) => item.status === "completed").slice(0, 15);
        const summaryEntries = await Promise.all(
          completed.map(async (session) => {
            try {
              const summary = await getInterviewSummary(
                { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
                session.id
              );
              return [session.id, summary] as const;
            } catch {
              return null;
            }
          })
        );
        if (!active) return;
        const nextSummaryMap: Record<string, InterviewSummary> = {};
        summaryEntries.forEach((entry) => {
          if (!entry) return;
          nextSummaryMap[entry[0]] = entry[1];
        });
        setSummaries(nextSummaryMap);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Failed to load history");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [accessToken, refreshToken]);

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
        <h1 className="text-2xl font-semibold text-white">Interview History</h1>
        <p className="text-sm text-slate-400">Review prior sessions and drill into score summaries.</p>
      </div>
      {error ? <Alert variant="error">{error}</Alert> : null}
      <Card>
        <div className="space-y-3">
          {sessions.length === 0 ? (
            <p className="text-sm text-slate-400">No history yet.</p>
          ) : (
            sessions.map((session) => {
              const summary = summaries[session.id];
              return (
                <Link
                  key={session.id}
                  href={`/dashboard/interview/${session.id}`}
                  className="block rounded-lg border border-slate-700 bg-slate-900/55 p-3 transition hover:border-brand-500/50"
                >
                  <p className="text-sm font-medium text-slate-100">{session.role_target}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    {session.session_mode} · {session.status} · {formatDateTime(session.created_at)}
                  </p>
                  {summary ? (
                    <p className="mt-1 text-xs text-brand-100">
                      Final score {summary.final_score.toFixed(1)} · {summary.recommendation}
                    </p>
                  ) : null}
                </Link>
              );
            })
          )}
        </div>
      </Card>
    </div>
  );
}

