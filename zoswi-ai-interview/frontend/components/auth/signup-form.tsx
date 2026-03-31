"use client";

import { FormEvent, startTransition, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { apiBaseUrl } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { signupSchema } from "@/lib/validators/auth";

type SignupFormState = {
  full_name: string;
  email: string;
  password: string;
  role: "candidate" | "student" | "recruiter";
  years_experience: string;
  role_contact_email: string;
  target_role: string;
  university_name: string;
  graduation_year: string;
  degree_program: string;
  organization_name: string;
  recruiter_title: string;
  hiring_focus: string;
};

export function SignupForm() {
  const router = useRouter();
  const { signup } = useAuth();
  const [form, setForm] = useState<SignupFormState>({
    full_name: "",
    email: "",
    password: "",
    role: "candidate",
    years_experience: "",
    role_contact_email: "",
    target_role: "",
    university_name: "",
    graduation_year: "",
    degree_program: "",
    organization_name: "",
    recruiter_title: "",
    hiring_focus: ""
  });
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const googleOAuthUrl = `${apiBaseUrl()}/api/v1/auth/oauth/google/start`;
  const linkedinOAuthUrl = `${apiBaseUrl()}/api/v1/auth/oauth/linkedin/start`;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const parsed = signupSchema.safeParse(form);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid registration data");
      return;
    }
    setPending(true);
    startTransition(async () => {
      try {
        const payload = {
          full_name: parsed.data.full_name.trim(),
          email: parsed.data.email.trim().toLowerCase(),
          password: parsed.data.password,
          role: parsed.data.role,
          years_experience:
            parsed.data.role === "candidate" && typeof parsed.data.years_experience === "number"
              ? parsed.data.years_experience
              : undefined,
          role_contact_email: parsed.data.role_contact_email?.trim()
            ? parsed.data.role_contact_email.trim().toLowerCase()
            : undefined,
          profile_data: {} as Record<string, string>
        };

        if (parsed.data.role === "candidate" && parsed.data.target_role?.trim()) {
          payload.profile_data.target_role = parsed.data.target_role.trim();
        }
        if (parsed.data.role === "student") {
          payload.profile_data.university_name = parsed.data.university_name?.trim() ?? "";
          payload.profile_data.graduation_year = parsed.data.graduation_year?.trim() ?? "";
          if (parsed.data.degree_program?.trim()) {
            payload.profile_data.degree_program = parsed.data.degree_program.trim();
          }
        }
        if (parsed.data.role === "recruiter") {
          payload.profile_data.organization_name = parsed.data.organization_name?.trim() ?? "";
          if (parsed.data.recruiter_title?.trim()) {
            payload.profile_data.recruiter_title = parsed.data.recruiter_title.trim();
          }
          if (parsed.data.hiring_focus?.trim()) {
            payload.profile_data.hiring_focus = parsed.data.hiring_focus.trim();
          }
        }

        await signup(payload);
        router.replace("/dashboard");
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Sign up failed");
      } finally {
        setPending(false);
      }
    });
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {error ? <Alert variant="error">{error}</Alert> : null}
      <label className="block space-y-1">
        <span className="text-sm font-medium text-slate-200">Full Name</span>
        <Input
          autoComplete="name"
          value={form.full_name}
          onChange={(event) => setForm((previous) => ({ ...previous, full_name: event.target.value }))}
          required
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm font-medium text-slate-200">Email</span>
        <Input
          autoComplete="email"
          value={form.email}
          onChange={(event) => setForm((previous) => ({ ...previous, email: event.target.value }))}
          type="email"
          required
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm font-medium text-slate-200">Password</span>
        <Input
          autoComplete="new-password"
          value={form.password}
          onChange={(event) => setForm((previous) => ({ ...previous, password: event.target.value }))}
          type="password"
          required
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm font-medium text-slate-200">Account Role</span>
        <Select
          value={form.role}
          onChange={(event) =>
            setForm((previous) => ({
              ...previous,
              role: event.target.value as "candidate" | "student" | "recruiter"
            }))
          }
        >
          <option value="candidate">Candidate</option>
          <option value="student">Student</option>
          <option value="recruiter">Recruiter</option>
        </Select>
      </label>

      {form.role === "candidate" ? (
        <>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Years of Experience</span>
            <Input
              value={form.years_experience}
              onChange={(event) => setForm((previous) => ({ ...previous, years_experience: event.target.value }))}
              type="number"
              min={0}
              max={50}
              step={0.1}
            />
          </label>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Target Role (Optional)</span>
            <Input
              value={form.target_role}
              onChange={(event) => setForm((previous) => ({ ...previous, target_role: event.target.value }))}
            />
          </label>
        </>
      ) : null}

      {form.role === "student" ? (
        <>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">University Email</span>
            <Input
              value={form.role_contact_email}
              onChange={(event) => setForm((previous) => ({ ...previous, role_contact_email: event.target.value }))}
              type="email"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">University Name</span>
            <Input
              value={form.university_name}
              onChange={(event) => setForm((previous) => ({ ...previous, university_name: event.target.value }))}
            />
          </label>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Graduation Year</span>
            <Input
              value={form.graduation_year}
              onChange={(event) => setForm((previous) => ({ ...previous, graduation_year: event.target.value }))}
              type="text"
              inputMode="numeric"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Degree Program (Optional)</span>
            <Input
              value={form.degree_program}
              onChange={(event) => setForm((previous) => ({ ...previous, degree_program: event.target.value }))}
            />
          </label>
        </>
      ) : null}

      {form.role === "recruiter" ? (
        <>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Recruiter Email</span>
            <Input
              value={form.role_contact_email}
              onChange={(event) => setForm((previous) => ({ ...previous, role_contact_email: event.target.value }))}
              type="email"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Organization Name</span>
            <Input
              value={form.organization_name}
              onChange={(event) => setForm((previous) => ({ ...previous, organization_name: event.target.value }))}
            />
          </label>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Recruiter Title (Optional)</span>
            <Input
              value={form.recruiter_title}
              onChange={(event) => setForm((previous) => ({ ...previous, recruiter_title: event.target.value }))}
            />
          </label>
          <label className="block space-y-1">
            <span className="text-sm font-medium text-slate-200">Hiring Focus (Optional)</span>
            <Input
              value={form.hiring_focus}
              onChange={(event) => setForm((previous) => ({ ...previous, hiring_focus: event.target.value }))}
            />
          </label>
        </>
      ) : null}

      <Button className="w-full" type="submit" disabled={pending}>
        {pending ? (
          <span className="inline-flex items-center gap-2">
            <Spinner /> Creating account...
          </span>
        ) : (
          "Create account"
        )}
      </Button>
      <div className="space-y-2">
        <a
          href={googleOAuthUrl}
          className="block rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-center text-sm font-medium text-slate-100 transition hover:border-brand-400"
        >
          Continue with Google
        </a>
        <a
          href={linkedinOAuthUrl}
          className="block rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-center text-sm font-medium text-slate-100 transition hover:border-brand-400"
        >
          Continue with LinkedIn
        </a>
      </div>
      <p className="text-sm text-slate-400">
        Already registered?{" "}
        <Link href="/login" className="text-brand-200 hover:text-brand-100">
          Log in
        </Link>
      </p>
    </form>
  );
}
