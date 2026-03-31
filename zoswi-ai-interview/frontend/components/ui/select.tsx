"use client";

import type { SelectHTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export function Select({ className, children, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        "w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm text-slate-100 focus:border-brand-300 focus:outline-none focus:ring-2 focus:ring-brand-700",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}

