"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type LiveInterviewPanelProps = {
  latestQuestion: string | null;
  onAppendTranscript: (text: string) => void;
  disabled?: boolean;
  roleTarget?: string;
  sessionMode?: string;
  sessionStatus?: string;
  transport?: "ws" | "rest";
};

type SpeechRecognitionAlternativeLike = {
  transcript: string;
  confidence: number;
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

interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

export function LiveInterviewPanel({
  latestQuestion,
  onAppendTranscript,
  disabled = false,
  roleTarget,
  sessionMode,
  sessionStatus,
  transport = "rest"
}: LiveInterviewPanelProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const sessionStartRef = useRef<number | null>(null);
  const [mediaReady, setMediaReady] = useState(false);
  const [micMuted, setMicMuted] = useState(false);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceInterim, setVoiceInterim] = useState("");
  const [voiceCaptured, setVoiceCaptured] = useState("");
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [autoReadQuestion, setAutoReadQuestion] = useState(true);
  const [speaking, setSpeaking] = useState(false);
  const [codingQuickAnswer, setCodingQuickAnswer] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const lastSpokenQuestionRef = useRef<string>("");

  const speechRecognitionCtor = useMemo<SpeechRecognitionConstructor | null>(() => {
    if (typeof window === "undefined") return null;
    const speechWindow = window as Window & {
      SpeechRecognition?: SpeechRecognitionConstructor;
      webkitSpeechRecognition?: SpeechRecognitionConstructor;
    };
    return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null;
  }, []);

  const speechSupported = Boolean(speechRecognitionCtor);
  const speechSynthesisSupported = typeof window !== "undefined" && "speechSynthesis" in window;
  const hasQuestion = Boolean(latestQuestion?.trim());
  const bannerText = hasQuestion
    ? `AI Interview Question: ${latestQuestion?.trim()}`
    : "AI Interview Question: Start session to begin your live interview.";
  const isCodingQuestion = Boolean(
    latestQuestion &&
      /\b(code|coding|algorithm|function|implement|complexity|optimi[sz]e|debug|query|sql)\b/i.test(latestQuestion)
  );
  const elapsedLabel = useMemo(() => {
    const mins = Math.floor(elapsedSeconds / 60)
      .toString()
      .padStart(2, "0");
    const secs = (elapsedSeconds % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
  }, [elapsedSeconds]);

  async function startMedia() {
    setMediaError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: true
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      if (!sessionStartRef.current) {
        sessionStartRef.current = Date.now();
      }
      setMediaReady(true);
      setMicMuted(false);
    } catch (error) {
      setMediaError(error instanceof Error ? error.message : "Camera/microphone access was denied.");
      setMediaReady(false);
    }
  }

  function stopMedia() {
    const stream = mediaStreamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setMediaReady(false);
    setMicMuted(false);
    setElapsedSeconds(0);
    sessionStartRef.current = null;
  }

  function toggleMicMute() {
    const stream = mediaStreamRef.current;
    if (!stream) return;
    const nextMuted = !micMuted;
    stream.getAudioTracks().forEach((track) => {
      track.enabled = !nextMuted;
    });
    setMicMuted(nextMuted);
  }

  function speakQuestion(question: string) {
    const cleanQuestion = question.trim();
    if (!cleanQuestion || !speechSynthesisSupported) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(cleanQuestion);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }

  function startListening() {
    if (!speechRecognitionCtor || disabled) return;
    setVoiceError(null);
    try {
      const recognition = new speechRecognitionCtor();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";
      recognition.onresult = (event) => {
        let finalText = "";
        let interimText = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const result = event.results[i];
          const chunk = String(result?.[0]?.transcript ?? "").trim();
          if (!chunk) continue;
          if (result.isFinal) {
            finalText += `${chunk} `;
          } else {
            interimText += `${chunk} `;
          }
        }
        const normalizedInterim = interimText.trim();
        setVoiceInterim(normalizedInterim);
        if (finalText.trim()) {
          const normalizedFinal = finalText.trim();
          setVoiceCaptured((previous) => `${previous} ${normalizedFinal}`.trim());
          onAppendTranscript(normalizedFinal);
        }
      };
      recognition.onerror = () => {
        setVoiceError("Speech recognition error. Check browser permissions and mic access.");
      };
      recognition.onend = () => {
        setIsListening(false);
      };
      recognition.start();
      recognitionRef.current = recognition;
      setIsListening(true);
    } catch {
      setVoiceError("Could not start speech recognition in this browser.");
      setIsListening(false);
    }
  }

  function stopListening() {
    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
    setVoiceInterim("");
  }

  function submitCodingQuickAnswer() {
    const clean = codingQuickAnswer.trim();
    if (!clean) return;
    onAppendTranscript(clean);
    setCodingQuickAnswer("");
  }

  useEffect(() => {
    if (!videoRef.current || !mediaStreamRef.current) return;
    videoRef.current.srcObject = mediaStreamRef.current;
  }, [mediaReady]);

  useEffect(() => {
    if (!autoReadQuestion || !latestQuestion?.trim()) return;
    const cleanQuestion = latestQuestion.trim();
    if (lastSpokenQuestionRef.current === cleanQuestion) return;
    lastSpokenQuestionRef.current = cleanQuestion;
    speakQuestion(cleanQuestion);
  }, [autoReadQuestion, latestQuestion]);

  useEffect(() => {
    if (!mediaReady || !sessionStartRef.current) return;
    const interval = window.setInterval(() => {
      if (!sessionStartRef.current) return;
      const diffMs = Date.now() - sessionStartRef.current;
      setElapsedSeconds(Math.max(0, Math.floor(diffMs / 1000)));
    }, 1000);
    return () => window.clearInterval(interval);
  }, [mediaReady]);

  useEffect(() => {
    if (!disabled) return;
    if (isListening) {
      stopListening();
    }
  }, [disabled, isListening]);

  useEffect(() => {
    return () => {
      stopListening();
      stopMedia();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return (
    <Card className="overflow-hidden border-slate-600/80 bg-gradient-to-b from-slate-900/95 via-slate-900 to-slate-950/95 p-0">
      <div className="border-b border-slate-700/80 bg-slate-900/80 px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Live interview call</p>
            <h4 className="text-sm font-semibold text-white">{roleTarget ?? "Interview Session"}</h4>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{sessionMode ?? "mixed"}</Badge>
            <Badge>{sessionStatus ?? "created"}</Badge>
            <Badge>{transport === "ws" ? "Realtime WS" : "REST fallback"}</Badge>
            <Badge>{mediaReady ? `In call ${elapsedLabel}` : "Not connected"}</Badge>
          </div>
        </div>
      </div>

      <div className="space-y-3 p-4">
        <div className="overflow-hidden rounded-2xl border border-slate-700/80 bg-gradient-to-br from-slate-900 to-slate-800">
          <div className="interview-banner-wrap h-9 border-b border-slate-700/70 bg-slate-950/80">
            <div className="interview-banner-track flex h-full items-center whitespace-nowrap px-4 text-xs font-semibold uppercase tracking-wide text-slate-200">
              {bannerText}
            </div>
          </div>

          <div className="grid gap-3 p-3 md:grid-cols-2">
            <div className="relative overflow-hidden rounded-xl border border-cyan-500/30 bg-[radial-gradient(circle_at_top,rgba(43,202,223,0.25),transparent_58%),linear-gradient(160deg,#0c1b30,#111827)] p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-cyan-100">AI interviewer</p>
                <div className="flex items-center gap-2 text-[11px] text-slate-200">
                  <span
                    className={`h-2 w-2 rounded-full ${speaking ? "animate-pulse bg-emerald-400" : "bg-slate-500"}`}
                  />
                  <span>{speaking ? "Speaking" : "Ready"}</span>
                </div>
              </div>
              <div className="mt-6">
                <div className="flex h-16 w-16 items-center justify-center rounded-full border border-cyan-300/30 bg-cyan-400/10 text-xl text-cyan-200">
                  AI
                </div>
                <p className="mt-4 text-sm text-white">
                  {hasQuestion
                    ? latestQuestion?.trim()
                    : "Start the session. I will ask one question at a time and adapt to your responses."}
                </p>
                <div className="mt-3 flex items-end gap-1">
                  <span className="interview-wave-bar h-2 w-1 rounded-full bg-cyan-300/80" />
                  <span className="interview-wave-bar interview-wave-delay-1 h-4 w-1 rounded-full bg-cyan-300/80" />
                  <span className="interview-wave-bar interview-wave-delay-2 h-6 w-1 rounded-full bg-cyan-300/80" />
                  <span className="interview-wave-bar interview-wave-delay-3 h-3 w-1 rounded-full bg-cyan-300/80" />
                  <span className="interview-wave-bar interview-wave-delay-4 h-5 w-1 rounded-full bg-cyan-300/80" />
                </div>
              </div>
              <div className="absolute bottom-3 left-3 rounded-lg bg-slate-900/70 px-2 py-1 text-xs text-white">
                ZoSwi AI
              </div>
            </div>

            <div className="relative overflow-hidden rounded-xl border border-slate-700 bg-black">
              <video ref={videoRef} className="h-[300px] w-full object-cover" autoPlay muted playsInline />
              {!mediaReady ? (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-950/85 p-4 text-center text-xs text-slate-300">
                  Join with camera and microphone to appear in the interview screen.
                </div>
              ) : null}
              <div className="absolute left-3 top-3 rounded-lg bg-slate-900/70 px-2 py-1 text-xs text-white">
                {micMuted ? "Mic muted" : "Mic live"}
              </div>
              <div className="absolute bottom-3 left-3 rounded-lg bg-slate-900/70 px-2 py-1 text-xs text-white">You</div>
            </div>
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-700/80 bg-slate-900/55 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Meeting Controls</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {!mediaReady ? (
                <Button onClick={() => void startMedia()} disabled={disabled}>
                  Join Cam + Mic
                </Button>
              ) : (
                <>
                  <Button onClick={() => toggleMicMute()} variant="secondary" disabled={disabled}>
                    {micMuted ? "Unmute Mic" : "Mute Mic"}
                  </Button>
                  <Button onClick={() => stopMedia()} variant="secondary">
                    Leave Interview
                  </Button>
                </>
              )}
              <Button
                onClick={() => (isListening ? stopListening() : startListening())}
                disabled={!speechSupported || disabled}
              >
                {isListening ? "Stop Voice Capture" : "Capture Voice"}
              </Button>
              <Button
                onClick={() => latestQuestion && speakQuestion(latestQuestion)}
                variant="secondary"
                disabled={!speechSynthesisSupported || !hasQuestion}
              >
                {speaking ? "Playing..." : "Replay Question"}
              </Button>
              <Button onClick={() => setAutoReadQuestion((previous) => !previous)} variant="ghost">
                {autoReadQuestion ? "Auto Voice On" : "Auto Voice Off"}
              </Button>
            </div>
          </div>

          <div
            className={
              isCodingQuestion
                ? "rounded-2xl border border-cyan-500/35 bg-cyan-500/10 p-3"
                : "rounded-2xl border border-slate-700/80 bg-slate-900/55 p-3"
            }
          >
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-cyan-100">
                {isCodingQuestion ? "Coding Prompt Quick Reply" : "Quick Response Insert"}
              </p>
              <Badge>{isCodingQuestion ? "Single answer mode" : "Short reply mode"}</Badge>
            </div>
            <p className="mt-1 text-xs text-slate-300">
              {isCodingQuestion
                ? "Share one concise approach, tradeoff, or final answer. No full code block needed."
                : "Insert a short response into your main answer box to speed up turn replies."}
            </p>
            <div className="mt-2 flex gap-2">
              <Input
                value={codingQuickAnswer}
                onChange={(event) => setCodingQuickAnswer(event.target.value)}
                placeholder={
                  isCodingQuestion
                    ? "Example: I would use a hash map in one pass for O(n) time."
                    : "Example: I handled cross-team incidents by prioritizing impact first."
                }
                maxLength={400}
              />
              <Button onClick={submitCodingQuickAnswer} disabled={!codingQuickAnswer.trim()}>
                Insert
              </Button>
            </div>
          </div>
        </div>

        {voiceCaptured ? (
          <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-400">Captured Voice Transcript</p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-200">{voiceCaptured}</p>
            {voiceInterim ? <p className="mt-2 text-xs text-slate-400">Listening: {voiceInterim}</p> : null}
          </div>
        ) : null}

        {!speechSupported ? (
          <Alert variant="info">
            Speech recognition is not supported in this browser. You can still type responses manually.
          </Alert>
        ) : null}
      </div>

      {mediaError ? <Alert variant="error" className="mx-4 mb-3">{mediaError}</Alert> : null}
      {voiceError ? <Alert variant="error" className="mx-4 mb-3">{voiceError}</Alert> : null}
    </Card>
  );
}
