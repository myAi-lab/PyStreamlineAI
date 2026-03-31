import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

type AlertVariant = "info" | "error" | "success";

const variants: Record<AlertVariant, string> = {
  info: "border-brand-500/50 bg-brand-600/10 text-brand-100",
  error: "border-rose-500/50 bg-rose-500/10 text-rose-100",
  success: "border-emerald-500/50 bg-emerald-500/10 text-emerald-100"
};

export function Alert({
  className,
  variant = "info",
  ...props
}: HTMLAttributes<HTMLDivElement> & { variant?: AlertVariant }) {
  return (
    <div
      className={cn("rounded-xl border px-4 py-3 text-sm", variants[variant], className)}
      {...props}
    />
  );
}

