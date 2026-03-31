"use client";

import { useEffect, useMemo, useReducer, useRef, useState } from "react";

import { AIPanel } from "@/components/interview/AIPanel";
import { Controls } from "@/components/interview/Controls";
import { VideoPanel } from "@/components/interview/VideoPanel";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { InterviewWSStatus } from "@/hooks/useInterviewWS";
import { useMediaStream } from "@/hooks/useMediaStream";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { cn } from "@/lib/utils/cn";

type InterviewWindowAction =
  | { type: "WS_CONNECTING" }
  | { type: "WS_CONNECTED" }
  | { type: "WS_DISCONNECTED" }
  | { type: "PROCESSING_START" }
  | { type: "PROCESSING_DONE" }
  | { type: "AI_SPEAK_START" }
  | { type: "AI_SPEAK_END" }
  | { type: "LISTEN_START" }
  | { type: "LISTEN_STOP" }
  | { type: "RESET_IDLE" }
  | { type: "ERROR" };

export type InterviewWindowState =
  | "idle"
  | "connecting"
  | "active"
  | "ai_speaking"
  | "user_listening"
  | "processing"
  | "disconnected";

function stateMachine(state: InterviewWindowState, action: InterviewWindowAction): InterviewWindowState {
  switch (action.type) {
    case "WS_CONNECTING":
      return "connecting";
    case "WS_CONNECTED":
      if (state === "processing" || state === "ai_speaking" || state === "user_listening") return state;
      return "active";
    case "WS_DISCONNECTED":
      if (state === "idle") return state;
      return "disconnected";
    case "PROCESSING_START":
      return "processing";
    case "PROCESSING_DONE":
      return state === "disconnected" ? state : "active";
    case "AI_SPEAK_START":
      if (state === "processing" || state === "connecting" || state === "disconnected") return state;
      return "ai_speaking";
    case "AI_SPEAK_END":
      return state === "ai_speaking" ? "active" : state;
    case "LISTEN_START":
      if (state === "processing" || state === "connecting" || state === "disconnected") return state;
      return "user_listening";
    case "LISTEN_STOP":
      return state === "user_listening" ? "active" : state;
    case "RESET_IDLE":
      return "idle";
    case "ERROR":
      return "disconnected";
    default:
      return state;
  }
}

type InterviewWindowProps = {
  latestQuestion: string | null;
  roleTarget: string;
  sessionMode: string;
  sessionStatus: string;
  wsStatus: InterviewWSStatus;
  wsError: string | null;
  disabled?: boolean;
  isProcessing?: boolean;
  onStartInterview: () => Promise<void> | void;
  onSubmitAnswer: (answer: string) => Promise<void> | void;
  fullScreen?: boolean;
};

