"use client";

import { FormEvent, startTransition, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";
import { createInterviewSession } from "@/services/interview-service";
import type { InterviewMode, InterviewSession } from "@/types/api";

export function SessionCreateForm({
  onCreated
}: {
  onCreated: (session: InterviewSession) => void;
}) {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [roleTarget, setRoleTarget] = useState("Senior Backend Engineer");
  const [mode, setMode] = useState<InterviewMode>("mixed");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (roleTarget.trim().length < 2) {
      setError("Role target is required");
      return;
    }
    setPending(true);
    startTransition(async () => {
      try {
        const created = await createInterviewSession(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          { role_target: roleTarget.trim(), session_mode: mode }
        );
        onCreated(created);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Could not create session");
      } finally {
        setPending(false);
      }
    });
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-white">Create Interview Session</h3>
      <form className="mt-4 grid gap-4 md:grid-cols-[1fr_180px_auto]" onSubmit={handleSubmit}>
        <Input value={roleTarget} onChange={(event) => setRoleTarget(event.target.value)} />
        <Select value={mode} onChange={(event) => setMode(event.target.value as InterviewMode)}>
          <option value="mixed">Mixed</option>
          <option value="behavioral">Behavioral</option>
          <option value="technical">Technical</option>
        </Select>
        <Button type="submit" disabled={pending}>
          {pending ? (
            <span className="inline-flex items-center gap-2">
              <Spinner /> Creating
            </span>
          ) : (
            "Create"
          )}
        </Button>
      </form>
      {error ? <Alert variant="error" className="mt-3">{error}</Alert> : null}
    </Card>
  );
}

