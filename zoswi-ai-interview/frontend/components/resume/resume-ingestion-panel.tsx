"use client";

import { FormEvent, startTransition, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { TextArea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth/auth-context";
import { analyzeResumeText, uploadResume } from "@/services/resume-service";
import type { ResumeProcessResponse } from "@/types/api";

type ResumeIngestionPanelProps = {
  onProcessed: (result: ResumeProcessResponse) => void;
};

export function ResumeIngestionPanel({ onProcessed }: ResumeIngestionPanelProps) {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [resumeText, setResumeText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function submitText(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (resumeText.trim().length < 80) {
      setError("Resume text must be at least 80 characters");
      return;
    }
    setPending(true);
    startTransition(async () => {
      try {
        const processed = await analyzeResumeText(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          { raw_text: resumeText.trim(), file_name: "pasted_resume.txt" }
        );
        onProcessed(processed);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Text analysis failed");
      } finally {
        setPending(false);
      }
    });
  }

  function submitFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError("Select a file to upload");
      return;
    }
    setPending(true);
    startTransition(async () => {
      try {
        const processed = await uploadResume(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          file
        );
        onProcessed(processed);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Upload failed");
      } finally {
        setPending(false);
      }
    });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <h3 className="text-lg font-semibold text-white">Paste Resume Text</h3>
        <p className="mt-1 text-sm text-slate-400">
          Paste complete resume content for AI extraction and recommendations.
        </p>
        <form className="mt-4 space-y-3" onSubmit={submitText}>
          <TextArea
            rows={10}
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            placeholder="Paste resume content..."
          />
          <Button type="submit" disabled={pending}>
            {pending ? (
              <span className="inline-flex items-center gap-2">
                <Spinner /> Processing
              </span>
            ) : (
              "Analyze Text"
            )}
          </Button>
        </form>
      </Card>
      <Card>
        <h3 className="text-lg font-semibold text-white">Upload Resume File</h3>
        <p className="mt-1 text-sm text-slate-400">Accepted: PDF, DOC, DOCX, TXT (max 5 MB).</p>
        <form className="mt-4 space-y-3" onSubmit={submitFile}>
          <Input
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <Button type="submit" disabled={pending}>
            {pending ? (
              <span className="inline-flex items-center gap-2">
                <Spinner /> Uploading
              </span>
            ) : (
              "Upload and Analyze"
            )}
          </Button>
        </form>
      </Card>
      {error ? <Alert variant="error" className="lg:col-span-2">{error}</Alert> : null}
    </div>
  );
}

