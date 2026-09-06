import { describe, expect, it } from 'vitest'

import {
  applyNativeDistanceSample,
  createWorkoutDistanceState,
} from './workoutDistance'

describe('workoutDistance', () => {
  it('starts without a native baseline by default', () => {
    expect(
      createWorkoutDistanceState(),
    ).toEqual({
      lastNativeDistanceM: null,
      accumulatedDistanceM: 0,
    })
  })

  it('can start with an already known native distance', () => {
    expect(
      createWorkoutDistanceState(1234),
    ).toEqual({
      lastNativeDistanceM: 1234,
      accumulatedDistanceM: 0,
    })
  })

  it('ignores invalid initial native distance', () => {
    expect(
      createWorkoutDistanceState(-1),
    ).toEqual({
      lastNativeDistanceM: null,
      accumulatedDistanceM: 0,
    })

    expect(
      createWorkoutDistanceState(Number.NaN),
    ).toEqual({
      lastNativeDistanceM: null,
      accumulatedDistanceM: 0,
    })
  })

  it('uses the first native sample only as baseline', () => {
    const initial =
      createWorkoutDistanceState()

    const next = applyNativeDistanceSample(
      initial,
      406,
      true,
    )

    expect(next).toEqual({
      lastNativeDistanceM: 406,
      accumulatedDistanceM: 0,
    })
  })

  it('accumulates positive native distance deltas', () => {
    let state =
      createWorkoutDistanceState(406)

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

  it('updates baseline but does not count while paused', () => {
    let state =
      createWorkoutDistanceState(100)

    state = applyNativeDistanceSample(
      state,
      120,
      false,
    )

    expect(state).toEqual({
      lastNativeDistanceM: 120,
      accumulatedDistanceM: 0,
    })
  })

  it('does not include paused distance after resume', () => {
    let state =
      createWorkoutDistanceState(100)

    state = applyNativeDistanceSample(
      state,
      120,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      140,
      false,
    )

    state = applyNativeDistanceSample(
      state,
      150,
      true,
    )

    expect(state).toEqual({
      lastNativeDistanceM: 150,
      accumulatedDistanceM: 30,
    })
  })

  it('handles a native distance counter reset', () => {
    let state =
      createWorkoutDistanceState(1000)

    state = applyNativeDistanceSample(
      state,
      1050,
      true,
    )

    state = applyNativeDistanceSample(
      state,
      5,
      true,
    )

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

  it('ignores null samples', () => {
    const state =
      createWorkoutDistanceState(500)

    expect(
      applyNativeDistanceSample(
        state,
        null,
        true,
      ),
    ).toEqual(state)
  })

  it('ignores NaN and negative samples', () => {
    const state =
      createWorkoutDistanceState(500)

    expect(
      applyNativeDistanceSample(
        state,
        Number.NaN,
        true,
      ),
    ).toEqual(state)

    expect(
      applyNativeDistanceSample(
        state,
        -1,
        true,
      ),
    ).toEqual(state)
  })
})