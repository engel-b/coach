import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  applyWorkoutRuntimeEvent,
  createWorkoutRuntime,
  getFinishWindowRemainingSeconds,
} from './workoutRuntime'


describe('workout runtime', () => {
  it('starts in running state', () => {
    expect(
      createWorkoutRuntime(),
    ).toEqual({
      state: 'running',
      finishWindowElapsedSeconds: 0,
    })
  })


  it('enters the finish window when the planned duration is reached', () => {
    const runtime =
      createWorkoutRuntime()

    const result =
      applyWorkoutRuntimeEvent(
        runtime,
        {
          type:
            'planned_duration_reached',
        },
      )

    expect(result).toEqual({
      state: 'finish_window',
      finishWindowElapsedSeconds: 0,
    })

    expect(
      getFinishWindowRemainingSeconds(
        result,
      ),
    ).toBe(30)
  })


  it('counts the finish window while the user keeps riding', () => {
    let runtime =
      applyWorkoutRuntimeEvent(
        createWorkoutRuntime(),
        {
          type:
            'planned_duration_reached',
        },
      )

    runtime =
      applyWorkoutRuntimeEvent(
        runtime,
        {
          type: 'tick',
        },
      )

    expect(runtime).toEqual({
      state: 'finish_window',
      finishWindowElapsedSeconds: 1,
    })

    expect(
      getFinishWindowRemainingSeconds(
        runtime,
      ),
    ).toBe(29)
  })


  it('completes when the bike stops during the finish window', () => {
    let runtime =
      applyWorkoutRuntimeEvent(
        createWorkoutRuntime(),
        {
          type:
            'planned_duration_reached',
        },
      )

    for (let second = 0; second < 10; second += 1) {
      runtime =
        applyWorkoutRuntimeEvent(
          runtime,
          {
            type: 'tick',
          },
        )
    }

    runtime =
      applyWorkoutRuntimeEvent(
        runtime,
        {
          type: 'bike_stopped',
        },
      )

    expect(runtime.state).toBe(
      'completed',
    )
  })


  it('enters overtime after 30 seconds of continued riding', () => {
    let runtime =
      applyWorkoutRuntimeEvent(
        createWorkoutRuntime(),
        {
          type:
            'planned_duration_reached',
        },
      )

    for (let second = 0; second < 30; second += 1) {
      runtime =
        applyWorkoutRuntimeEvent(
          runtime,
          {
            type: 'tick',
          },
        )
    }

    expect(runtime).toEqual({
      state: 'overtime',
      finishWindowElapsedSeconds: 30,
    })
  })


  it('does not complete when the bike stops after the finish window', () => {
    let runtime =
      applyWorkoutRuntimeEvent(
        createWorkoutRuntime(),
        {
          type:
            'planned_duration_reached',
        },
      )

    for (let second = 0; second < 30; second += 1) {
      runtime =
        applyWorkoutRuntimeEvent(
          runtime,
          {
            type: 'tick',
          },
        )
    }

    runtime =
      applyWorkoutRuntimeEvent(
        runtime,
        {
          type: 'bike_stopped',
        },
      )

    expect(runtime.state).toBe(
      'overtime',
    )
  })


  it('ignores additional events after completion', () => {
    let runtime =
      applyWorkoutRuntimeEvent(
        createWorkoutRuntime(),
        {
          type:
            'planned_duration_reached',
        },
      )

    runtime =
      applyWorkoutRuntimeEvent(
        runtime,
        {
          type: 'bike_stopped',
        },
      )

    const result =
      applyWorkoutRuntimeEvent(
        runtime,
        {
          type: 'tick',
        },
      )

    expect(result).toBe(runtime)
  })
})