"use client";

import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variantMap: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-400 text-surface hover:bg-brand-300 focus-visible:ring-brand-300 disabled:bg-brand-800 disabled:text-brand-100",
  secondary:
    "bg-slate-200 text-slate-900 hover:bg-slate-100 focus-visible:ring-slate-400 disabled:bg-slate-300 disabled:text-slate-600",
  ghost:
    "bg-transparent text-slate-100 hover:bg-slate-800 focus-visible:ring-slate-500 disabled:text-slate-500",
  danger:
    "bg-rose-500 text-white hover:bg-rose-400 focus-visible:ring-rose-300 disabled:bg-rose-800 disabled:text-rose-200"
};

export function Button({ className, variant = "primary", type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
        variantMap[variant],
        className
      )}
      {...props}
    />
  );
}

