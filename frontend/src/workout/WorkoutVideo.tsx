import { useEffect, useRef } from "react";

interface WorkoutVideoProps {
  src: string;
  paused: boolean;
  playbackRate: number;
}

export function WorkoutVideo({ src, paused, playbackRate }: WorkoutVideoProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  /*
   * WorkoutView bleibt die Source of Truth.
   *
   * Diese Komponente setzt lediglich den gewünschten
   * Zustand auf dem echten HTMLVideoElement um.
   *
   * Das ist ein Seiteneffekt auf ein Browser-Objekt und
   * gehört deshalb in useEffect(), nicht in den Render.
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
         * Kein Fehlerdialog nötig.
         *
         * Falls Autoplay doch blockiert wird, bleibt die
         * Trainingsanwendung weiterhin benutzbar.
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
    />
  );
}
