import type {
  HeartRateHistory,
  LoadAdjustedHeartRateTrend,
  WorkoutType,
} from "./types";

export interface HeartRateHistoryPresentation {
  scope: string | null;
  statusText: string;
  responseTrendText: string | null;
  loadAdjustedTrendText: string | null;
}

function workoutTypeScope(workoutType: WorkoutType | null): string | null {
  switch (workoutType) {
    case "base_endurance":
      return "Auswertung nur für Grundlagen-Einheiten.";
    case "recovery":
      return "Auswertung nur für Recovery-Einheiten.";
    case "moderate":
      return "Auswertung nur für moderate Einheiten.";
    case null:
      return null;
  }
}

function statusText(history: HeartRateHistory): string {
  switch (history.status) {
    case "mostly_in_target":
      return `In ${history.workoutCount} vergleichbaren Workouts lag deine Herzfrequenz überwiegend im Zielbereich.`;
    case "mostly_above_target":
      return `In ${history.workoutCount} vergleichbaren Workouts lag deine Herzfrequenz häufig oberhalb des Zielbereichs. Deshalb wird die heutige Dauer bei Bedarf konservativ begrenzt; Zielpuls- und Safety-Grenzen werden nicht angehoben.`;
    case "mostly_below_target":
      return `In ${history.workoutCount} vergleichbaren Workouts lag deine Herzfrequenz häufig unterhalb des Zielbereichs. Daraus wird nicht automatisch mehr Intensität abgeleitet.`;
    case "mixed":
      return `Die letzten ${history.workoutCount} vergleichbaren Workouts zeigen noch kein eindeutiges Herzfrequenzmuster.`;
    case "insufficient_data":
      return "";
  }
}

function responseTrendText(history: HeartRateHistory): string | null {
  if (history.responseTrend === "insufficient_data") {
    return null;
  }

  const observation =
    history.responseTrend === "lower"
      ? "Bei den neueren vergleichbaren Workouts lag deine durchschnittliche Herzfrequenz relativ zum jeweiligen Zielbereich niedriger als bei den älteren."
      : history.responseTrend === "higher"
        ? "Bei den neueren vergleichbaren Workouts lag deine durchschnittliche Herzfrequenz relativ zum jeweiligen Zielbereich höher als bei den älteren."
        : "Die durchschnittliche Herzfrequenz relativ zum jeweiligen Zielbereich ist über die vergleichbaren Workouts weitgehend stabil.";

  const change =
    history.targetPositionChangePoints === null
      ? ""
      : ` Veränderung: ${history.targetPositionChangePoints > 0 ? "+" : ""}${history.targetPositionChangePoints} Prozentpunkte.`;

  return `${observation}${change} Diese Beobachtung ist rein beschreibend und erhöht die Trainingsintensität nicht automatisch.`;
}

function loadAdjustedObservation(trend: LoadAdjustedHeartRateTrend): string {
  switch (trend) {
    case "lower_at_similar_power":
      return "Die Herzfrequenz-Reaktion war bei den neueren Einheiten niedriger, obwohl die durchschnittliche Bike-Leistung ähnlich blieb.";
    case "higher_at_similar_power":
      return "Die Herzfrequenz-Reaktion war bei den neueren Einheiten höher, obwohl die durchschnittliche Bike-Leistung ähnlich blieb.";
    case "stable_at_similar_power":
      return "Herzfrequenz-Reaktion und durchschnittliche Bike-Leistung blieben über die vergleichbaren Einheiten weitgehend stabil.";
    case "lower_with_lower_power":
      return "Die niedrigere Herzfrequenz ging mit einer niedrigeren durchschnittlichen Bike-Leistung einher; deshalb wird sie nicht als günstigere Reaktion interpretiert.";
    case "higher_with_higher_power":
      return "Die höhere Herzfrequenz ging mit einer höheren durchschnittlichen Bike-Leistung einher; die Belastung war also nicht vergleichbar.";
    case "load_changed":
      return "Die Bike-Leistung hat sich zwischen älteren und neueren Einheiten deutlich verändert; der Herzfrequenz-Trend wird deshalb nicht isoliert interpretiert.";
    case "insufficient_data":
      return "";
  }
}

function loadAdjustedTrendText(history: HeartRateHistory): string | null {
  if (history.loadAdjustedTrend === "insufficient_data") {
    return null;
  }

  const powerChange =
    history.powerChangePercent === null
      ? ""
      : ` Leistungsänderung: ${history.powerChangePercent > 0 ? "+" : ""}${history.powerChangePercent} %.`;
  const medianPower =
    history.medianPowerW === null
      ? ""
      : ` Median der vergleichbaren Einheiten: ${history.medianPowerW} W.`;

  return `${loadAdjustedObservation(history.loadAdjustedTrend)}${powerChange}${medianPower} Auch diese Beobachtung ist rein deskriptiv und verändert die Trainingsintensität nicht automatisch.`;
}

export function heartRateHistoryPresentation(
  history: HeartRateHistory | null,
): HeartRateHistoryPresentation | null {
  if (history === null || history.status === "insufficient_data") {
    return null;
  }

  return {
    scope: workoutTypeScope(history.workoutType),
    statusText: statusText(history),
    responseTrendText: responseTrendText(history),
    loadAdjustedTrendText: loadAdjustedTrendText(history),
  };
}
