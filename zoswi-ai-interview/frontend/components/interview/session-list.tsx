import Link from "next/link";

import { Card } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils/date";
import type { InterviewSession } from "@/types/api";

export function SessionList({ sessions }: { sessions: InterviewSession[] }) {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-white">Session History</h3>
      <div className="mt-4 space-y-3">
        {sessions.length === 0 ? (
          <p className="text-sm text-slate-400">No sessions created yet.</p>
        ) : (
          sessions.map((session) => (
            <Link
              key={session.id}
              href={`/dashboard/interview/${session.id}`}
              className="block rounded-lg border border-slate-700 bg-slate-900/60 p-3 transition hover:border-brand-500/50"
            >
              <p className="text-sm font-medium text-slate-100">{session.role_target}</p>
              <p className="mt-1 text-xs text-slate-400">
                {session.session_mode} · {session.status} · {formatDateTime(session.created_at)}
              </p>
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}