export function InterviewWindow({
  latestQuestion,
  roleTarget,
  sessionMode,
  sessionStatus,
  wsStatus,
  wsError,
  disabled = false,
  isProcessing = false,
  onStartInterview,
  onSubmitAnswer,
  fullScreen = false
}: InterviewWindowProps) {
  const [viewState, dispatch] = useReducer(stateMachine, "idle");
  const [localError, setLocalError] = useState<string | null>(null);
  const [autoVoice, setAutoVoice] = useState(true);
  const [micEnabled, setMicEnabled] = useState(true);
  const [cameraEnabled, setCameraEnabled] = useState(true);
  const [listeningEnabled, setListeningEnabled] = useState(false);
  const [micPermissionDenied, setMicPermissionDenied] = useState(false);
  const [quickReply, setQuickReply] = useState("");
  const [lastCapturedTranscript, setLastCapturedTranscript] = useState("");
  const [lastSubmittedAnswer, setLastSubmittedAnswer] = useState("");
  const submitInFlightRef = useRef(false);
  const lastSpokenQuestionRef = useRef("");
  const prevSpeakingRef = useRef(false);
  const prevListeningRef = useRef(false);
  const media = useMediaStream();

  const {
    supported: speechSupported,
    isSpeaking,
    speak,
    cancel
  } = useSpeechSynthesis();

  const canListen = micEnabled && !micPermissionDenied && sessionStatus === "active" && !disabled;

  async function requestSystemMicPermission() {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      return true;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      stream.getTracks().forEach((track) => track.stop());
      setMicPermissionDenied(false);
      setLocalError(null);
      return true;
    } catch {
      setMicPermissionDenied(true);
      setListeningEnabled(false);
      setLocalError("Microphone permission is required for live voice mode. Enable it in browser site settings.");
      return false;
    }
  }

  async function ensureCameraPreview() {
    if (!cameraEnabled) {
      return true;
    }
    if (media.isActive && media.cameraOn) {
      return true;
    }
    const started = await media.start({ video: true, audio: false });
    if (!started) {
      setLocalError("Camera preview could not start. Allow camera access in browser site settings.");
      return false;
    }
    return true;
  }

  async function submitAnswer(answerText: string) {
    const clean = answerText.trim();
    if (!clean || submitInFlightRef.current || disabled) {
      return;
    }

    submitInFlightRef.current = true;
    setLastSubmittedAnswer(clean);
    setLocalError(null);
    dispatch({ type: "PROCESSING_START" });

    try {
      await onSubmitAnswer(clean);
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Could not send response. Check realtime connection.";
      setLocalError(message);
      dispatch({ type: "ERROR" });
      return;
    } finally {
      submitInFlightRef.current = false;
      dispatch({ type: "PROCESSING_DONE" });
    }
  }

  const {
    supported: recognitionSupported,
    isListening,
    error: recognitionError,
    start: startRecognition,
    stop: stopRecognition
  } = useSpeechRecognition({
    enabled: listeningEnabled && canListen && !isSpeaking && !isProcessing,
    onFinalTranscript: (text) => {
      const clean = text.trim();
      if (!clean) return;
      setLastCapturedTranscript(clean);
      void submitAnswer(clean);
    }
  });

  const stateLabel = useMemo(() => viewState.replace("_", " "), [viewState]);
  const hasQuestion = Boolean(latestQuestion?.trim());
  const canStartInterview =
    (sessionStatus === "created" || sessionStatus === "ready" || sessionStatus === "paused") &&
    !disabled &&
    !isProcessing;

  async function handleStartInterview() {
    if (!canStartInterview) return;
    setLocalError(null);
    dispatch({ type: "PROCESSING_START" });
    try {
      if (cameraEnabled) {
        await ensureCameraPreview();
      }
      if (micEnabled) {
        const granted = await requestSystemMicPermission();
        if (granted) {
          setListeningEnabled(true);
        }
      }
      await onStartInterview();
    } catch (startError) {
      setLocalError(startError instanceof Error ? startError.message : "Could not start interview session.");
      dispatch({ type: "ERROR" });
      return;
    } finally {
      dispatch({ type: "PROCESSING_DONE" });
    }
  }

  function handleLeave() {
    stopRecognition();
    cancel();
    media.stop();
    setListeningEnabled(false);
    dispatch({ type: "RESET_IDLE" });
  }

  async function handleToggleCameraEnabled() {
    if (cameraEnabled) {
      setCameraEnabled(false);
      if (media.isActive && media.cameraOn) {
        media.toggleCamera();
      }
      return;
    }

    setCameraEnabled(true);
    if (!media.isActive) {
      const started = await media.start({ video: true, audio: false });
      if (!started) {
        setLocalError("Camera preview could not start. Allow camera access in browser site settings.");
      }
      return;
    }
    if (!media.cameraOn) {
      media.toggleCamera();
    }
  }

  async function handleToggleListening() {
    if (!micEnabled) {
      setListeningEnabled(false);
      return;
    }
    if (isListening || listeningEnabled) {
      setListeningEnabled(false);
      stopRecognition();
      return;
    }
    const granted = await requestSystemMicPermission();
    if (!granted) {
      return;
    }
    setListeningEnabled(true);
    startRecognition();
  }

  function handleQuickSend() {
    const clean = quickReply.trim();
    if (!clean) return;
    void submitAnswer(clean);
    setQuickReply("");
  }

  useEffect(() => {
    if (wsStatus === "connecting" || wsStatus === "reconnecting") {
      dispatch({ type: "WS_CONNECTING" });
      return;
    }
    if (wsStatus === "connected") {
      dispatch({ type: "WS_CONNECTED" });
      return;
    }
    if (wsStatus === "disconnected") {
      dispatch({ type: "WS_DISCONNECTED" });
    }
  }, [wsStatus]);

  useEffect(() => {
    if (isProcessing) {
      dispatch({ type: "PROCESSING_START" });
      return;
    }
    dispatch({ type: "PROCESSING_DONE" });
  }, [isProcessing]);

  useEffect(() => {
    if (!autoVoice || !latestQuestion?.trim() || disabled) {
      return;
    }
    const cleanQuestion = latestQuestion.trim();
    if (lastSpokenQuestionRef.current === cleanQuestion) {
      return;
    }
    lastSpokenQuestionRef.current = cleanQuestion;
    speak(cleanQuestion, { rate: 1, pitch: 1 });
  }, [autoVoice, disabled, latestQuestion, speak]);

  useEffect(() => {
    if (isSpeaking && !prevSpeakingRef.current) {
      dispatch({ type: "AI_SPEAK_START" });
    }
    if (!isSpeaking && prevSpeakingRef.current) {
      dispatch({ type: "AI_SPEAK_END" });
    }
    prevSpeakingRef.current = isSpeaking;
  }, [isSpeaking]);

  useEffect(() => {
    if (isListening && !prevListeningRef.current) {
      dispatch({ type: "LISTEN_START" });
    }
    if (!isListening && prevListeningRef.current) {
      dispatch({ type: "LISTEN_STOP" });
    }
    prevListeningRef.current = isListening;
  }, [isListening]);

  useEffect(() => {
    if (isSpeaking && isListening) {
      stopRecognition();
    }
  }, [isListening, isSpeaking, stopRecognition]);

  useEffect(() => {
    if (!micEnabled && isListening) {
      stopRecognition();
    }
  }, [isListening, micEnabled, stopRecognition]);

  useEffect(() => {
    if (!canListen || !listeningEnabled || isSpeaking) {
      if (isListening) {
        stopRecognition();
      }
      return;
    }
    if (!isListening) {
      startRecognition();
    }
  }, [canListen, listeningEnabled, isListening, isSpeaking, startRecognition, stopRecognition]);

  const questionText = latestQuestion?.trim()
    ? latestQuestion.trim()
    : "Start interview to get the first AI question.";

  return (
    <Card
      className={cn(
        "relative overflow-hidden border-slate-700 bg-slate-950 p-0",
        fullScreen ? "h-full rounded-none border-x-0 border-t-0" : "rounded-2xl"
      )}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_14%_0%,rgba(14,165,233,0.12),transparent_38%),radial-gradient(circle_at_90%_100%,rgba(29,78,216,0.14),transparent_44%)]" />

      <div className="relative flex h-full flex-col px-3 py-3 sm:px-4 sm:py-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">One on One Interview</p>
            <h4 className="text-sm font-semibold text-white">{roleTarget}</h4>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{sessionMode}</Badge>
            <Badge>{sessionStatus}</Badge>
            <Badge>{wsStatus === "connected" ? "Realtime WS" : "WS reconnecting"}</Badge>
            <Badge className="capitalize">{stateLabel}</Badge>
            {!canStartInterview ? null : (
              <Button onClick={() => void handleStartInterview()} disabled={disabled || isProcessing}>
                {isProcessing ? "Starting..." : "Start Interview"}
              </Button>
            )}
          </div>
        </div>

        <div className="mx-auto mt-3 w-full max-w-4xl rounded-md border-4 border-black bg-slate-100/95 px-4 py-3 text-center shadow-[0_12px_40px_rgba(0,0,0,0.35)]">
          <p className="text-sm font-semibold text-slate-800">{questionText}</p>
        </div>

        <div className="relative mt-3 flex-1 overflow-hidden rounded-[30px] border-2 border-slate-700/90 bg-slate-900/55 p-3">
          <AIPanel
            question={latestQuestion}
            roleTarget={roleTarget}
            isSpeaking={isSpeaking}
            stateLabel={stateLabel}
          />

          <div className="absolute bottom-4 right-4 z-20 w-[170px] sm:w-[220px] lg:w-[250px]">
            <VideoPanel
              stream={media.stream}
              joined={cameraEnabled && media.isActive && media.cameraOn}
              micOn={micEnabled}
              cameraOn={cameraEnabled && media.cameraOn}
              tileMode
            />
          </div>

          <div className="absolute bottom-4 left-4 z-20">
            <Controls
              micEnabled={micEnabled}
              cameraEnabled={cameraEnabled}
              listening={isListening}
              canStartInterview={canStartInterview}
              disabled={disabled}
              hasQuestion={hasQuestion}
              autoVoice={autoVoice}
              onToggleMicEnabled={() => {
                setMicEnabled((previous) => {
                  const next = !previous;
                  if (!next) {
                    setListeningEnabled(false);
                    stopRecognition();
                  }
                  return next;
                });
              }}
              onToggleCameraEnabled={() => void handleToggleCameraEnabled()}
              onLeave={handleLeave}
              onStartInterview={() => void handleStartInterview()}
              onToggleListening={() => void handleToggleListening()}
              onReplayQuestion={() => latestQuestion && speak(latestQuestion)}
              onToggleAutoVoice={() => setAutoVoice((previous) => !previous)}
              condensed
            />
          </div>

          <div className="absolute right-4 top-4 z-20 rounded-xl border border-slate-700/80 bg-slate-900/78 p-2 text-xs text-slate-200">
            <p>System Mic: {micEnabled ? "enabled" : "muted"}</p>
            <p>Mic Permission: {micPermissionDenied ? "blocked" : "ok"}</p>
            <p>Camera: {cameraEnabled && media.cameraOn ? "on" : "off"}</p>
            <p>Camera Permission: {media.permissionDenied ? "blocked" : "ok"}</p>
            <p>AI voice: {isSpeaking ? "speaking" : "idle"}</p>
            <p>Listener: {isListening ? "active" : "idle"}</p>
          </div>

          <div className="absolute bottom-4 left-1/2 z-20 w-[52%] min-w-[260px] max-w-[520px] -translate-x-1/2 rounded-xl border border-slate-700/80 bg-slate-900/78 p-2">
            <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-400">Single Answer Input</p>
            <div className="flex items-center gap-2">
              <Input
                value={quickReply}
                onChange={(event) => setQuickReply(event.target.value)}
                placeholder="Provide one concise answer..."
                maxLength={420}
                className="bg-slate-950/85"
              />
              <Button onClick={handleQuickSend} disabled={!quickReply.trim() || disabled || isProcessing}>
                Send
              </Button>
            </div>
            {lastCapturedTranscript ? (
              <p className="mt-1 max-h-10 overflow-hidden text-[11px] text-slate-300">Voice: {lastCapturedTranscript}</p>
            ) : null}
            {lastSubmittedAnswer ? (
              <p className="mt-1 max-h-10 overflow-hidden text-[11px] text-cyan-100">Sent: {lastSubmittedAnswer}</p>
            ) : null}
          </div>
        </div>

        <div className="mt-3 space-y-2">
          {wsError ? <Alert variant="error">{wsError}</Alert> : null}
          {localError ? <Alert variant="error">{localError}</Alert> : null}
          {micPermissionDenied ? (
            <Alert variant="error">
              Microphone access is blocked for this site. Allow it in browser settings and reload interview.
            </Alert>
          ) : null}
          {media.permissionDenied ? (
            <Alert variant="error">
              Camera access is blocked for this site. Allow camera access in browser settings.
            </Alert>
          ) : null}
          {media.error ? <Alert variant="error">{media.error}</Alert> : null}
          {recognitionError ? <Alert variant="error">{recognitionError}</Alert> : null}
          {!recognitionSupported ? (
            <Alert variant="info">
              Speech recognition is unavailable in this browser. Use single answer input.
            </Alert>
          ) : null}
          {!speechSupported ? (
            <Alert variant="info">
              Text-to-speech is unavailable in this browser. AI question audio playback is disabled.
            </Alert>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
