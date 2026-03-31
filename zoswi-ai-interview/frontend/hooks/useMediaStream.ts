"use client";

import { useCallback, useEffect, useState } from "react";

type MediaStartOptions = {
  video?: boolean;
  audio?: boolean;
};

export function useMediaStream() {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [micOn, setMicOn] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stop = useCallback(() => {
    setStream((previous) => {
      if (previous) {
        previous.getTracks().forEach((track) => track.stop());
      }
      return null;
    });
    setIsActive(false);
    setMicOn(false);
    setCameraOn(false);
  }, []);

  const start = useCallback(async (options?: MediaStartOptions) => {
    const enableVideo = options?.video ?? true;
    const enableAudio = options?.audio ?? true;
    setError(null);
    setPermissionDenied(false);

    try {
      const media = await navigator.mediaDevices.getUserMedia({
        video: enableVideo ? { width: { ideal: 1280 }, height: { ideal: 720 } } : false,
        audio: enableAudio
      });

      const audioTrack = media.getAudioTracks()[0];
      const videoTrack = media.getVideoTracks()[0];
      setStream(media);
      setIsActive(true);
      setMicOn(Boolean(audioTrack?.enabled));
      setCameraOn(Boolean(videoTrack?.enabled));
      return true;
    } catch (startError) {
      const message =
        startError instanceof Error
          ? startError.message
          : "Could not access camera/microphone.";
      if (message.toLowerCase().includes("denied") || message.toLowerCase().includes("permission")) {
        setPermissionDenied(true);
      }
      setError(message);
      setIsActive(false);
      return false;
    }
  }, []);

  const toggleMic = useCallback(() => {
    if (!stream) return false;
    const tracks = stream.getAudioTracks();
    if (tracks.length === 0) return false;
    const next = !tracks[0].enabled;
    tracks.forEach((track) => {
      track.enabled = next;
    });
    setMicOn(next);
    return next;
  }, [stream]);

  const toggleCamera = useCallback(() => {
    if (!stream) return false;
    const tracks = stream.getVideoTracks();
    if (tracks.length === 0) return false;
    const next = !tracks[0].enabled;
    tracks.forEach((track) => {
      track.enabled = next;
    });
    setCameraOn(next);
    return next;
  }, [stream]);

  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    stream,
    isActive,
    micOn,
    cameraOn,
    permissionDenied,
    error,
    start,
    stop,
    toggleMic,
    toggleCamera
  };
}
