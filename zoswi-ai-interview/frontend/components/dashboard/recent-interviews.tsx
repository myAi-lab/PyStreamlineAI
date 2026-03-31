import Link from "next/link";

import { Card } from "@/components/ui/card";
import type { InterviewSession } from "@/types/api";
import { formatDateTime } from "@/lib/utils/date";

export function RecentInterviews({ sessions }: { sessions: InterviewSession[] }) {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-white">Recent Interview Sessions</h3>
      <div className="mt-4 space-y-3">
        {sessions.length === 0 ? (
          <p className="text-sm text-slate-400">No interview sessions yet.</p>
        ) : (
          sessions.slice(0, 5).map((session) => (
            <Link
              key={session.id}
              href={`/dashboard/interview/${session.id}`}
              className="block rounded-lg border border-slate-700 bg-slate-900/60 p-3 transition hover:border-brand-500/60"
            >
              <p className="text-sm font-medium text-slate-200">
                {session.role_target} · {session.session_mode}
              </p>
              <p className="text-xs text-slate-400">
                Status: {session.status} · {formatDateTime(session.created_at)}
              </p>
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}

