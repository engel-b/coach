import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    // Damit der Vite-Entwicklungsserver auch von einem anderen
    // Rechner im lokalen Netzwerk erreichbar ist.
    host: "0.0.0.0",

    proxy: {
      // Alle HTTP-Aufrufe nach /api werden an FastAPI weitergeleitet.
      //
      // Frontend:
      //   GET /api/devices
      //
      // wird dadurch zu:
      //   GET http://127.0.0.1:8000/api/devices
      //
      // Vergleich zur Java-Welt:
      // ungefähr ein lokaler Reverse Proxy für die Entwicklungsumgebung.
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      // Trainingsvideos werden vom Backend aus dem konfigurierten
      // HEALTH_COACH_VIDEO_DIR unter /videos ausgeliefert.
      "/videos": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      // Das brauchen wir wenig später für unseren
      // Backend -> Frontend WebSocket.
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
    },
  },
});
