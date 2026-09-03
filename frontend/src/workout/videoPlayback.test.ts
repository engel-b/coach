import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  calculateVideoPlaybackRate,
  shouldPauseVideoForBike,
} from './videoPlayback'


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
    expect(
      shouldPauseVideoForBike(-1),
    ).toBe(true)
  })
})


describe('calculateVideoPlaybackRate', () => {
  it('uses normal playback while no bike speed is known', () => {
    expect(
      calculateVideoPlaybackRate(null),
    ).toBe(1)
  })


  it('uses normal playback at the reference speed', () => {
    expect(
      calculateVideoPlaybackRate(20),
    ).toBe(1)
  })


  it('slows the video down below the reference speed', () => {
    expect(
      calculateVideoPlaybackRate(15),
    ).toBe(0.75)
  })


  it('speeds the video up above the reference speed', () => {
    expect(
      calculateVideoPlaybackRate(30),
    ).toBe(1.5)
  })


  it('does not go below the minimum playback rate', () => {
    expect(
      calculateVideoPlaybackRate(5),
    ).toBe(0.5)

    expect(
      calculateVideoPlaybackRate(0),
    ).toBe(0.5)
  })


  it('does not exceed the maximum playback rate', () => {
    expect(
      calculateVideoPlaybackRate(40),
    ).toBe(2)

    expect(
      calculateVideoPlaybackRate(60),
    ).toBe(2)
  })
})