import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { ResumeAnalysis } from "@/types/api";

type ResumeAnalysisCardProps = {
  analysis: ResumeAnalysis | null;
};

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-200">{title}</h4>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No items yet.</p>
      ) : (
        <ul className="mt-2 space-y-1 text-sm text-slate-300">
          {items.map((item) => (
            <li key={item} className="rounded-md bg-slate-900/55 px-2 py-1">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ResumeAnalysisCard({ analysis }: ResumeAnalysisCardProps) {
  if (!analysis) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-white">Resume Analysis</h3>
        <p className="mt-2 text-sm text-slate-400">Run a resume analysis to view strengths and recommendations.</p>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-white">Resume Analysis</h3>
        <Badge>
          {analysis.model_name} · {analysis.analysis_version}
        </Badge>
      </div>
      <p className="mt-3 rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-sm text-slate-300">
        {analysis.summary}
      </p>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <ListBlock title="Extracted Skills" items={analysis.extracted_skills} />
        <ListBlock title="Strengths" items={analysis.strengths} />
        <ListBlock title="Weaknesses" items={analysis.weaknesses} />
        <ListBlock title="Suggestions" items={analysis.suggestions} />
      </div>
    </Card>
  );
}

