import { readApiError } from "./apiError";

export async function synthesizeSpeech(
  text: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const response = await fetch("/api/speech/synthesize", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
    signal,
  });

  if (!response.ok) {
    throw await readApiError(
      response,
      "Sprachausgabe konnte nicht erzeugt werden",
    );
  }

  return response.blob();
}
