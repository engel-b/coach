import { describe, expect, it } from 'vitest'

import {
  applyNativeDistanceSample,
  createWorkoutDistanceState,
} from './workoutDistance'

describe('workoutDistance', () => {
  it('starts without accumulated distance', () => {
    expect(createWorkoutDistanceState()).toEqual({
      lastNativeDistanceM: null,
      accumulatedDistanceM: 0,
    })
  })

  it('uses the first native distance as baseline', () => {
    const result = applyNativeDistanceSample(
      createWorkoutDistanceState(),
      406,
      true,
    )

    expect(result).toEqual({
      lastNativeDistanceM: 406,
      accumulatedDistanceM: 0,
    })
  })

  it('accumulates native distance while workout is active', () => {
    let state = createWorkoutDistanceState()

    state = applyNativeDistanceSample(
      state,
      406,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      421,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      439,
      true,
    )

    expect(state).toEqual({
      lastNativeDistanceM: 439,
      accumulatedDistanceM: 33,
    })
  })

  it('does not accumulate distance while paused', () => {
    let state = createWorkoutDistanceState()

    state = applyNativeDistanceSample(
      state,
      1000,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      1010,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      1020,
      false,
    )

    expect(state).toEqual({
      lastNativeDistanceM: 1020,
      accumulatedDistanceM: 10,
    })
  })

  it('does not include paused distance after resume', () => {
    let state = createWorkoutDistanceState()

    state = applyNativeDistanceSample(
      state,
      1000,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      1010,
      true,
    )

    /*
     * Während Pause rollt das Bike noch 20 m weiter.
     */
    state = applyNativeDistanceSample(
      state,
      1030,
      false,
    )

    /*
     * Nach Resume kommen weitere 10 m dazu.
     */
    state = applyNativeDistanceSample(
      state,
      1040,
      true,
    )

    expect(state).toEqual({
      lastNativeDistanceM: 1040,
      accumulatedDistanceM: 20,
    })
  })

  it('handles a native bike distance reset', () => {
    let state = createWorkoutDistanceState()

    state = applyNativeDistanceSample(
      state,
      1000,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      1050,
      true,
    )

    /*
     * Bike wurde zurückgesetzt.
     */
    state = applyNativeDistanceSample(
      state,
      5,
      true,
    )

    /*
     * Danach läuft der neue Zähler normal weiter.
     */
    state = applyNativeDistanceSample(
      state,
      20,
      true,
    )

    expect(state).toEqual({
      lastNativeDistanceM: 20,
      accumulatedDistanceM: 65,
    })
  })

  it('ignores null distance samples', () => {
    const current = {
      lastNativeDistanceM: 100,
      accumulatedDistanceM: 25,
    }

    expect(
      applyNativeDistanceSample(
        current,
        null,
        true,
      ),
    ).toBe(current)
  })

  it('ignores invalid distance samples', () => {
    const current = {
      lastNativeDistanceM: 100,
      accumulatedDistanceM: 25,
    }

    expect(
      applyNativeDistanceSample(
        current,
        Number.NaN,
        true,
      ),
    ).toBe(current)

    expect(
      applyNativeDistanceSample(
        current,
        -1,
        true,
      ),
    ).toBe(current)
  })
})