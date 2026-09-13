export type CheckInField =
  | "energy"
  | "recovery"
  | "muscleSoreness"
  | "stress"
  | "availableTrainingMinutes";

export interface CheckInOption {
  value: number;
  label: string;
}

export interface CheckInQuestion {
  field: CheckInField;
  title: string;
  description: string;
  options: CheckInOption[];
}

const scaleOptions: CheckInOption[] = [
  { value: 1, label: "Sehr niedrig" },
  { value: 2, label: "Niedrig" },
  { value: 3, label: "Normal" },
  { value: 4, label: "Gut" },
  { value: 5, label: "Sehr gut" },
];

export const checkInQuestions: CheckInQuestion[] = [
  {
    field: "energy",
    title: "Wie viel Energie hast du heute?",
    description: "1 = sehr wenig, 5 = sehr viel",
    options: scaleOptions,
  },
  {
    field: "recovery",
    title: "Wie gut fühlst du dich erholt?",
    description: "1 = überhaupt nicht, 5 = vollständig erholt",
    options: scaleOptions,
  },
  {
    field: "muscleSoreness",
    title: "Wie stark ist dein Muskelkater?",
    description: "1 = keiner, 5 = sehr stark",
    options: [
      { value: 1, label: "Keiner" },
      { value: 2, label: "Leicht" },
      { value: 3, label: "Mittel" },
      { value: 4, label: "Stark" },
      { value: 5, label: "Sehr stark" },
    ],
  },
  {
    field: "stress",
    title: "Wie hoch ist dein Stresslevel?",
    description: "1 = entspannt, 5 = sehr gestresst",
    options: [
      { value: 1, label: "Entspannt" },
      { value: 2, label: "Niedrig" },
      { value: 3, label: "Mittel" },
      { value: 4, label: "Hoch" },
      { value: 5, label: "Sehr hoch" },
    ],
  },
  {
    field: "availableTrainingMinutes",
    title: "Wie viel Zeit hast du heute?",
    description: "Wie lange möchtest du maximal trainieren?",
    options: [
      { value: 15, label: "15 min" },
      { value: 20, label: "20 min" },
      { value: 25, label: "25 min" },
      { value: 30, label: "30 min" },
    ],
  },
];
