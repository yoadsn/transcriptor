import { describe, it, expect } from 'vitest'
import { cropStyle } from './cropStyle'
import type { BBox, PageDims } from '../types'

describe('cropStyle', () => {
  const pageDims: PageDims = { width_px: 1000, height_px: 2000 }

  it('computes scale factor as displayHeight / bbox.h', () => {
    const bbox: BBox = { x: 100, y: 200, w: 400, h: 50 }
    const displayHeight = 100
    const style = cropStyle(bbox, pageDims, displayHeight)

    // scale = displayHeight / bbox.h = 100 / 50 = 2
    // bgWidth = 1000 * 2 = 2000
    // bgHeight = 2000 * 2 = 4000
    expect(style.backgroundSize).toBe('2000px 4000px')
  })

  it('computes correct backgroundPosition for bbox in the middle of a page', () => {
    const bbox: BBox = { x: 100, y: 200, w: 400, h: 50 }
    const displayHeight = 100
    const padding = 16
    const style = cropStyle(bbox, pageDims, displayHeight, padding)

    // scale = 100 / 50 = 2
    // bgPosX = -(100 * 2 - 16) = -(200 - 16) = -184
    // bgPosY = -(200 * 2) = -400
    expect(style.backgroundPosition).toBe('-184px -400px')
  })

  it('handles bbox at page origin (x=0, y=0)', () => {
    const bbox: BBox = { x: 0, y: 0, w: 200, h: 40 }
    const displayHeight = 80
    const padding = 16
    const style = cropStyle(bbox, pageDims, displayHeight, padding)

    // scale = 80 / 40 = 2
    // bgPosX = -(0 * 2 - 16) = 16
    // bgPosY = -(0 * 2) = 0
    expect(style.backgroundPosition).toBe('16px 0px')
  })

  it('computes container width correctly with padding', () => {
    const bbox: BBox = { x: 50, y: 100, w: 300, h: 60 }
    const displayHeight = 120
    const padding = 16
    const style = cropStyle(bbox, pageDims, displayHeight, padding)

    // scale = 120 / 60 = 2
    // containerWidth = Math.ceil(300 * 2) + 16 * 2 = 600 + 32 = 632
    expect(style.width).toBe(632)
    expect(style.height).toBe(displayHeight)
  })

  it('uses default padding of 16 when not provided', () => {
    const bbox: BBox = { x: 100, y: 100, w: 200, h: 50 }
    const displayHeight = 100
    const styleWithDefault = cropStyle(bbox, pageDims, displayHeight)
    const styleWithExplicit = cropStyle(bbox, pageDims, displayHeight, 16)

    expect(styleWithDefault.width).toBe(styleWithExplicit.width)
    expect(styleWithDefault.backgroundPosition).toBe(styleWithExplicit.backgroundPosition)
  })

  it('sets backgroundRepeat to no-repeat', () => {
    const bbox: BBox = { x: 0, y: 0, w: 100, h: 100 }
    const style = cropStyle(bbox, pageDims, 100)
    expect(style.backgroundRepeat).toBe('no-repeat')
  })

  it('padding affects x-offset correctly', () => {
    const bbox: BBox = { x: 200, y: 100, w: 400, h: 100 }
    const displayHeight = 100
    const padding0 = cropStyle(bbox, pageDims, displayHeight, 0)
    const padding32 = cropStyle(bbox, pageDims, displayHeight, 32)

    // scale = 100 / 100 = 1
    // padding=0: bgPosX = -(200*1 - 0) = -200
    // padding=32: bgPosX = -(200*1 - 32) = -168
    expect(padding0.backgroundPosition).toBe('-200px -100px')
    expect(padding32.backgroundPosition).toBe('-168px -100px')
  })
})
