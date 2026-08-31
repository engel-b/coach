import { useState } from 'react'


interface WorkoutVideoProps {
  src: string
  paused: boolean
}


export function WorkoutVideo({
  src,
  paused,
}: WorkoutVideoProps) {
  const [videoElement, setVideoElement] =
    useState<HTMLVideoElement | null>(null)

  /*
   * Das Workout entscheidet, ob pausiert ist.
   *
   * Das Video besitzt bewusst keinen eigenen Pause-State.
   * Damit haben wir nur eine "Source of Truth":
   *
   * WorkoutView.paused
   *
   * Java-Vergleich:
   * WorkoutVideo ist hier eher eine View/Presentation-Komponente
   * und kein eigener fachlicher Service.
   */
  if (videoElement !== null) {
    if (paused && !videoElement.paused) {
      videoElement.pause()
    }

    if (!paused && videoElement.paused) {
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
      })
    }
  }

  return (
    <video
      ref={setVideoElement}
      className="workout-video"
      src={src}
      autoPlay
      muted
      loop
      playsInline
      preload="auto"
    />
  )
}
