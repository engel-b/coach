import type { TrainingRecommendation } from '../training/types'


export async function getTrainingRecommendation(
  personId: number,
): Promise<TrainingRecommendation> {
  const response = await fetch(
    `/api/persons/${personId}/training-recommendation`,
  )

  if (!response.ok) {
    throw new Error(
      `Could not load training recommendation: HTTP ${response.status}`,
    )
  }

  return (await response.json()) as TrainingRecommendation
}

