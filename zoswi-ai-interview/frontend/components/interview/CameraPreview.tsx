"use client";

import { useEffect, useRef } from "react";

type CameraPreviewProps = {
  stream: MediaStream | null;
  enabled: boolean;
  warning: string | null;
  disabled: boolean;
  onToggle: (enabled: boolean) => void;
};

export function CameraPreview({
  stream,
  enabled,
  warning,
  disabled,
  onToggle
}: CameraPreviewProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!videoRef.current) {
      return;
    }
    videoRef.current.srcObject = stream;
  }, [stream]);

  function renderSwitch(
    label: string,
    checked: boolean,
    isDisabled: boolean,
    onChange: (enabled: boolean) => void
  ) {
    return (
      <label
        className={`inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide ${
          isDisabled ? "cursor-not-allowed text-slate-500" : "cursor-pointer text-slate-300"
        }`}
      >
        <span>{label}</span>
        <span>{checked ? "On" : "Off"}</span>
        <input
          type="checkbox"
          className="sr-only"
          checked={checked}
          disabled={isDisabled}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span
          className={`relative h-6 w-11 rounded-full border transition ${
            checked ? "border-cyan-300/60 bg-cyan-500/55" : "border-white/20 bg-slate-700/80"
          } ${isDisabled ? "opacity-55" : ""}`}
        >
          <span
            className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
              checked ? "translate-x-5" : ""
            }`}
          />
        </span>
      </label>
    );
  }

  return (
    <section className="panel p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Camera Preview</h3>
        <div className="flex flex-wrap items-center gap-3">{renderSwitch("Camera", enabled, disabled, onToggle)}</div>
      </div>
      <div className="relative mt-3 overflow-hidden rounded-xl border border-white/10 bg-slate-900">
        <video ref={videoRef} autoPlay muted playsInline className="h-56 w-full object-cover sm:h-64" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-slate-950/80 to-transparent" />
      </div>
      {!enabled ? <p className="mt-3 text-sm text-slate-300">Camera is off. Keeping it on improves trust and outcomes.</p> : null}
      {enabled && !stream ? <p className="mt-3 text-sm text-slate-300">Allow camera permission to start premium monitoring.</p> : null}
      {disabled ? <p className="mt-2 text-xs text-slate-500">Camera control is locked while the interview is live.</p> : null}
      {warning ? <p className="mt-3 rounded-lg border border-rose-300/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">{warning}</p> : null}
    </section>
  );
}
