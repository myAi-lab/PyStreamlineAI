"use client";

import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";
import { formatDateTime } from "@/lib/utils/date";
import { listRecentScores } from "@/services/workspace-service";
import type { RecentScoreItem } from "@/types/api";

export default function DashboardRecentScoresPage() {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [scores, setScores] = useState<RecentScoreItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void (async () => {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        const data = await listRecentScores({
          accessToken,
          refreshToken,
          onTokenRefresh: applyRefreshedTokens
        });
        if (!active) return;
        setScores(data);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Unable to load recent scores");
      } finally {
        if (active) setLoading(false);
      }
    })();
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
        <h1 className="text-2xl font-semibold text-white">Recent Scores</h1>
        <p className="text-sm text-slate-400">Resume and interview score timeline for recruiter readiness tracking.</p>
      </div>
      {error ? <Alert variant="error">{error}</Alert> : null}
      <Card>
        <div className="space-y-3">
          {scores.length === 0 ? (
            <p className="text-sm text-slate-400">No score history available yet.</p>
          ) : (
            scores.map((item) => (
              <div key={item.entity_id} className="rounded-lg border border-slate-700 bg-slate-900/55 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{item.title}</p>
                    <p className="mt-1 text-xs uppercase tracking-wide text-slate-400">{item.kind.replace("_", " ")}</p>
                  </div>
                  <p className="text-sm font-semibold text-brand-100">{item.score.toFixed(1)}%</p>
                </div>
                <p className="mt-2 text-sm text-slate-300">{item.summary}</p>
                <p className="mt-2 text-[11px] text-slate-500">{formatDateTime(item.created_at)}</p>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
