"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { TextArea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth/auth-context";
import { formatDateTime } from "@/lib/utils/date";
import {
  createWorkspaceSession,
  getWorkspaceSession,
  listWorkspaceSessions,
  sendWorkspaceMessage,
  updateWorkspaceSession
} from "@/services/workspace-service";
import type { WorkspaceMessage, WorkspaceSession } from "@/types/api";

const starterPrompts = [
  "Summarize my resume strengths for backend platform roles.",
  "Create a concise recruiter outreach message from my profile.",
  "Turn my interview feedback into a 2-week improvement plan."
];

export default function AIWorkspacePage() {
  const searchParams = useSearchParams();
  const requestedSessionId = searchParams.get("session");
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [sessions, setSessions] = useState<WorkspaceSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<WorkspaceMessage[]>([]);
  const [draft, setDraft] = useState(starterPrompts[0]);
  const [titleDraft, setTitleDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const transcriptBottomRef = useRef<HTMLDivElement>(null);

  async function loadSessions() {
    if (!accessToken) return;
    const sessionList = await listWorkspaceSessions({
      accessToken,
      refreshToken,
      onTokenRefresh: applyRefreshedTokens
    });
    setSessions(sessionList);
    if (requestedSessionId && sessionList.some((item) => item.id === requestedSessionId)) {
      setActiveSessionId(requestedSessionId);
      return;
    }
    if (!activeSessionId && sessionList[0]) {
      setActiveSessionId(sessionList[0].id);
    }
    if (!sessionList[0] && accessToken) {
      const created = await createWorkspaceSession(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {}
      );
      setSessions([created]);
      setActiveSessionId(created.id);
    }
  }

  async function loadActiveSession(sessionId: string) {
    if (!accessToken) return;
    const detail = await getWorkspaceSession(
      { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
      sessionId
    );
    setMessages(detail.messages);
    setTitleDraft(detail.session.title);
  }

  useEffect(() => {
    let active = true;
    async function boot() {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        await loadSessions();
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Unable to load workspace");
      } finally {
        if (active) setLoading(false);
      }
    }
    void boot();
    return () => {
      active = false;
    };
  }, [accessToken, refreshToken, requestedSessionId]);

  useEffect(() => {
    if (!activeSessionId) return;
    let active = true;
    void (async () => {
      setError(null);
      try {
        await loadActiveSession(activeSessionId);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Unable to load session");
      }
    })();
    return () => {
      active = false;
    };
  }, [activeSessionId, accessToken, refreshToken]);

  useEffect(() => {
    transcriptBottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  async function handleCreateSession() {
    if (!accessToken) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createWorkspaceSession(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {}
      );
      setSessions((prev) => [created, ...prev]);
      setActiveSessionId(created.id);
      setDraft("");
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create session");
    } finally {
      setCreating(false);
    }
  }

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeSessionId || !accessToken) return;
    const cleanMessage = draft.trim();
    if (!cleanMessage) {
      setError("Message cannot be empty");
      return;
    }
    setSending(true);
    setError(null);
    try {
      const response = await sendWorkspaceMessage(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        { sessionId: activeSessionId, message: cleanMessage }
      );
      setMessages((previous) => [...previous, response.user_message, response.assistant_message]);
      setDraft("");
      setSessions((previous) => {
        const withoutCurrent = previous.filter((item) => item.id !== response.session.id);
        return [response.session, ...withoutCurrent];
      });
      setTitleDraft(response.session.title);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Message failed");
    } finally {
      setSending(false);
    }
  }

  async function handleRename() {
    if (!activeSessionId || !accessToken || !titleDraft.trim()) return;
    setRenaming(true);
    setError(null);
    try {
      const updated = await updateWorkspaceSession(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        activeSessionId,
        titleDraft.trim()
      );
      setSessions((previous) => previous.map((item) => (item.id === updated.id ? updated : item)));
    } catch (renameError) {
      setError(renameError instanceof Error ? renameError.message : "Unable to rename session");
    } finally {
      setRenaming(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">AI Workspace</h1>
        <p className="text-sm text-slate-400">
          Persistent ZoSwi chat sessions with structured AI guidance for resume, interview, and career actions.
        </p>
      </div>
      {error ? <Alert variant="error">{error}</Alert> : null}

      <div className="grid gap-4 xl:grid-cols-[320px_1fr]">
        <Card>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Recent Chats</h3>
            <Button onClick={() => void handleCreateSession()} disabled={creating}>
              {creating ? "Creating..." : "New Chat"}
            </Button>
          </div>
          <div className="mt-4 space-y-2">
            {sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => setActiveSessionId(session.id)}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  session.id === activeSessionId
                    ? "border-brand-500 bg-brand-500/10"
                    : "border-slate-700 bg-slate-900/60 hover:border-slate-500"
                }`}
              >
                <p className="text-sm font-semibold text-slate-100">{session.title}</p>
                <p className="mt-1 text-xs text-slate-400">{session.last_message_preview ?? "No messages yet"}</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  {session.message_count} messages | {formatDateTime(session.updated_at)}
                </p>
              </button>
            ))}
          </div>
        </Card>

        <Card className="flex min-h-[70vh] flex-col">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-700 pb-3">
            <div className="w-full max-w-xl space-y-1">
              <label className="text-xs uppercase tracking-wide text-slate-400">Session title</label>
              <div className="flex gap-2">
                <Input value={titleDraft} onChange={(event) => setTitleDraft(event.target.value)} />
                <Button onClick={() => void handleRename()} disabled={renaming || !titleDraft.trim()}>
                  {renaming ? "Saving..." : "Save"}
                </Button>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {starterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setDraft(prompt)}
                  className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-1.5 text-xs text-slate-200 transition hover:border-brand-400"
                >
                  Use Template
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[92%] rounded-xl border px-4 py-3 text-sm ${
                  message.role === "user"
                    ? "ml-auto border-brand-600/50 bg-brand-500/15 text-slate-100"
                    : "border-slate-700 bg-slate-900/60 text-slate-200"
                }`}
              >
                <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-400">{message.role}</p>
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            ))}
            <div ref={transcriptBottomRef} />
          </div>

          <form className="mt-4 border-t border-slate-700 pt-3" onSubmit={handleSend}>
            <TextArea
              rows={4}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask ZoSwi about resume targeting, interview prep, outreach, or role strategy..."
            />
            <div className="mt-3 flex items-center justify-between">
              <p className="text-xs text-slate-400">
                ZoSwi can make mistakes. Validate important outputs before using them.
              </p>
              <Button type="submit" disabled={sending || !activeSessionId}>
                {sending ? "Sending..." : "Send"}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
