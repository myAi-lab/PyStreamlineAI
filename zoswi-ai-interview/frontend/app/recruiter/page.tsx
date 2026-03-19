"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getClientAccessToken, getRecruiterAccessState, getRecruiterCandidates } from "../../lib/api";

type CandidateRow = {
  candidate_name: string;
  role: string;
  latest_session_id: string;
  latest_overall_score: number | null;
  status: string;
};

export default function RecruiterCandidateListPage() {
  const [items, setItems] = useState<CandidateRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    const token = getClientAccessToken();
    const access = getRecruiterAccessState(token || undefined);
    if (!access.allowed) {
      if (mounted) {
        setItems([]);
        setError(access.message || "Recruiter access is restricted.");
      }
      return () => {
        mounted = false;
      };
    }
    getRecruiterCandidates({}, token || undefined)
      .then((rows) => {
        if (mounted) {
          setItems(Array.isArray(rows) ? (rows as CandidateRow[]) : []);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Unable to load candidates.");
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
          <h1 className="font-[var(--font-display)] text-3xl font-semibold text-slate-100">Recruiter - Candidate List</h1>
          <div className="flex flex-wrap gap-2">
            <Link href="/recruiter/queue" className="rounded-lg border border-white/20 px-3 py-2 text-sm text-slate-200">
              Interview Queue
            </Link>
            <Link href="/recruiter/exports" className="rounded-lg border border-white/20 px-3 py-2 text-sm text-slate-200">
              Export Results
            </Link>
          </div>
        </div>
        {error ? <p className="mt-4 rounded-lg bg-rose-500/20 px-3 py-2 text-sm text-rose-100">{error}</p> : null}
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm text-slate-200">
            <thead>
              <tr className="border-b border-white/10">
                <th className="py-2 pr-3">Candidate</th>
                <th className="py-2 pr-3">Role</th>
                <th className="py-2 pr-3">Score</th>
                <th className="py-2 pr-3">Status</th>
                <th className="py-2 pr-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.latest_session_id} className="border-b border-white/5">
                  <td className="py-2 pr-3">{item.candidate_name}</td>
                  <td className="py-2 pr-3">{item.role}</td>
                  <td className="py-2 pr-3">{typeof item.latest_overall_score === "number" ? item.latest_overall_score.toFixed(1) : "N/A"}</td>
                  <td className="py-2 pr-3">{item.status}</td>
                  <td className="py-2 pr-3">
                    <Link href={`/recruiter/interviews/${item.latest_session_id}`} className="text-cyan-200 hover:text-cyan-100">
                      Open
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
