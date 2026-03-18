"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getClientAccessToken, getRecruiterAccessState, getRecruiterInterviews } from "../../../lib/api";

type InterviewRow = {
  session_id: string;
  candidate_name: string;
  role: string;
  status: string;
  overall_score: number | null;
  recommendation: string | null;
  integrity_flag_count: number;
};

export default function RecruiterQueuePage() {
  const [rows, setRows] = useState<InterviewRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    const token = getClientAccessToken();
    const access = getRecruiterAccessState(token || undefined);
    if (!access.allowed) {
      if (mounted) {
        setRows([]);
        setError(access.message || "Recruiter access is restricted.");
      }
      return () => {
        mounted = false;
      };
    }
    getRecruiterInterviews({}, token || undefined)
      .then((payload) => {
        if (mounted) {
          setRows(Array.isArray(payload) ? (payload as InterviewRow[]) : []);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Unable to load interview queue.");
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <main className="relative mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <section className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-[var(--font-display)] text-3xl font-semibold text-slate-100">Recruiter - Interview Queue</h1>
          <Link href="/recruiter" className="rounded-lg border border-white/20 px-3 py-2 text-sm text-slate-200">
            Candidate List
          </Link>
        </div>
        {error ? <p className="mt-4 rounded-lg bg-rose-500/20 px-3 py-2 text-sm text-rose-100">{error}</p> : null}
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm text-slate-200">
            <thead>
              <tr className="border-b border-white/10">
                <th className="py-2 pr-3">Candidate</th>
                <th className="py-2 pr-3">Role</th>
                <th className="py-2 pr-3">Score</th>
                <th className="py-2 pr-3">Recommendation</th>
                <th className="py-2 pr-3">Integrity Flags</th>
                <th className="py-2 pr-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => (
                <tr key={item.session_id} className="border-b border-white/5">
                  <td className="py-2 pr-3">{item.candidate_name}</td>
                  <td className="py-2 pr-3">{item.role}</td>
                  <td className="py-2 pr-3">{typeof item.overall_score === "number" ? item.overall_score.toFixed(1) : "N/A"}</td>
                  <td className="py-2 pr-3">{item.recommendation || "N/A"}</td>
                  <td className="py-2 pr-3">{item.integrity_flag_count}</td>
                  <td className="py-2 pr-3">
                    <Link href={`/recruiter/interviews/${item.session_id}`} className="text-cyan-200 hover:text-cyan-100">
                      Review
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
