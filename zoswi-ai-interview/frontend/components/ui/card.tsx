import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-700 bg-card/85 p-5 shadow-soft backdrop-blur-sm",
        className
      )}
      {...props}
    />
  );
}

