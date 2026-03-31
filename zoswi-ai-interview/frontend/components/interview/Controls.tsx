"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

type ControlsProps = {
  micEnabled: boolean;
  cameraEnabled: boolean;
  listening: boolean;
  canStartInterview: boolean;
  disabled: boolean;
  hasQuestion: boolean;
  autoVoice: boolean;
  onToggleMicEnabled: () => void;
  onToggleCameraEnabled: () => void;
  onLeave: () => void;
  onStartInterview: () => void;
  onToggleListening: () => void;
  onReplayQuestion: () => void;
  onToggleAutoVoice: () => void;
  condensed?: boolean;
};

export function Controls({
  micEnabled,
  cameraEnabled,
  listening,
  canStartInterview,
  disabled,
  hasQuestion,
  autoVoice,
  onToggleMicEnabled,
  onToggleCameraEnabled,
  onLeave,
  onStartInterview,
  onToggleListening,
  onReplayQuestion,
  onToggleAutoVoice,
  condensed = false
}: ControlsProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-700/80 bg-slate-900/80 p-3 shadow-[0_12px_38px_rgba(2,6,23,0.7)] backdrop-blur",
        condensed && "min-w-[310px]"
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={onToggleMicEnabled} variant="secondary" disabled={disabled}>
          {micEnabled ? "Mute" : "Unmute"}
        </Button>
        <Button onClick={onToggleCameraEnabled} variant="secondary" disabled={disabled}>
          {cameraEnabled ? "Cam Off" : "Cam On"}
        </Button>

        <Button onClick={onStartInterview} disabled={!canStartInterview || disabled}>
          Start Interview
        </Button>

        <Button onClick={onLeave} variant="danger">
          End Call
        </Button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Button onClick={onToggleListening} disabled={disabled || !micEnabled} variant="ghost" className="px-3 py-1.5 text-xs">
          {listening ? "Listening On" : "Listening Off"}
        </Button>
        <Button onClick={onReplayQuestion} disabled={!hasQuestion} variant="ghost" className="px-3 py-1.5 text-xs">
          Replay Question
        </Button>
        <Button onClick={onToggleAutoVoice} variant="ghost" className="px-3 py-1.5 text-xs">
          {autoVoice ? "AI Voice Auto" : "AI Voice Manual"}
        </Button>
      </div>
    </div>
  );
}
