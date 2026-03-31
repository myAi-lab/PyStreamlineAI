import Link from "next/link";

import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { FeatureItem } from "@/types/domain";

const features: FeatureItem[] = [
  {
    title: "AI Resume Intelligence",
    description: "Normalize resume signals into strengths, risks, and role-specific recommendations."
  },
  {
    title: "Structured Interview Engine",
    description: "Run adaptive multi-turn interviews with professional question progression."
  },
  {
    title: "Turn-Level Scoring",
    description: "Capture rubric-based communication, confidence, and technical depth by turn."
  },
  {
    title: "Recruiter Readiness API",
    description: "Expose clean candidate summaries designed for downstream hiring workflows."
  }
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <section className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 pb-20 pt-16 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <Badge>Enterprise AI Interview Platform</Badge>
            <h1 className="mt-6 text-4xl font-bold leading-tight text-white md:text-6xl">
              Candidate intelligence from resume ingestion to recruiter-ready interview outcomes.
            </h1>
            <p className="mt-6 max-w-2xl text-lg text-slate-300">
              ZoSwi delivers durable interview sessions, structured AI scoring, and privacy-aware candidate data
              handling for modern recruiting teams.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/signup">
                <Button className="px-6 py-3 text-base">Create Account</Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary" className="px-6 py-3 text-base">
                  Enter Dashboard
                </Button>
              </Link>
            </div>
          </div>
          <Card className="w-full max-w-md">
            <p className="text-sm uppercase tracking-wide text-brand-100">Platform Focus</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              <li>Separated frontend/backend architecture</li>
              <li>Async AI workflows with validated JSON outputs</li>
              <li>Durable session state and persistent interview history</li>
              <li>Role-ready authorization and structured observability</li>
            </ul>
          </Card>
        </section>

        <section id="features" className="mx-auto w-full max-w-7xl px-6 pb-16">
          <div className="grid gap-4 md:grid-cols-2">
            {features.map((feature) => (
              <Card key={feature.title}>
                <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
                <p className="mt-2 text-sm text-slate-300">{feature.description}</p>
              </Card>
            ))}
          </div>
        </section>

        <section id="trust" className="mx-auto w-full max-w-7xl px-6 pb-16">
          <Card className="grid gap-5 md:grid-cols-3">
            <div>
              <p className="text-3xl font-bold text-brand-100">API-first</p>
              <p className="mt-2 text-sm text-slate-300">Versioned contracts for candidate, interview, and platform services.</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-brand-100">Privacy-aware</p>
              <p className="mt-2 text-sm text-slate-300">
                Candidate-scoped access, prompt redaction hooks, and constrained PII exposure.
              </p>
            </div>
            <div>
              <p className="text-3xl font-bold text-brand-100">Realtime-ready</p>
              <p className="mt-2 text-sm text-slate-300">
                WebSocket interview transport with clean upgrade path to voice and proctoring layers.
              </p>
            </div>
          </Card>
        </section>

        <section id="platform" className="mx-auto w-full max-w-7xl px-6 pb-6">
          <Card className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-white">Build recruiter confidence with every interview cycle.</h2>
              <p className="mt-2 text-sm text-slate-300">
                Move from prototype hiring workflows to production-grade candidate intelligence.
              </p>
            </div>
            <Link href="/signup">
              <Button className="px-5 py-3">Start with ZoSwi</Button>
            </Link>
          </Card>
        </section>
      </main>
      <Footer />
    </div>
  );
}

