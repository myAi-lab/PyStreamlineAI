"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type SpeakOptions = {
  rate?: number;
  pitch?: number;
  lang?: string;
  voiceURI?: string;
};

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  const cancel = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    currentUtteranceRef.current = null;
    setIsSpeaking(false);
  }, [supported]);

  const speak = useCallback(
    (text: string, options?: SpeakOptions) => {
      if (!supported) {
        return false;
      }
      const clean = text.trim();
      if (!clean) {
        return false;
      }

      cancel();
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.rate = options?.rate ?? 1;
      utterance.pitch = options?.pitch ?? 1;
      utterance.lang = options?.lang ?? "en-US";

      if (options?.voiceURI) {
        const selected = window.speechSynthesis
          .getVoices()
          .find((voice) => voice.voiceURI === options.voiceURI);
        if (selected) {
          utterance.voice = selected;
        }
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        currentUtteranceRef.current = null;
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        currentUtteranceRef.current = null;
      };

      currentUtteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
      return true;
    },
    [cancel, supported]
  );

  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return {
    supported,
    isSpeaking,
    speak,
    cancel
  };
}
