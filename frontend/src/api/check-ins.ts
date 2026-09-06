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
