interface ValidationIssue {
  loc?: unknown;
  msg?: unknown;
}

function isValidationIssue(value: unknown): value is ValidationIssue {
  return typeof value === "object" && value !== null;
}

export async function readApiError(
  response: Response,
  fallback: string,
): Promise<Error> {
  let detail: unknown;

  try {
    const body: unknown = await response.json();

    if (typeof body === "object" && body !== null && "detail" in body) {
      detail = body.detail;
    }
  } catch {
    // Auch eine leere oder ungültige Fehlerantwort bleibt behandelbar.
  }

  if (typeof detail === "string" && detail.trim() !== "") {
    return new Error(detail);
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .filter(isValidationIssue)
      .map((issue) => issue.msg)
      .filter((message): message is string => typeof message === "string");

    if (messages.length > 0) {
      return new Error(messages.join("\n"));
    }
  }

  return new Error(`${fallback}: HTTP ${response.status}`);
}
