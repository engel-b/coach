import { useEffect, useRef } from "react";

interface WorkoutVideoProps {
  src: string;
  paused: boolean;
  playbackRate: number;
  initialPositionSeconds: number;
  onPositionChange: (positionSeconds: number) => void;
}

export function WorkoutVideo({
  src,
  paused,
  playbackRate,
  initialPositionSeconds,
  onPositionChange,
}: WorkoutVideoProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const initialPositionAppliedRef = useRef(false);

  /*
   * Die gespeicherte Videoposition wird genau einmal gesetzt,
   * sobald der Browser die Metadaten des Videos kennt.
   *
   * Erst dann kennen wir insbesondere video.duration und können
   * eine gespeicherte Position sinnvoll begrenzen.
   *
   * Das Ref verhindert, dass spätere React-Renders das laufende
   * Video wieder auf die Startposition zurücksetzen.
   */
  function handleLoadedMetadata(): void {
    const videoElement = videoRef.current;

    if (videoElement === null || initialPositionAppliedRef.current) {
      return;
    }

    const duration = videoElement.duration;

    if (
      Number.isFinite(initialPositionSeconds) &&
      initialPositionSeconds >= 0 &&
      Number.isFinite(duration) &&
      duration > 0
    ) {
      /*
       * Da das Video mit "loop" läuft, speichern wir eine Position
       * innerhalb dieses Videos.
       *
       * modulo behandelt auch den Fall, dass sich die Videolänge
       * zwischen zwei Trainings geändert hat.
       */
      videoElement.currentTime = initialPositionSeconds % duration;
    }

    initialPositionAppliedRef.current = true;

    onPositionChange(videoElement.currentTime);
  }

  /*
   * timeupdate kommt vom Browser während der Wiedergabe.
   *
   * WorkoutVideo besitzt die Browser-API, aber nicht den
   * fachlichen Workout-Zustand. Deshalb melden wir nur die
   * aktuelle Position nach außen.
   */
  function handleTimeUpdate(): void {
    const videoElement = videoRef.current;

    if (videoElement === null) {
      return;
    }

    onPositionChange(videoElement.currentTime);
  }

  /*
   * WorkoutView bleibt die Source of Truth für Play/Pause.
   *
   * Diese Komponente setzt lediglich den gewünschten Zustand
   * auf dem echten HTMLVideoElement um.
   */
  useEffect(() => {
    const videoElement = videoRef.current;

    if (videoElement === null) {
      return;
    }

    videoElement.playbackRate = playbackRate;

    if (paused) {
      if (!videoElement.paused) {
        videoElement.pause();
      }

      return;
    }

    if (videoElement.paused) {
      /*
       * play() liefert ein Promise.
       *
       * Browser können Autoplay grundsätzlich blockieren.
       * Da das Video muted läuft, ist Autoplay bei modernen
       * Browsern normalerweise erlaubt.
       */
      void videoElement.play().catch(() => {
        /*
         * Audio-/Autoplay-Regeln des Browsers dürfen das
         * eigentliche Workout nicht blockieren.
         */
      });
    }
  }, [paused, playbackRate]);

  return (
    <video
      ref={videoRef}
      className="workout-video"
      src={src}
      autoPlay
      muted
      loop
      playsInline
      preload="auto"
      onLoadedMetadata={handleLoadedMetadata}
      onTimeUpdate={handleTimeUpdate}
    />
  );
}
