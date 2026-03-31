"use client";

import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";
import { formatDateTime } from "@/lib/utils/date";
import {
  buildImmigrationBrief,
  refreshImmigrationUpdates,
  searchImmigrationUpdates
} from "@/services/immigration-service";
import type { ImmigrationSearchResponse } from "@/types/api";

const trustedResources = [
  { label: "USCIS Newsroom", href: "https://www.uscis.gov/newsroom" },
  { label: "US Department of State - Visa", href: "https://travel.state.gov/content/travel/en/us-visas.html" },
  { label: "DHS Study in the States", href: "https://studyinthestates.dhs.gov/" },
  { label: "Department of Labor Foreign Labor", href: "https://www.dol.gov/agencies/eta/foreign-labor" }
];

export default function ImmigrationUpdatesPage() {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(20);
  const [categories, setCategories] = useState<string[]>([]);
  const [result, setResult] = useState<ImmigrationSearchResponse | null>(null);
  const [brief, setBrief] = useState("");
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [generatingBrief, setGeneratingBrief] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const availableCategories = result?.categories ?? [];

  useEffect(() => {
    let active = true;
    void (async () => {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        const response = await searchImmigrationUpdates(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          { query: "", visa_categories: [], limit: 20, force_refresh: true }
        );
        if (!active) return;
        setResult(response);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Unable to load immigration updates");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, applyRefreshedTokens, refreshToken]);

  async function runSearch(forceRefresh = false) {
    if (!accessToken) return;
    setSearching(true);
    setError(null);
    try {
      const response = await searchImmigrationUpdates(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        { query, visa_categories: categories, limit, force_refresh: forceRefresh }
      );
      setResult(response);
      if (forceRefresh) {
        setBrief("");
      }
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function runRefresh() {
    if (!accessToken) return;
    setRefreshing(true);
    setError(null);
    try {
      await refreshImmigrationUpdates({ accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens });
      await runSearch(true);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

  async function generateBrief() {
    if (!accessToken) return;
    setGeneratingBrief(true);
    setError(null);
    try {
      const response = await buildImmigrationBrief(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        { query, visa_categories: categories, limit: Math.min(limit, 10) }
      );
      setBrief(response.brief);
    } catch (briefError) {
      setError(briefError instanceof Error ? briefError.message : "Could not generate brief");
    } finally {
      setGeneratingBrief(false);
    }
  }

  function toggleCategory(category: string) {
    setCategories((previous) =>
      previous.includes(category) ? previous.filter((item) => item !== category) : [...previous, category]
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-[30vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">Immigration & Visa Updates</h1>
        <p className="text-sm text-slate-400">
          Live update feed with category filters, quick policy summary, and source-first links.
        </p>
      </div>

      {error ? <Alert variant="error">{error}</Alert> : null}

      <Card>
        <h3 className="text-lg font-semibold text-white">Search & Filters</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_160px_auto]">
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search topics: H1B registration, STEM OPT, visa bulletin..."
          />
          <Select value={String(limit)} onChange={(event) => setLimit(Number.parseInt(event.target.value, 10))}>
            <option value="10">10 results</option>
            <option value="20">20 results</option>
            <option value="30">30 results</option>
            <option value="40">40 results</option>
          </Select>
          <Button onClick={() => void runSearch(false)} disabled={searching}>
            {searching ? "Searching..." : "Search"}
          </Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {availableCategories.map((category) => {
            const selected = categories.includes(category);
            return (
              <button
                key={category}
                type="button"
                onClick={() => toggleCategory(category)}
                className={`rounded-full border px-3 py-1 text-xs transition ${
                  selected
                    ? "border-brand-500 bg-brand-500/20 text-brand-100"
                    : "border-slate-600 bg-slate-900 text-slate-300 hover:border-slate-400"
                }`}
              >
                {category}
              </button>
            );
          })}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button onClick={() => void runRefresh()} disabled={refreshing} variant="secondary">
            {refreshing ? "Refreshing..." : "Refresh Feed"}
          </Button>
          <Button onClick={() => void generateBrief()} disabled={generatingBrief}>
            {generatingBrief ? "Generating..." : "Generate AI Brief"}
          </Button>
        </div>
        {result?.live_note ? <p className="mt-3 text-xs text-slate-400">{result.live_note}</p> : null}
        {result?.last_refreshed_at ? (
          <p className="mt-1 text-xs text-slate-500">Last refresh: {formatDateTime(result.last_refreshed_at)}</p>
        ) : null}
      </Card>

      {brief ? (
        <Card>
          <h3 className="text-lg font-semibold text-white">ZoSwi Brief</h3>
          <pre className="mt-3 whitespace-pre-wrap text-sm text-slate-200">{brief}</pre>
        </Card>
      ) : null}

      <Card>
        <h3 className="text-lg font-semibold text-white">Latest Updates Feed</h3>
        <div className="mt-3 space-y-3">
          {!result || result.updates.length === 0 ? (
            <p className="text-sm text-slate-400">No updates found for the current query/filter.</p>
          ) : (
            result.updates.map((item) => (
              <div key={item.id} className="rounded-lg border border-slate-700 bg-slate-900/55 p-3">
                <p className="text-sm font-semibold text-slate-100">{item.title}</p>
                <p className="mt-1 text-xs text-slate-400">
                  {item.source} | {item.visa_category} |{" "}
                  {item.published_date ? formatDateTime(item.published_date) : "Unknown date"}
                </p>
                <p className="mt-2 text-sm text-slate-300">{item.summary}</p>
                {item.tags.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {item.tags.slice(0, 6).map((tag) => (
                      <span key={tag} className="rounded-full border border-slate-600 px-2 py-0.5 text-[11px] text-slate-300">
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : null}
                <a
                  href={item.link}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex rounded-lg border border-brand-500/40 bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-100 transition hover:border-brand-400"
                >
                  Read Original Source
                </a>
              </div>
            ))
          )}
        </div>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold text-white">Trusted Sources</h3>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {trustedResources.map((resource) => (
            <a
              key={resource.href}
              href={resource.href}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-3 text-sm text-slate-200 transition hover:border-brand-400"
            >
              {resource.label}
            </a>
          ))}
        </div>
      </Card>
    </div>
  );
}
