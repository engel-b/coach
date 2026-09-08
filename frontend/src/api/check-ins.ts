import type { CheckIn, CheckInRequest } from "../check-in/types";

export async function createCheckIn(
  personId: number,
  request: CheckInRequest,
): Promise<CheckIn> {
  const response = await fetch(`/api/persons/${personId}/check-ins`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Could not create check-in: HTTP ${response.status}`);
  }

  return (await response.json()) as CheckIn;
}

export async function getLatestCheckIn(
  personId: number,
): Promise<CheckIn | null> {
  const response = await fetch(`/api/persons/${personId}/check-ins/latest`);

  if (!response.ok) {
    throw new Error("Der letzte Check-in konnte nicht geladen werden.");
  }

  return (await response.json()) as CheckIn | null;
}

export async function getCheckInHistory(
  personId: number,
  limit = 90,
): Promise<CheckIn[]> {
  const response = await fetch(
    `/api/persons/${personId}/check-ins?limit=${limit}`,
  );

  if (!response.ok) {
    throw new Error(
      `Check-in-Verlauf konnte nicht geladen werden: HTTP ${response.status}`,
    );
  }

  return (await response.json()) as CheckIn[];
}
