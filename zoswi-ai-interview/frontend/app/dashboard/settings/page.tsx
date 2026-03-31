"use client";

import { FormEvent, startTransition, useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { TextArea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth/auth-context";
import { profileSchema } from "@/lib/validators/profile";
import { fetchCandidateProfile, updateCandidateProfile } from "@/services/candidate-service";
import { submitFeedback } from "@/services/platform-service";
import type { CandidateProfile } from "@/types/api";

export default function DashboardSettingsPage() {
  const { accessToken, refreshToken, applyRefreshedTokens, user } = useAuth();
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      if (!accessToken) return;
      setLoading(true);
      try {
        const profileData = await fetchCandidateProfile({
          accessToken,
          refreshToken,
          onTokenRefresh: applyRefreshedTokens
        });
        if (!active) return;
        setProfile(profileData);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Failed to load settings");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [accessToken, applyRefreshedTokens, refreshToken]);

  function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) return;
    setError(null);
    setMessage(null);
    const parsed = profileSchema.safeParse({
      headline: profile.headline,
      years_experience: profile.years_experience,
      target_roles: profile.target_roles,
      location: profile.location,
      role_contact_email: profile.role_contact_email,
      role_profile: profile.role_profile
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid profile values");
      return;
    }

    setSaving(true);
    startTransition(async () => {
      try {
        const updated = await updateCandidateProfile(
          { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
          {
            headline: parsed.data.headline ?? null,
            years_experience: parsed.data.years_experience ?? null,
            target_roles: parsed.data.target_roles,
            location: parsed.data.location ?? null,
            role_contact_email: parsed.data.role_contact_email ?? null,
            role_profile: parsed.data.role_profile ?? {}
          }
        );
        setProfile(updated);
        setMessage("Profile saved.");
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Profile update failed");
      } finally {
        setSaving(false);
      }
    });
  }

  async function handleFeedbackSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!feedback.trim()) return;
    setError(null);
    try {
      await submitFeedback(
        { accessToken, refreshToken, onTokenRefresh: applyRefreshedTokens },
        {
          category: "product",
          message: feedback.trim()
        }
      );
      setFeedback("");
      setMessage("Feedback submitted.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Feedback submission failed");
    }
  }

  if (loading || !profile) {
    return (
      <div className="flex min-h-[30vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-white">Settings</h1>
        <p className="text-sm text-slate-400">Manage profile details and platform preferences.</p>
      </div>
      {error ? <Alert variant="error">{error}</Alert> : null}
      {message ? <Alert variant="success">{message}</Alert> : null}

      <Card>
        <h3 className="text-lg font-semibold text-white">Profile</h3>
        <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={handleProfileSubmit}>
          <label className="space-y-1">
            <span className="text-sm text-slate-300">Headline</span>
            <Input
              value={profile.headline ?? ""}
              onChange={(event) => setProfile({ ...profile, headline: event.target.value })}
            />
          </label>
          {user?.role === "candidate" ? (
            <label className="space-y-1">
              <span className="text-sm text-slate-300">Years Experience</span>
              <Input
                type="number"
                min={0}
                max={50}
                step={0.1}
                value={profile.years_experience ?? 0}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    years_experience: Number.parseFloat(event.target.value || "0")
                  })
                }
              />
            </label>
          ) : (
            <div />
          )}
          <label className="space-y-1 md:col-span-2">
            <span className="text-sm text-slate-300">Target Roles (comma separated)</span>
            <Input
              value={profile.target_roles.join(", ")}
              onChange={(event) =>
                setProfile({
                  ...profile,
                  target_roles: event.target.value
                    .split(",")
                    .map((item) => item.trim())
                    .filter(Boolean)
                })
              }
            />
          </label>
          <label className="space-y-1 md:col-span-2">
            <span className="text-sm text-slate-300">Location</span>
            <Input
              value={profile.location ?? ""}
              onChange={(event) => setProfile({ ...profile, location: event.target.value })}
            />
          </label>
          {user?.role === "candidate" ? (
            <label className="space-y-1 md:col-span-2">
              <span className="text-sm text-slate-300">Preferred Target Role</span>
              <Input
                value={profile.role_profile.target_role ?? ""}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    role_profile: { ...profile.role_profile, target_role: event.target.value }
                  })
                }
              />
            </label>
          ) : null}
          {user?.role === "student" ? (
            <>
              <label className="space-y-1">
                <span className="text-sm text-slate-300">University Name</span>
                <Input
                  value={profile.role_profile.university_name ?? ""}
                  onChange={(event) =>
                    setProfile({
                      ...profile,
                      role_profile: { ...profile.role_profile, university_name: event.target.value }
                    })
                  }
                />
              </label>
              <label className="space-y-1">
                <span className="text-sm text-slate-300">Graduation Year</span>
                <Input
                  value={profile.role_profile.graduation_year ?? ""}
                  onChange={(event) =>
                    setProfile({
                      ...profile,
                      role_profile: { ...profile.role_profile, graduation_year: event.target.value }
                    })
                  }
                />
              </label>
              <label className="space-y-1 md:col-span-2">
                <span className="text-sm text-slate-300">Degree Program</span>
                <Input
                  value={profile.role_profile.degree_program ?? ""}
                  onChange={(event) =>
                    setProfile({
                      ...profile,
                      role_profile: { ...profile.role_profile, degree_program: event.target.value }
                    })
                  }
                />
              </label>
            </>
          ) : null}
          {user?.role === "recruiter" ? (
            <>
              <label className="space-y-1">
                <span className="text-sm text-slate-300">Organization Name</span>
                <Input
                  value={profile.role_profile.organization_name ?? ""}
                  onChange={(event) =>
                    setProfile({
                      ...profile,
                      role_profile: { ...profile.role_profile, organization_name: event.target.value }
                    })
                  }
                />
              </label>
              <label className="space-y-1">
                <span className="text-sm text-slate-300">Recruiter Title</span>
                <Input
                  value={profile.role_profile.recruiter_title ?? ""}
                  onChange={(event) =>
                    setProfile({
                      ...profile,
                      role_profile: { ...profile.role_profile, recruiter_title: event.target.value }
                    })
                  }
                />
              </label>
              <label className="space-y-1 md:col-span-2">
                <span className="text-sm text-slate-300">Hiring Focus</span>
                <Input
                  value={profile.role_profile.hiring_focus ?? ""}
                  onChange={(event) =>
                    setProfile({
                      ...profile,
                      role_profile: { ...profile.role_profile, hiring_focus: event.target.value }
                    })
                  }
                />
              </label>
            </>
          ) : null}
          {user?.role === "candidate" ? null : (
            <label className="space-y-1 md:col-span-2">
              <span className="text-sm text-slate-300">Role Contact Email</span>
              <Input
                type="email"
                value={profile.role_contact_email ?? ""}
                onChange={(event) => setProfile({ ...profile, role_contact_email: event.target.value })}
              />
            </label>
          )}
          <div className="md:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save Profile"}
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold text-white">Privacy & Feedback</h3>
        <p className="mt-2 text-sm text-slate-400">
          Transcript and analysis data are user-scoped. Use this to submit platform feedback.
        </p>
        <form className="mt-4 space-y-3" onSubmit={handleFeedbackSubmit}>
          <TextArea
            rows={4}
            value={feedback}
            onChange={(event) => setFeedback(event.target.value)}
            placeholder="Share platform feedback..."
          />
          <Button type="submit">Submit Feedback</Button>
        </form>
      </Card>
    </div>
  );
}
