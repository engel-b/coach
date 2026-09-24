import type { LoadResponse } from "./types";

export function loadResponsePresentation(
  context: LoadResponse | null,
): string | null {
  if (context === null || context.status === "insufficient_data") {
    return null;
  }

  const observation = {
    stable:
      "Herzfrequenz und Bike-Belastung wirken in den vergleichbaren Einheiten weitgehend stabil.",
    lower_hr_at_similar_load:
      "Die Herzfrequenz war bei ähnlicher Bike-Leistung niedriger als in älteren vergleichbaren Einheiten.",
    higher_hr_at_similar_load:
      "Die Herzfrequenz war bei ähnlicher Bike-Leistung höher als in älteren vergleichbaren Einheiten.",
    lower_load:
      "Die niedrigere Herzfrequenz trat zusammen mit einer niedrigeren Bike-Belastung auf.",
    higher_load:
      "Die höhere Herzfrequenz trat zusammen mit einer höheren Bike-Belastung auf.",
    mixed:
      "Die Belastungsreaktion ist derzeit gemischt, weil sich Herzfrequenz und Bike-Belastung nicht eindeutig gemeinsam entwickelt haben.",
  }[context.status];

  const bikeDetails = [
    context.medianPowerW === null
      ? null
      : `${context.medianPowerW} W Medianleistung`,
    context.medianCadenceRpm === null
      ? null
      : `${context.medianCadenceRpm.toFixed(1)} rpm Mediankadenz`,
  ].filter((value): value is string => value !== null);

  const readiness = context.readinessCaution
    ? " Die heutige Readiness enthält zusätzlich ein konservatives Belastungssignal."
    : "";
  const details =
    bikeDetails.length > 0 ? ` Basis: ${bikeDetails.join(", ")}.` : "";

  return `${observation}${details}${readiness} Diese Einordnung ist rein deskriptiv und verändert die Trainingsintensität nicht automatisch.`;
}
