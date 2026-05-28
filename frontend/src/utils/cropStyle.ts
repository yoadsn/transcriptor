import type { CSSProperties } from 'react'
import type { BBox, PageDims } from '../types'

/**
 * Returns CSS properties for a div that shows only the bbox region of the full page image.
 * Uses background-image approach: background-size, background-position.
 *
 * @param bbox - Bounding box in original pixel coordinates
 * @param pageDims - Full page dimensions in pixels
 * @param displayHeight - Desired display height of the strip in CSS px
 * @param padding - Optional horizontal padding in CSS px (default 16)
 */
export function cropStyle(
  bbox: BBox,
  pageDims: PageDims,
  displayHeight: number,
  padding = 16
): CSSProperties {
  const scale = displayHeight / bbox.h
  const containerWidth = Math.ceil(bbox.w * scale) + padding * 2
  const bgWidth = pageDims.width_px * scale
  const bgHeight = pageDims.height_px * scale
  const bgPosX = -(bbox.x * scale - padding)
  const bgPosY = -(bbox.y * scale)

  return {
    width: containerWidth,
    height: displayHeight,
    backgroundSize: `${bgWidth}px ${bgHeight}px`,
    backgroundPosition: `${bgPosX}px ${bgPosY}px`,
    backgroundRepeat: 'no-repeat',
  }
}
