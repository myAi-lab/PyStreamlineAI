"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";
import { formatDateTime } from "@/lib/utils/date";
import { createWorkspaceSession, listWorkspaceSessions } from "@/services/workspace-service";
import type { WorkspaceSession } from "@/types/api";

export default function DashboardRecentChatsPage() {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [sessions, setSessions] = useState<WorkspaceSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!accessToken) return;
    const data = await listWorkspaceSessions({
      accessToken,
      refreshToken,
      onTokenRefresh: applyRefreshedTokens
    });
    setSessions(data);
  }

  useEffect(() => {
    let active = true;
    void (async () => {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        await load();
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Unable to load chat history");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, refreshToken]);

  async function handleCreate() {
    if (!accessToken) return;
    setCreating(true);
    setError(null);
    try {
      await createWorkspaceSession(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {}
      );
      await load();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create chat");
    } finally {
      setCreating(false);
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
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Recent Chats</h1>
          <p className="text-sm text-slate-400">Persistent ZoSwi workspace sessions with full conversation context.</p>
        </div>
        <Button onClick={() => void handleCreate()} disabled={creating}>
          {creating ? "Creating..." : "New Chat"}
        </Button>
      </div>
      {error ? <Alert variant="error">{error}</Alert> : null}
      <Card>
        <div className="space-y-3">
          {sessions.length === 0 ? (
            <p className="text-sm text-slate-400">No chat sessions yet.</p>
          ) : (
            sessions.map((session) => (
              <Link
                key={session.id}
                href={`/dashboard/ai-workspace?session=${session.id}`}
                className="block rounded-lg border border-slate-700 bg-slate-900/55 p-3 transition hover:border-brand-500/60"
              >
                <p className="text-sm font-semibold text-slate-100">{session.title}</p>
                <p className="mt-1 text-xs text-slate-400">{session.last_message_preview ?? "No messages yet"}</p>
                <p className="mt-2 text-[11px] text-slate-500">
                  {session.message_count} messages | Updated {formatDateTime(session.updated_at)}
                </p>
              </Link>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
