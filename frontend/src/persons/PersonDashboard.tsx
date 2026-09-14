import { useEffect, useMemo, useState } from "react";

import { getCheckInHistory, getLatestCheckIn } from "../api/check-ins";
import { getPersonProfile } from "../api/persons";
import { getTrainingRecommendation } from "../api/training";
import { getWorkoutHistory } from "../api/workouts";
import type { CheckIn } from "../check-in/types";
import { WeightGoalProgress } from "../training/WeightGoalProgress";
import type { TrainingRecommendation } from "../training/types";
import {
  recommendationReasonLabels,
  weightTrendLabel,
  workoutTitle,
} from "../training/recommendationPresentation";
import type { Workout } from "../workout/types";
import type { Person, PersonProfile } from "./types";

interface PersonDashboardProps {
  person: Person;
  onStartCheckIn: () => void;
  onChangePerson: () => void;
  onEditProfile: () => void;
}

interface DashboardData {
  profile: PersonProfile | null;
  latestCheckIn: CheckIn | null;
  checkIns: CheckIn[];
  workouts: Workout[];
  recommendation: TrainingRecommendation | null;
}

const EMPTY_DASHBOARD_DATA: DashboardData = {
  profile: null,
  latestCheckIn: null,
  checkIns: [],
  workouts: [],
  recommendation: null,
};

