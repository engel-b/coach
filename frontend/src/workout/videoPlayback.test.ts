import {
  describe,
  expect,
  it,
} from 'vitest'

import { shouldPauseVideoForBike } from './videoPlayback'


describe('shouldPauseVideoForBike', () => {
  it('does not pause while no bike speed is known', () => {
    expect(
      shouldPauseVideoForBike(null),
    ).toBe(false)
  })


  it('pauses when the bike stands still', () => {
    expect(
      shouldPauseVideoForBike(0),
    ).toBe(true)
  })


  it('does not pause while the bike is moving', () => {
    expect(
      shouldPauseVideoForBike(0.1),
    ).toBe(false)

    expect(
      shouldPauseVideoForBike(25),
    ).toBe(false)
  })


  it('treats negative speed as stopped', () => {
    /*
     * Eine negative Geschwindigkeit wäre zwar keine
     * sinnvolle FTMS-Messung, soll aber keinesfalls dazu
     * führen, dass das Video weiterläuft.
     */
    expect(
      shouldPauseVideoForBike(-1),
    ).toBe(true)
  })
})