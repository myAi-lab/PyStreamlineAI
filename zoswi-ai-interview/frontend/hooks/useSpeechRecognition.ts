"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type SpeechRecognitionAlternativeLike = {
  transcript: string;
};

type SpeechRecognitionResultLike = {
  isFinal: boolean;
  0: SpeechRecognitionAlternativeLike;
  length: number;
};

type SpeechRecognitionEventLike = Event & {
  resultIndex: number;
  results: ArrayLike<SpeechRecognitionResultLike>;
};

type SpeechRecognitionErrorEventLike = Event & {
  error?:
    | "aborted"
    | "audio-capture"
    | "network"
    | "not-allowed"
    | "service-not-allowed"
    | "bad-grammar"
    | "language-not-supported"
    | "no-speech"
    | string;
};

interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

type UseSpeechRecognitionOptions = {
  enabled?: boolean;
  lang?: string;
  pauseMs?: number;
  onFinalTranscript?: (text: string) => void;
};

export function useSpeechRecognition({
  enabled = true,
  lang = "en-US",
  pauseMs = 900,
  onFinalTranscript
}: UseSpeechRecognitionOptions) {
  const recognitionCtor = useMemo<SpeechRecognitionConstructor | null>(() => {
    if (typeof window === "undefined") return null;
    return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null;
  }, []);

  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [lastTranscript, setLastTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const shouldRunRef = useRef(false);
  const pendingTranscriptRef = useRef("");
  const pauseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onFinalTranscriptRef = useRef<UseSpeechRecognitionOptions["onFinalTranscript"]>(onFinalTranscript);

  const supported = Boolean(recognitionCtor);

  useEffect(() => {
    onFinalTranscriptRef.current = onFinalTranscript;
  }, [onFinalTranscript]);

  const flushPendingTranscript = useCallback(() => {
    const payload = pendingTranscriptRef.current.trim();
    pendingTranscriptRef.current = "";
    if (!payload) return;
    setLastTranscript(payload);
    onFinalTranscriptRef.current?.(payload);
  }, []);

  const scheduleFlush = useCallback(() => {
    if (pauseTimerRef.current) {
      clearTimeout(pauseTimerRef.current);
      pauseTimerRef.current = null;
    }
    pauseTimerRef.current = setTimeout(() => {
      flushPendingTranscript();
    }, pauseMs);
  }, [flushPendingTranscript, pauseMs]);

  const stop = useCallback(() => {
    shouldRunRef.current = false;
    if (pauseTimerRef.current) {
      clearTimeout(pauseTimerRef.current);
      pauseTimerRef.current = null;
    }
    flushPendingTranscript();
    setInterimTranscript("");
    const recognition = recognitionRef.current;
    if (recognition) {
      try {
        recognition.stop();
      } catch {
        // Ignore engine stop failures.
      }
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, [flushPendingTranscript]);

  const start = useCallback(() => {
    if (!supported || !enabled || !recognitionCtor) {
      return false;
    }

    setError(null);
    shouldRunRef.current = true;

    try {
      const recognition = new recognitionCtor();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = lang;

      recognition.onresult = (event) => {
        let interimText = "";
        let finalText = "";

        for (let index = event.resultIndex; index < event.results.length; index += 1) {
          const result = event.results[index];
          const chunk = String(result?.[0]?.transcript ?? "").trim();
          if (!chunk) {
            continue;
          }
          if (result.isFinal) {
            finalText += `${chunk} `;
          } else {
            interimText += `${chunk} `;
          }
        }

        setInterimTranscript(interimText.trim());
        if (finalText.trim()) {
          pendingTranscriptRef.current = `${pendingTranscriptRef.current} ${finalText.trim()}`.trim();
          scheduleFlush();
        }
      };

      recognition.onerror = (event) => {
        const reason = String(event?.error ?? "").toLowerCase();
        if (reason === "aborted") {
          return;
        }
        if (reason === "no-speech") {
          return;
        }
        if (reason === "not-allowed" || reason === "service-not-allowed") {
          shouldRunRef.current = false;
          setIsListening(false);
          setError("Microphone permission blocked. Allow microphone access in browser site settings.");
          return;
        }
        if (reason === "audio-capture") {
          shouldRunRef.current = false;
          setIsListening(false);
          setError("No microphone device detected. Connect a mic and try again.");
          return;
        }
        if (reason === "network") {
          setError("Speech recognition network/service error. Please retry.");
          return;
        }
        setError("Speech recognition failed. Check browser compatibility and microphone access.");
      };

      recognition.onend = () => {
        setIsListening(false);
        if (!shouldRunRef.current || !enabled) {
          return;
        }
        try {
          recognition.start();
          setIsListening(true);
        } catch {
          setError("Could not restart speech recognition.");
          shouldRunRef.current = false;
        }
      };

      recognition.start();
      recognitionRef.current = recognition;
      setIsListening(true);
      return true;
    } catch {
      setError("Could not start speech recognition in this browser.");
      shouldRunRef.current = false;
      setIsListening(false);
      return false;
    }
  }, [enabled, lang, recognitionCtor, scheduleFlush, supported]);

  const toggle = useCallback(() => {
    if (isListening) {
      stop();
      return false;
    }
    return start();
  }, [isListening, start, stop]);

  useEffect(() => {
    if (enabled) {
      return;
    }
    stop();
  }, [enabled, stop]);

  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    supported,
    isListening,
    interimTranscript,
    lastTranscript,
    error,
    start,
    stop,
    toggle
  };
}
