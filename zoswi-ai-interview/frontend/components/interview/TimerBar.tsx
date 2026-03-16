"use client";

type TimerBarProps = {
  secondsLeft: number;
  totalSeconds: number;
};

function formatSeconds(seconds: number) {
  const mins = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const secs = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${mins}:${secs}`;
}

export function TimerBar({ secondsLeft, totalSeconds }: TimerBarProps) {
  const pct = totalSeconds <= 0 ? 0 : Math.max(0, Math.min(100, (secondsLeft / totalSeconds) * 100));
  return (
    <section className="panel p-4">
      <div className="flex items-center justify-between text-sm font-medium text-slate-300">
        <span className="uppercase tracking-wide">Interview Time Left</span>
        <span className={secondsLeft <= 10 ? "font-semibold text-rose-300" : "font-semibold text-cyan-300"}>
          {formatSeconds(secondsLeft)}
        </span>
      </div>
      <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-sky-300 to-emerald-300 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-slate-400">Stay concise and finish before the timer expires.</p>
    </section>
  );
}
