"use client";

import { useEffect, useRef, useState } from "react";

import { apiBaseUrl } from "@/lib/api/client";

export type WSMessage = {
  type: string;
  payload: Record<string, unknown>;
};

export function useWebsocketInterview(sessionId: string, token: string | null) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token || !sessionId) {
      return;
    }

    const base = apiBaseUrl().replace(/^http/, "ws");
    const ws = new WebSocket(`${base}/api/v1/ws/interviews/${sessionId}?token=${encodeURIComponent(token)}`);
    socketRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as WSMessage;
        setLastMessage(parsed);
      } catch {
        // Ignore malformed websocket payloads.
      }
    };

    return () => {
      ws.close();
      socketRef.current = null;
    };
  }, [sessionId, token]);

  function send(message: Record<string, unknown>) {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    }
  }

  return {
    connected,
    lastMessage,
    send
  };
}

