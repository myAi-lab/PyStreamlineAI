"use client";

import { useEffect, useState } from "react";

import { apiRequest } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";

type QueryState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

export function useApiQuery<T>(path: string, enabled = true) {
  const { accessToken, refreshToken, applyRefreshedTokens } = useAuth();
  const [state, setState] = useState<QueryState<T>>({
    data: null,
    loading: enabled,
    error: null
  });

  useEffect(() => {
    if (!enabled || !accessToken) {
      setState((previous) => ({ ...previous, loading: false }));
      return;
    }

    let active = true;
    setState((previous) => ({ ...previous, loading: true, error: null }));
    apiRequest<T>(path, {
      accessToken,
      refreshToken,
      onTokenRefresh: applyRefreshedTokens
    })
      .then((data) => {
        if (!active) return;
        setState({ data, loading: false, error: null });
      })
      .catch((error: Error) => {
        if (!active) return;
        setState({ data: null, loading: false, error: error.message });
      });

    return () => {
      active = false;
    };
  }, [accessToken, applyRefreshedTokens, enabled, path, refreshToken]);

  return state;
}

