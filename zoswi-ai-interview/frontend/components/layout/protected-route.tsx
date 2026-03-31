"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth/auth-context";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { initialized, isAuthenticated } = useAuth();

  useEffect(() => {
    if (initialized && !isAuthenticated) {
      router.replace("/login");
    }
  }, [initialized, isAuthenticated, router]);

  if (!initialized) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