function formatDuration(elapsedSeconds: number): string {
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function statusLabel(status: Workout["status"]): string {
  switch (status) {
    case "running":
      return "Läuft";
    case "completed":
      return "Abgeschlossen";
    case "aborted":
      return "Abgebrochen";
  }
}

function formatWeight(value: number): string {
  return value.toLocaleString("de-DE", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function createWeightPoints(checkIns: CheckIn[]): CheckIn[] {
  return checkIns
    .filter((checkIn) => checkIn.currentWeightKg !== null)
    .sort(
      (left, right) =>
        new Date(left.timestamp).getTime() -
        new Date(right.timestamp).getTime(),
    );
}

interface WeightChartProps {
  checkIns: CheckIn[];
  startWeightKg: number | null;
  targetWeightKg: number | null;
}

function WeightChart({
  checkIns,
  startWeightKg,
  targetWeightKg,
}: WeightChartProps) {
  const points = useMemo(() => createWeightPoints(checkIns), [checkIns]);

  if (points.length < 2) {
    return (
      <div className="dashboard-chart-empty">
        <strong>Noch kein Verlauf</strong>
        <span>
          Ab zwei Gewichtsmessungen zeigt der Coach hier deine Entwicklung.
        </span>
      </div>
    );
  }

  /*
   * Start- und Zielgewicht gehören zur Skala des Diagramms.
   *
   * Java-Analogie: Statt nur die Messwerte in eine Liste zu legen und daraus
   * min/max zu bestimmen, nehmen wir hier noch zwei optionale Referenzwerte in
   * dieselbe Berechnung auf. So liegen beide horizontalen Linien garantiert
   * innerhalb des sichtbaren Diagrammbereichs.
   */
  const weights = points.map((point) => point.currentWeightKg as number);
  const scaleWeights = [
    ...weights,
    ...(startWeightKg === null ? [] : [startWeightKg]),
    ...(targetWeightKg === null ? [] : [targetWeightKg]),
  ];

  const minimum = Math.min(...scaleWeights);
  const maximum = Math.max(...scaleWeights);
  const padding = Math.max(0.5, (maximum - minimum) * 0.12);
  const chartMinimum = minimum - padding;
  const chartMaximum = maximum + padding;
  const chartRange = Math.max(0.1, chartMaximum - chartMinimum);

  const scaleTicks = [0, 0.25, 0.5, 0.75, 1].map((position) => ({
    position,
    value: chartMaximum - chartRange * position,
  }));

  const toChartY = (weight: number): number =>
    100 - ((weight - chartMinimum) / chartRange) * 100;

  const path = points
    .map((point, index) => {
      const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100;
      const weight = point.currentWeightKg as number;
      const y = toChartY(weight);

      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <div className="dashboard-weight-chart" aria-label="Gewichtsverlauf">
      <div className="dashboard-weight-chart-legend">
        {startWeightKg !== null && (
          <span className="dashboard-weight-reference start">
            <i aria-hidden="true" />
            Start {formatWeight(startWeightKg)} kg
          </span>
        )}
        {targetWeightKg !== null && (
          <span className="dashboard-weight-reference target">
            <i aria-hidden="true" />
            Ziel {formatWeight(targetWeightKg)} kg
          </span>
        )}
      </div>

      <div className="dashboard-weight-chart-plot">
        <div className="dashboard-weight-chart-scale" aria-hidden="true">
          {scaleTicks.map((tick) => (
            <span
              key={tick.position}
              style={{ top: `${tick.position * 100}%` }}
            >
              {formatWeight(tick.value)} kg
            </span>
          ))}
        </div>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img">
          <line x1="0" y1="25" x2="100" y2="25" />
          <line x1="0" y1="50" x2="100" y2="50" />
          <line x1="0" y1="75" x2="100" y2="75" />

          {startWeightKg !== null && (
            <line
              className="dashboard-weight-reference-line start"
              x1="0"
              y1={toChartY(startWeightKg)}
              x2="100"
              y2={toChartY(startWeightKg)}
            />
          )}

          {targetWeightKg !== null && (
            <line
              className="dashboard-weight-reference-line target"
              x1="0"
              y1={toChartY(targetWeightKg)}
              x2="100"
              y2={toChartY(targetWeightKg)}
            />
          )}

          <path d={path} />
        </svg>
        <div className="dashboard-weight-chart-points" aria-hidden="true">
          {points.map((point, index) => {
            const x = (index / (points.length - 1)) * 100;
            const weight = point.currentWeightKg as number;
            const y = toChartY(weight);

            return (
              <span
                key={point.timestamp}
                className="dashboard-weight-chart-point"
                style={{
                  left: `${x}%`,
                  top: `${y}%`,
                }}
              />
            );
          })}
        </div>
      </div>
      <div className="dashboard-chart-axis">
        <span>{formatDate(points[0].timestamp)}</span>
        <span>{formatDate(points[points.length - 1].timestamp)}</span>
      </div>
    </div>
  );
}

function CoachAvatar() {
  return (
    <div className="dashboard-coach-avatar" aria-hidden="true">
      <div className="dashboard-coach-face">DFC</div>
      <span>Coach</span>
    </div>
  );
}

function coachMessage(latestCheckIn: CheckIn | null, workouts: Workout[]) {
  const completedWorkouts = workouts.filter(
    (workout) => workout.status === "completed",
  ).length;

  if (latestCheckIn === null) {
    return {
      title: "Bereit, wenn du es bist.",
      text: "Starte deinen Check-in. Danach kann ich deine Tagesform einordnen und dir die passende Trainingsempfehlung geben.",
    };
  }

  const signals: string[] = [];

  if (latestCheckIn.energy >= 4) {
    signals.push("deine Energie ist gut");
  } else if (latestCheckIn.energy <= 2) {
    signals.push("deine Energie ist heute eher niedrig");
  }

  if (latestCheckIn.recovery >= 4) {
    signals.push("du fühlst dich gut erholt");
  } else if (latestCheckIn.recovery <= 2) {
    signals.push("deine Erholung ist noch nicht optimal");
  }

  if (latestCheckIn.stress >= 4) {
    signals.push("dein Stresslevel ist erhöht");
  }

  const checkInSummary =
    signals.length > 0
      ? `Dein letzter Check-in zeigt: ${signals.join(" und ")}.`
      : "Dein letzter Check-in liegt vor und liefert eine solide Grundlage für die nächste Empfehlung.";

  const workoutSummary =
    completedWorkouts > 0
      ? ` In der geladenen Historie sind ${completedWorkouts} abgeschlossene Trainings enthalten.`
      : "";

  return {
    title: "Dein aktueller Stand",
    text: `${checkInSummary}${workoutSummary}`,
  };
}

function badgeDefinitions(data: DashboardData) {
  const completedWorkouts = data.workouts.filter(
    (workout) => workout.status === "completed",
  ).length;

  return [
    {
      title: "Profil eingerichtet",
      detail: "Deine Basisdaten sind hinterlegt.",
      earned: data.profile !== null,
    },
    {
      title: "Erster Check-in",
      detail: "Die erste Tagesform wurde erfasst.",
      earned: data.latestCheckIn !== null,
    },
    {
      title: "Erstes Training",
      detail: "Ein Training wurde abgeschlossen.",
      earned: completedWorkouts >= 1,
    },
    {
      title: "5 Trainings",
      detail: "Fünf Trainings erfolgreich abgeschlossen.",
      earned: completedWorkouts >= 5,
    },
  ];
}

export function PersonDashboard({
  person,
  onStartCheckIn,
  onChangePerson,
  onEditProfile,
}: PersonDashboardProps) {
  const [data, setData] = useState<DashboardData>(EMPTY_DASHBOARD_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard(): Promise<void> {
      setLoading(true);
      setError(null);

      try {
        /*
         * Die Check-in-Historie ist bewusst fehlertolerant.
         * Solange der neue History-Endpunkt im Backend noch nicht existiert,
         * funktioniert das restliche Dashboard trotzdem vollständig.
         */
        const [profile, latestCheckIn, workouts, checkIns, recommendation] =
          await Promise.all([
            getPersonProfile(person.id),
            getLatestCheckIn(person.id),
            getWorkoutHistory(person.id, 10),
            getCheckInHistory(person.id, 90).catch(() => []),
            getTrainingRecommendation(person.id).catch(() => null),
          ]);

        if (!cancelled) {
          setData({
            profile,
            latestCheckIn,
            workouts,
            checkIns,
            recommendation,
          });
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Dashboard konnte nicht geladen werden.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [person.id]);

  const weightPoints = useMemo(
    () => createWeightPoints(data.checkIns),
    [data.checkIns],
  );
  const latestWeight =
    data.latestCheckIn?.currentWeightKg ??
    weightPoints[weightPoints.length - 1]?.currentWeightKg ??
    null;
  const firstWeight = weightPoints[0]?.currentWeightKg ?? null;
  const weightChange =
    latestWeight !== null && firstWeight !== null
      ? latestWeight - firstWeight
      : null;
  const coach = coachMessage(data.latestCheckIn, data.workouts);
  const recommendationReasonTags =
    data.recommendation === null
      ? []
      : recommendationReasonLabels(data.recommendation);
  const recommendationWeightTrend =
    data.recommendation === null ? null : weightTrendLabel(data.recommendation);
  const badges = badgeDefinitions(data);

  return (
    <section className="person-dashboard">
      <header className="dashboard-header">
        <div>
          <div className="eyebrow">DIGITAL FITNESS COACH</div>
          <h1>Hallo {person.displayName}</h1>
          <p>Dein Überblick für Training, Gesundheit und Fortschritt.</p>
        </div>

        <div className="dashboard-header-actions">
          <button
            type="button"
            className="secondary-action"
            onClick={onEditProfile}
          >
            Profil bearbeiten
          </button>
          <button
            type="button"
            className="change-person"
            onClick={onChangePerson}
          >
            Person wechseln
          </button>
        </div>
      </header>

      <section className="dashboard-check-in-card">
        <div>
          <div className="dashboard-section-label">HEUTE</div>
          <h2>Wie geht es dir?</h2>
          <p>
            Ein kurzer Check-in aktualisiert deine Tagesform und bildet die
            Grundlage für die heutige Trainingsempfehlung.
          </p>
        </div>

        <button
          type="button"
          className="primary-action dashboard-primary-action"
          onClick={onStartCheckIn}
        >
          Check-in starten
        </button>
      </section>

      {error !== null && <div className="error-message">{error}</div>}

      <div className="dashboard-main-grid">
        <section className="dashboard-card dashboard-weight-card">
          <div className="dashboard-card-header">
            <div>
              <div className="dashboard-section-label">FORTSCHRITT</div>
              <h2>Gewichtsverlauf</h2>
            </div>
            <span className="dashboard-card-meta">letzte Messungen</span>
          </div>

          {loading ? (
            <div className="dashboard-card-loading">Werte werden geladen …</div>
          ) : (
            <>
              <div className="dashboard-weight-stats">
                <div>
                  <span>Aktuell</span>
                  <strong>
                    {latestWeight === null
                      ? "–"
                      : `${formatWeight(latestWeight)} kg`}
                  </strong>
                </div>
                <div>
                  <span>Veränderung</span>
                  <strong>
                    {weightChange === null
                      ? "–"
                      : `${weightChange > 0 ? "+" : ""}${formatWeight(weightChange)} kg`}
                  </strong>
                </div>
                <div>
                  <span>Ziel</span>
                  <strong>
                    {data.profile?.targetWeightKg === null ||
                    data.profile?.targetWeightKg === undefined
                      ? "–"
                      : `${formatWeight(data.profile.targetWeightKg)} kg`}
                  </strong>
                </div>
              </div>

              {data.recommendation !== null && (
                <WeightGoalProgress
                  recommendation={data.recommendation}
                  compact
                />
              )}

              <WeightChart
                checkIns={data.checkIns}
                startWeightKg={data.profile?.startWeightKg ?? null}
                targetWeightKg={data.profile?.targetWeightKg ?? null}
              />
            </>
          )}
        </section>

        <aside className="dashboard-card dashboard-coach-card">
          <div className="dashboard-coach-heading">
            <CoachAvatar />
            <div>
              <div className="dashboard-section-label">DEIN COACH</div>
              <h2>{coach.title}</h2>
            </div>
          </div>

          <p className="dashboard-coach-text">{coach.text}</p>

          <div className="dashboard-coach-recommendation">
            <span>Empfehlung</span>

            {data.recommendation === null ? (
              <strong>
                Starte den Check-in, damit ich dein Training passend zur aktuellen
                Tagesform empfehlen kann.
              </strong>
            ) : (
              <>
                <strong>
                  {workoutTitle(data.recommendation.workoutType)} ·{" "}
                  {data.recommendation.totalDurationMinutes} min
                </strong>
                <p className="dashboard-coach-reason">
                  {data.recommendation.reason}
                </p>

                {recommendationWeightTrend !== null && (
                  <div className="dashboard-coach-trend">
                    <span>Gewichtstrend</span>
                    <strong>{recommendationWeightTrend}</strong>
                  </div>
                )}

                {recommendationReasonTags.length > 0 && (
                  <div className="dashboard-coach-reason-tags">
                    {recommendationReasonTags.map((label) => (
                      <span key={label}>{label}</span>
                    ))}
                  </div>
                )}

                <small>
                  Basierend auf deinem letzten Check-in. Für eine aktuelle
                  Empfehlung bitte neu einchecken.
                </small>
              </>
            )}
          </div>
        </aside>
      </div>

      <section className="dashboard-card dashboard-badges-card">
        <div className="dashboard-card-header">
          <div>
            <div className="dashboard-section-label">FORTSCHRITT</div>
            <h2>Deine Badges</h2>
          </div>
        </div>

        <div className="dashboard-badge-grid">
          {badges.map((badge) => (
            <article
              key={badge.title}
              className={
                badge.earned
                  ? "dashboard-badge earned"
                  : "dashboard-badge locked"
              }
            >
              <div className="dashboard-badge-icon">
                {badge.earned ? "✓" : "·"}
              </div>
              <div>
                <strong>{badge.title}</strong>
                <span>{badge.detail}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="dashboard-card dashboard-history-card">
        <div className="dashboard-card-header">
          <div>
            <div className="dashboard-section-label">TRAINING</div>
            <h2>Letzte Trainings</h2>
          </div>
        </div>

        {loading ? (
          <div className="dashboard-card-loading">
            Trainings werden geladen …
          </div>
        ) : data.workouts.length === 0 ? (
          <div className="dashboard-chart-empty">
            <strong>Noch keine Trainings vorhanden.</strong>
            <span>Dein erster abgeschlossener Workout erscheint hier.</span>
          </div>
        ) : (
          <div className="dashboard-workout-list">
            {data.workouts.map((workout) => (
              <article key={workout.id} className="dashboard-workout-row">
                <div className="dashboard-workout-date">
                  {formatDate(workout.startedAt)}
                </div>
                <div className="dashboard-workout-name">Training</div>
                <div className={`dashboard-workout-status ${workout.status}`}>
                  {statusLabel(workout.status)}
                </div>
                <strong>{formatDuration(workout.elapsedSeconds)}</strong>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
