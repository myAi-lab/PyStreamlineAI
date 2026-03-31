"use client";

import { useParams } from "next/navigation";

import { InterviewChat } from "@/components/interview/interview-chat";

export default function InterviewSessionPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;

  return (
    <div className="h-full">
      <InterviewChat sessionId={sessionId} fullScreen />
    </div>
  );
}
