"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { exchangeOAuthBridgeToken } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const bridgeToken = searchParams.get("bridge_token");

  useEffect(() => {
    if (!bridgeToken) {
      setError("Missing OAuth bridge token.");
      return;
    }

    let active = true;
    void (async () => {
      try {
        await exchangeOAuthBridgeToken(bridgeToken);
        if (!active) return;
        router.replace("/dashboard");
      } catch (exchangeError) {
        if (!active) return;
        setError(exchangeError instanceof Error ? exchangeError.message : "OAuth login failed");
      }
    })();

    return () => {
      active = false;
    };
  }, [bridgeToken, exchangeOAuthBridgeToken, router]);

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md items-center px-6 py-16">
      <Card className="w-full">
        <h1 className="text-2xl font-bold text-white">Completing OAuth Sign-In</h1>
        <p className="mt-2 text-sm text-slate-400">Finalizing your Google/LinkedIn session with ZoSwi.</p>
        <div className="mt-6">
          {error ? (
            <div className="space-y-4">
              <Alert variant="error">{error}</Alert>
              <Link href="/login">
                <Button variant="secondary">Back to Login</Button>
              </Link>
            </div>
          ) : (
            <div className="inline-flex items-center gap-2 text-sm text-slate-300">
              <Spinner />
              Signing you in...
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

