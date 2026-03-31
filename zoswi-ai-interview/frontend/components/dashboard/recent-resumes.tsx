import { Card } from "@/components/ui/card";
import type { Resume } from "@/types/api";
import { formatDateTime } from "@/lib/utils/date";

export function RecentResumes({ resumes }: { resumes: Resume[] }) {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-white">Recent Resume Runs</h3>
      <div className="mt-4 space-y-3">
        {resumes.length === 0 ? (
          <p className="text-sm text-slate-400">No resumes uploaded yet.</p>
        ) : (
          resumes.slice(0, 5).map((resume) => (
            <div key={resume.id} className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
              <p className="text-sm font-medium text-slate-200">{resume.file_name ?? "Pasted resume"}</p>
              <p className="text-xs text-slate-400">
                Status: {resume.parse_status} · {formatDateTime(resume.created_at)}
              </p>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

