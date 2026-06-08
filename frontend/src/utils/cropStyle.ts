import type { CSSProperties } from 'react'
import type { BBox, PageDims } from '../types'

/**
 * Width-based crop: scales a bbox to a fixed display width.
 * Returns { style, height } where style is the background CSS for the container div.
 */
export function cropBgStyle(
  bbox: BBox,
  pageDims: PageDims,
  displayWidth: number,
  pad = 0
): { style: CSSProperties; height: number } {
  const inner = displayWidth - pad * 2
  const scale = inner / bbox.w
  const bgW = pageDims.width_px * scale
  const bgH = pageDims.height_px * scale
  const posX = -(bbox.x * scale) + pad
  const posY = -(bbox.y * scale)
  const height = Math.round(bbox.h * scale)
  return {
    height,
    style: {
      width: displayWidth,
      height,
      backgroundSize: `${bgW}px ${bgH}px`,
      backgroundPosition: `${posX}px ${posY}px`,
      backgroundRepeat: 'no-repeat',
    },
  }
}

/**
 * Returns CSS properties for a div that shows only the bbox region of the full page image.
 * Uses background-image approach: background-size, background-position.
 *
 * @param bbox - Bounding box in original pixel coordinates
 * @param pageDims - Full page dimensions in pixels
 * @param displayHeight - Desired display height of the strip in CSS px
 * @param padding - Optional horizontal padding in CSS px (default 16)
 * @param maxWidth - Optional max container width in CSS px; scale is reduced if needed
 */
export function cropStyle(
  bbox: BBox,
  pageDims: PageDims,
  displayHeight: number,
  padding = 16,
  maxWidth?: number
): CSSProperties {
  let scale = displayHeight / bbox.h
  let containerWidth = Math.ceil(bbox.w * scale) + padding * 2

  if (maxWidth && containerWidth > maxWidth) {
    scale = (maxWidth - padding * 2) / bbox.w
    containerWidth = maxWidth
  }

  const actualHeight = Math.ceil(bbox.h * scale)
  const bgWidth = pageDims.width_px * scale
  const bgHeight = pageDims.height_px * scale
  const bgPosX = -(bbox.x * scale - padding)
  const bgPosY = -(bbox.y * scale)

  return {
    width: containerWidth,
    height: actualHeight,
    backgroundSize: `${bgWidth}px ${bgHeight}px`,
    backgroundPosition: `${bgPosX}px ${bgPosY}px`,
    backgroundRepeat: 'no-repeat',
  }
}
