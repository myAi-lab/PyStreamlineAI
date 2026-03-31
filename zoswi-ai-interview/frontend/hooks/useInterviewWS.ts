"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { apiBaseUrl } from "@/lib/api/client";

export type InterviewWSStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected";

export type InterviewWSClientMessage =
  | { type: "start" }
  | { type: "respond"; answer: string }
  | { type: "ping" };

export type InterviewWSServerMessage = {
  type: "session_started" | "turn_processed" | "error" | "pong";
  payload: Record<string, unknown>;
};

type UseInterviewWSOptions = {
  sessionId: string;
  token: string | null;
  enabled?: boolean;
  heartbeatIntervalMs?: number;
  reconnectBaseDelayMs?: number;
  reconnectMaxDelayMs?: number;
  reconnectMaxAttempts?: number;
};

function toWsBaseUrl(baseUrl: string) {
  return baseUrl.replace(/^http/i, "ws");
}

export function useInterviewWS({
  sessionId,
  token,
  enabled = true,
  heartbeatIntervalMs = 15_000,
  reconnectBaseDelayMs = 900,
  reconnectMaxDelayMs = 12_000,
  reconnectMaxAttempts = 8
}: UseInterviewWSOptions) {
  const [status, setStatus] = useState<InterviewWSStatus>("idle");
  const [lastMessage, setLastMessage] = useState<InterviewWSServerMessage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const intentionalCloseRef = useRef(false);
  const reconnectAttemptsRef = useRef(0);

  const cleanupSocket = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.onopen = null;
      socketRef.current.onclose = null;
      socketRef.current.onmessage = null;
      socketRef.current.onerror = null;
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const send = useCallback((message: InterviewWSClientMessage) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }
    socket.send(JSON.stringify(message));
    return true;
  }, []);

  const connect = useCallback(() => {
    if (!enabled || !token || !sessionId) {
      setStatus("idle");
      return;
    }

    clearReconnectTimer();
    cleanupSocket();

    const attempt = reconnectAttemptsRef.current;
    setStatus(attempt > 0 ? "reconnecting" : "connecting");

    const base = toWsBaseUrl(apiBaseUrl());
    const wsUrl = `${base}/api/v1/ws/interviews/${sessionId}?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      reconnectAttemptsRef.current = 0;
      setStatus("connected");
      setError(null);

      heartbeatTimerRef.current = setInterval(() => {
        if (socket.readyState !== WebSocket.OPEN) {
          return;
        }
        socket.send(JSON.stringify({ type: "ping" }));
      }, heartbeatIntervalMs);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as InterviewWSServerMessage;
        if (!payload?.type) {
          return;
        }
        setLastMessage(payload);
      } catch {
        setError("Malformed realtime payload received.");
      }
    };

    socket.onerror = () => {
      setError("Realtime connection encountered a transport error.");
    };

    socket.onclose = () => {
      if (heartbeatTimerRef.current) {
        clearInterval(heartbeatTimerRef.current);
        heartbeatTimerRef.current = null;
      }

      socketRef.current = null;
      if (intentionalCloseRef.current || !enabled) {
        setStatus("disconnected");
        return;
      }

      reconnectAttemptsRef.current += 1;
      if (reconnectAttemptsRef.current > reconnectMaxAttempts) {
        setStatus("disconnected");
        setError("Realtime connection lost. Reconnect limit reached.");
        return;
      }

      const delay = Math.min(
        reconnectBaseDelayMs * 2 ** (reconnectAttemptsRef.current - 1),
        reconnectMaxDelayMs
      );

      setStatus("reconnecting");
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, delay);
    };
  }, [
    cleanupSocket,
    clearReconnectTimer,
    enabled,
    heartbeatIntervalMs,
    reconnectBaseDelayMs,
    reconnectMaxAttempts,
    reconnectMaxDelayMs,
    sessionId,
    token
  ]);

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;
    clearReconnectTimer();
    cleanupSocket();
    setStatus("disconnected");
  }, [cleanupSocket, clearReconnectTimer]);

  const reconnect = useCallback(() => {
    intentionalCloseRef.current = false;
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  useEffect(() => {
    intentionalCloseRef.current = false;
    reconnectAttemptsRef.current = 0;
    connect();

    return () => {
      intentionalCloseRef.current = true;
      clearReconnectTimer();
      cleanupSocket();
      setStatus("disconnected");
    };
  }, [connect, cleanupSocket, clearReconnectTimer]);

  return {
    status,
    connected: status === "connected",
    lastMessage,
    error,
    send,
    reconnect,
    disconnect
  };
}
