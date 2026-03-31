"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/lib/auth/auth-context";

const links = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/recent-chats", label: "Recent Chats" },
  { href: "/dashboard/recent-scores", label: "Recent Scores" },
  { href: "/dashboard/resume", label: "Resume" },
  { href: "/dashboard/interview", label: "Interview" },
  { href: "/dashboard/careers", label: "Careers" },
  { href: "/dashboard/ai-workspace", label: "AI Workspace" },
  { href: "/dashboard/coding-room", label: "Coding Room" },
  { href: "/dashboard/immigration-updates", label: "Immigration" },
  { href: "/dashboard/history", label: "History" },
  { href: "/dashboard/settings", label: "Settings" }
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const isInterviewRoom = pathname.startsWith("/dashboard/interview/");

  if (isInterviewRoom) {
    return (
      <div className="h-screen bg-surface text-slate-100">
        <main className="h-full">{children}</main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface text-slate-100">
      <div className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-6 px-4 py-6 md:grid-cols-[240px_1fr]">
        <aside className="rounded-2xl border border-slate-800 bg-card/90 p-4 shadow-soft">
          <Link href="/dashboard" className="mb-6 block text-lg font-bold tracking-tight text-white">
            ZoSwi
          </Link>
          <nav className="space-y-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "block rounded-lg px-3 py-2 text-sm font-medium transition",
                  pathname === link.href || pathname.startsWith(`${link.href}/`)
                    ? "bg-brand-500/20 text-brand-100"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="mt-8 rounded-xl border border-slate-700/80 bg-slate-900/60 p-3 text-sm text-slate-300">
            <p className="font-semibold text-white">{user?.full_name ?? "Candidate"}</p>
            <p className="mt-1 text-xs uppercase tracking-wide text-slate-400">{user?.role}</p>
            <Button
              variant="ghost"
              className="mt-3 w-full justify-start px-2"
              onClick={() => {
                logout();
                router.replace("/login");
              }}
            >
              Log out
            </Button>
          </div>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}
