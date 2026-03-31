"use client";

import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils/cn";

type VideoPanelProps = {
  stream: MediaStream | null;
  joined: boolean;
  micOn: boolean;
  cameraOn: boolean;
  className?: string;
  tileMode?: boolean;
};

export function VideoPanel({
  stream,
  joined,
  micOn,
  cameraOn,
  className,
  tileMode = false
}: VideoPanelProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!videoRef.current) return;
    videoRef.current.srcObject = stream;
  }, [stream]);

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border border-slate-600/80 bg-black shadow-[0_24px_70px_rgba(2,6,23,0.65)]",
        tileMode ? "aspect-square w-full" : "h-[300px] w-full",
        className
      )}
    >
      <video
        ref={videoRef}
        className={cn("h-full w-full scale-x-[-1] object-cover", !joined && "opacity-70")}
        autoPlay
        muted
        playsInline
      />

      {!joined ? (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/88 p-4 text-center text-xs text-slate-300">
          Enable camera preview to appear in the interview room.
        </div>
      ) : null}

      <div className="absolute inset-x-0 top-0 flex items-center justify-between px-3 py-2">
        <span className="rounded-lg bg-slate-900/70 px-2 py-1 text-[11px] text-white">
          {micOn ? "Mic on" : "Mic muted"}
        </span>
        <span className="rounded-lg bg-slate-900/70 px-2 py-1 text-[11px] text-white">
          {cameraOn ? "Cam on" : "Cam off"}
        </span>
      </div>

      <div className="absolute bottom-2 left-2 rounded-lg bg-slate-900/75 px-2 py-1 text-[11px] font-medium text-white">
        You
      </div>
    </div>
  );
}
