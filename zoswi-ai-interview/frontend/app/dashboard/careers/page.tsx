"use client";

import { FormEvent, useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";
import { formatDateTime } from "@/lib/utils/date";
import { runCareersMatch } from "@/services/careers-service";
import { listResumes } from "@/services/resume-service";
import type { CareersMatchResponse, Resume } from "@/types/api";

const positionTypes = ["Full-Time", "Contract", "W2", "C2C", "Part-Time"];
const visaStatuses = [
  "US Citizen / Green Card",
  "H-1B",
  "F-1 OPT / CPT",
  "L-1",
  "TN",
  "Other visa status"
];

export default function CareersPage() {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>("");
  const [roleQuery, setRoleQuery] = useState("Software Engineer");
  const [location, setLocation] = useState("Remote");
  const [visaStatus, setVisaStatus] = useState(visaStatuses[0]);
  const [sponsorshipRequired, setSponsorshipRequired] = useState(false);
  const [postedWithinDays, setPostedWithinDays] = useState(7);
  const [maxResults, setMaxResults] = useState(8);
  const [selectedPositionTypes, setSelectedPositionTypes] = useState<string[]>(["Full-Time"]);
  const [result, setResult] = useState<CareersMatchResponse | null>(null);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void (async () => {
      if (!accessToken) return;
      setLoadingResumes(true);
      try {
        const data = await listResumes({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens });
        if (!active) return;
        setResumes(data);
        if (data[0]) {
          setSelectedResumeId(data[0].id);
        }
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Unable to load resume context");
      } finally {
        if (active) setLoadingResumes(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, applyRefreshedTokens, refreshToken]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError(null);
    setRunning(true);
    try {
      const response = await runCareersMatch(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {
          role_query: roleQuery.trim(),
          preferred_location: location.trim(),
          visa_status: visaStatus,
          sponsorship_required: sponsorshipRequired,
          selected_position_types: selectedPositionTypes,
          posted_within_days: postedWithinDays,
          max_results: maxResults,
          resume_id: selectedResumeId || undefined
        }
      );
      setResult(response);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Careers matching failed");
    } finally {
      setRunning(false);
    }
  }

  function togglePositionType(value: string) {
    setSelectedPositionTypes((previous) => {
      if (previous.includes(value)) {
        return previous.filter((item) => item !== value);
      }
      return [...previous, value];
    });
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">ZoSwi Careers</h1>
        <p className="text-sm text-slate-400">
          Resume-aware job matching with role relevance, sponsorship signals, and recruiter-ready apply scoring.
        </p>
      </div>

      {error ? <Alert variant="error">{error}</Alert> : null}

      <Card>
        <h3 className="text-lg font-semibold text-white">Career Match Studio</h3>
        {loadingResumes ? (
          <div className="mt-4 inline-flex items-center gap-2 text-sm text-slate-300">
            <Spinner /> Loading resume context...
          </div>
        ) : null}
        <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
          <div className="grid gap-3 md:grid-cols-3">
            <label className="space-y-1">
              <span className="text-sm text-slate-300">Target Role</span>
              <Input value={roleQuery} onChange={(event) => setRoleQuery(event.target.value)} />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-slate-300">Preferred Location</span>
              <Input value={location} onChange={(event) => setLocation(event.target.value)} />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-slate-300">Resume Context</span>
              <Select value={selectedResumeId} onChange={(event) => setSelectedResumeId(event.target.value)}>
                <option value="">Latest resume</option>
                {resumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.file_name ?? "Pasted resume"} ({formatDateTime(resume.created_at)})
                  </option>
                ))}
              </Select>
            </label>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <label className="space-y-1">
              <span className="text-sm text-slate-300">Visa Status</span>
              <Select value={visaStatus} onChange={(event) => setVisaStatus(event.target.value)}>
                {visaStatuses.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </Select>
            </label>
            <label className="space-y-1">
              <span className="text-sm text-slate-300">Posted Within</span>
              <Select
                value={String(postedWithinDays)}
                onChange={(event) => setPostedWithinDays(Number.parseInt(event.target.value, 10))}
              >
                <option value="0">Any time</option>
                <option value="1">Past 24 hours</option>
                <option value="3">Past 3 days</option>
                <option value="7">Past 7 days</option>
                <option value="14">Past 14 days</option>
                <option value="30">Past 30 days</option>
              </Select>
            </label>
            <label className="space-y-1">
              <span className="text-sm text-slate-300">Max Results</span>
              <Select value={String(maxResults)} onChange={(event) => setMaxResults(Number.parseInt(event.target.value, 10))}>
                <option value="5">5</option>
                <option value="8">8</option>
                <option value="10">10</option>
                <option value="12">12</option>
                <option value="15">15</option>
              </Select>
            </label>
          </div>

          <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
            <p className="text-sm font-medium text-slate-200">Position Type Filters</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {positionTypes.map((item) => {
                const selected = selectedPositionTypes.includes(item);
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => togglePositionType(item)}
                    className={`rounded-full border px-3 py-1 text-xs transition ${
                      selected
                        ? "border-brand-500 bg-brand-500/20 text-brand-100"
                        : "border-slate-600 bg-slate-900 text-slate-300 hover:border-slate-400"
                    }`}
                  >
                    {item}
                  </button>
                );
              })}
            </div>
            <label className="mt-3 flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={sponsorshipRequired}
                onChange={(event) => setSponsorshipRequired(event.target.checked)}
                className="h-4 w-4 rounded border-slate-600 bg-slate-900"
              />
              Need employer visa sponsorship
            </label>
          </div>

          <Button type="submit" disabled={running}>
            {running ? "Running match pipeline..." : "Find My Best Matches"}
          </Button>
        </form>
      </Card>

      {result ? (
        <>
          <Card>
            <h3 className="text-lg font-semibold text-white">Pipeline Trace</h3>
            <div className="mt-3 space-y-1 text-sm text-slate-300">
              {result.trace.map((step) => (
                <p key={step}>- {step}</p>
              ))}
              {result.info_message ? <p className="text-slate-400">Note: {result.info_message}</p> : null}
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-white">Recommended Jobs</h3>
            <div className="mt-4 space-y-3">
              {result.results.length === 0 ? (
                <p className="text-sm text-slate-400">
                  No strong matches found for the selected filters. Use top company links below and broaden role/location.
                </p>
              ) : (
                result.results.map((job) => (
                  <div key={`${job.source_provider}-${job.external_id ?? job.title}`} className="rounded-lg border border-slate-700 bg-slate-900/55 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-slate-100">{job.title}</p>
                        <p className="mt-1 text-xs text-slate-400">
                          {job.company} | {job.location} | {job.source_provider}
                        </p>
                      </div>
                      <p className="text-sm font-semibold text-brand-100">{job.overall_score}% readiness</p>
                    </div>
                    <div className="mt-2 grid gap-2 text-xs text-slate-300 md:grid-cols-4">
                      <p>Resume match: {job.resume_match_score}%</p>
                      <p>Role relevance: {job.role_relevance}%</p>
                      <p>Sponsorship: {job.sponsorship_status}</p>
                      <p>Sponsorship confidence: {job.sponsorship_confidence}%</p>
                    </div>
                    <p className="mt-2 text-sm text-slate-300">{job.reason}</p>
                    {job.missing_points.length > 0 ? (
                      <div className="mt-2 text-xs text-slate-400">
                        {job.missing_points.map((point) => (
                          <p key={point}>- {point}</p>
                        ))}
                      </div>
                    ) : null}
                    {job.apply_url ? (
                      <a
                        href={job.apply_url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 inline-flex rounded-lg border border-brand-500/40 bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-100 transition hover:border-brand-400"
                      >
                        Apply now
                      </a>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-white">Top Company Career Links</h3>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {result.top_company_links.map((link) => (
                <a
                  key={link.name}
                  href={link.url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-3 text-sm text-slate-200 transition hover:border-brand-400"
                >
                  {link.name} Careers
                </a>
              ))}
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
