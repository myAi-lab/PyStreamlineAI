import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full border border-brand-500/70 bg-brand-500/20 px-2.5 py-1 text-xs font-semibold text-brand-100",
        className
      )}
      {...props}
    />
  );
}

