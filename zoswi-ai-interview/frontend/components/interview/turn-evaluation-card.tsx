import { Card } from "@/components/ui/card";
import type { InterviewRespondResponse } from "@/types/api";

export function TurnEvaluationCard({
  response
}: {
  response: InterviewRespondResponse | null;
}) {
  if (!response) {
    return (
      <Card>
        <h4 className="text-sm font-semibold text-slate-200">Turn Evaluation</h4>
        <p className="mt-2 text-sm text-slate-400">Submit an answer to receive structured scoring feedback.</p>
      </Card>
    );
  }

  return (
    <Card>
      <h4 className="text-sm font-semibold text-slate-100">Last Turn Evaluation</h4>
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-300">
        <p>Overall: {response.evaluation.score_overall.toFixed(1)}</p>
        <p>Communication: {response.evaluation.score_communication.toFixed(1)}</p>
        <p>Technical: {response.evaluation.score_technical.toFixed(1)}</p>
        <p>Confidence: {response.evaluation.score_confidence.toFixed(1)}</p>
      </div>
      <p className="mt-3 text-sm text-slate-300">{response.evaluation.feedback}</p>
      {response.evaluation.strengths.length > 0 ? (
        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-300">Strengths</p>
          <p className="mt-1 text-xs text-slate-300">{response.evaluation.strengths.join(" | ")}</p>
        </div>
      ) : null}
      {response.evaluation.weaknesses.length > 0 ? (
        <div className="mt-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-rose-300">Weaknesses</p>
          <p className="mt-1 text-xs text-slate-300">{response.evaluation.weaknesses.join(" | ")}</p>
        </div>
      ) : null}
      {response.evaluation.next_step_guidance ? (
        <p className="mt-2 text-xs text-brand-100">
          Next-step guidance: {response.evaluation.next_step_guidance}
        </p>
      ) : null}
    </Card>
  );
}
