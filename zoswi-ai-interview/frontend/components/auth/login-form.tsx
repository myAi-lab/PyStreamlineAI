"use client";

import { FormEvent, startTransition, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { apiBaseUrl } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { loginSchema } from "@/lib/validators/auth";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const oauthError = searchParams.get("oauth_error");
  const googleOAuthUrl = `${apiBaseUrl()}/api/v1/auth/oauth/google/start`;
  const linkedinOAuthUrl = `${apiBaseUrl()}/api/v1/auth/oauth/linkedin/start`;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const parsed = loginSchema.safeParse({ email, password });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid credentials");
      return;
    }
    setPending(true);
    startTransition(async () => {
      try {
        await login(parsed.data);
        router.replace("/dashboard");
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Login failed");
      } finally {
        setPending(false);
      }
    });
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {oauthError ? <Alert variant="error">OAuth sign-in failed. Please try again.</Alert> : null}
      {error ? <Alert variant="error">{error}</Alert> : null}
      <label className="block space-y-1">
        <span className="text-sm font-medium text-slate-200">Email</span>
        <Input
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          required
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm font-medium text-slate-200">Password</span>
        <Input
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          required
        />
      </label>
      <Button className="w-full" type="submit" disabled={pending}>
        {pending ? (
          <span className="inline-flex items-center gap-2">
            <Spinner /> Signing in...
          </span>
        ) : (
          "Sign in"
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
        Need an account?{" "}
        <Link href="/signup" className="text-brand-200 hover:text-brand-100">
          Create one
        </Link>
      </p>
    </form>
  );
}
