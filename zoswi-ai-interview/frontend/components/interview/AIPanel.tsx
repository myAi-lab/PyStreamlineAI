"use client";

import { cn } from "@/lib/utils/cn";

type AIPanelProps = {
  question: string | null;
  roleTarget: string;
  isSpeaking: boolean;
  stateLabel: string;
};

export function AIPanel({ question, roleTarget, isSpeaking, stateLabel }: AIPanelProps) {
  return (
    <div className="relative h-full overflow-hidden rounded-3xl border border-slate-700/80 bg-gradient-to-b from-slate-900/85 via-slate-900/70 to-slate-950/90">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_28%,rgba(56,189,248,0.26),transparent_44%),radial-gradient(circle_at_52%_92%,rgba(30,64,175,0.2),transparent_38%)]" />

      <div className="relative flex h-full flex-col items-center justify-center px-5 py-8">
        <div className="mb-5 flex items-center gap-2 rounded-full border border-slate-600/80 bg-slate-900/70 px-3 py-1 text-xs text-slate-200">
          <span className={cn("h-2 w-2 rounded-full", isSpeaking ? "animate-pulse bg-emerald-400" : "bg-slate-500")} />
          <span>{isSpeaking ? "AI Buzz speaking" : stateLabel}</span>
          <span className="text-slate-400">|</span>
          <span>{roleTarget}</span>
        </div>

        <div className="relative flex h-[270px] w-[270px] items-center justify-center">
          <span
            className={cn(
              "absolute h-[250px] w-[250px] rounded-full border border-cyan-300/40",
              isSpeaking ? "ai-buzz-ring-fast" : "ai-buzz-ring-slow"
            )}
          />
          <span
            className={cn(
              "absolute h-[210px] w-[210px] rounded-full border border-cyan-200/35",
              isSpeaking ? "ai-buzz-ring-mid" : "ai-buzz-ring-slow"
            )}
          />
          <span
            className={cn(
              "absolute h-[170px] w-[170px] rounded-full border border-cyan-100/30",
              isSpeaking ? "ai-buzz-ring-fast" : "ai-buzz-ring-slow"
            )}
          />
          <span
            className={cn(
              "relative flex h-[130px] w-[130px] items-center justify-center rounded-full bg-cyan-400/18 text-cyan-100 shadow-[0_0_40px_rgba(45,212,191,0.35)]",
              isSpeaking && "ai-buzz-core"
            )}
          >
            AI
          </span>
        </div>

        <div className="mt-5 flex items-end gap-1">
          <span className={cn("h-2 w-1 rounded-full bg-cyan-300/80", isSpeaking && "interview-wave-bar")} />
          <span className={cn("h-4 w-1 rounded-full bg-cyan-300/80", isSpeaking && "interview-wave-bar interview-wave-delay-1")} />
          <span className={cn("h-6 w-1 rounded-full bg-cyan-300/80", isSpeaking && "interview-wave-bar interview-wave-delay-2")} />
          <span className={cn("h-3 w-1 rounded-full bg-cyan-300/80", isSpeaking && "interview-wave-bar interview-wave-delay-3")} />
          <span className={cn("h-5 w-1 rounded-full bg-cyan-300/80", isSpeaking && "interview-wave-bar interview-wave-delay-4")} />
        </div>

        <p className="mt-6 max-w-3xl text-center text-base leading-relaxed text-slate-100">
          {question?.trim()
            ? question.trim()
            : "I will ask one role-specific question at a time and keep this as a focused one-on-one interview."}
        </p>

        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">ZoSwi AI Buzz Interviewer</p>
      </div>
    </div>
  );
}
