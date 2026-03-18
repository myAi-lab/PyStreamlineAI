"use client";

import Link from "next/link";
import { useState } from "react";

import { getClientAccessToken, getRecruiterAccessState } from "../../../lib/api";

function getApiBase() {
  return String(process.env.NEXT_PUBLIC_API_BASE_URL || "").trim().replace(/\/+$/, "");
}

export default function RecruiterExportPage() {
  const [status, setStatus] = useState("");

  async function downloadExport() {
    const base = getApiBase();
    const token = getClientAccessToken();
    const access = getRecruiterAccessState(token || undefined);
    if (!access.allowed) {
      setStatus(access.message || "Recruiter access is restricted.");
      return;
    }
    if (!base) {
      setStatus("Missing NEXT_PUBLIC_API_BASE_URL.");
      return;
    }
    try {
      setStatus("Preparing export...");
      const response = await fetch(`${base}/recruiter/exports`, {
        method: "GET",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        cache: "no-store"
      });
      if (!response.ok) {
        throw new Error(`Export failed (${response.status}).`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "zoswi_interviews_export.csv";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setStatus("Export downloaded.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Export failed.");
    }
  }

  return (
    <main className="relative mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <section className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-[var(--font-display)] text-3xl font-semibold text-slate-100">Export Results</h1>
          <Link href="/recruiter" className="rounded-lg border border-white/20 px-3 py-2 text-sm text-slate-200">
            Candidate List
          </Link>
        </div>
        <p className="mt-3 text-sm text-slate-300">
          Generate and download interview reports in CSV format from recruiter APIs.
        </p>
        <button
          onClick={downloadExport}
          className="mt-4 rounded-lg border border-cyan-300/30 bg-cyan-400/90 px-4 py-2 text-sm font-semibold text-slate-900"
        >
          Download CSV Export
        </button>
        {status ? <p className="mt-3 text-sm text-slate-300">{status}</p> : null}
      </section>
    </main>
  );
}
