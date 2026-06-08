import type { BBox } from '../../types'

// Sample page dimensions (matches the zip's OIP sample image)
export const SAMPLE_PAGE = {
  width_px: 474,
  height_px: 218,
  image_url: '/sample-page.jpg',
}

// A representative line on the sample page to spotlight
const SPOTLIGHT_BBOX: BBox = { x: 6, y: 72, w: 462, h: 40 }

interface ManuscriptPreviewProps {
  width?: number
  lineIndex?: number
  tilt?: boolean
  customBbox?: BBox
}

export function ManuscriptPreview({ width = 460, tilt = true, customBbox }: ManuscriptPreviewProps) {
  const scale = width / SAMPLE_PAGE.width_px
  const b = customBbox ?? SPOTLIGHT_BBOX

  return (
    <div style={{
      position: 'relative',
      width,
      transform: tilt ? 'rotate(-1.4deg)' : 'none',
      flexShrink: 0,
    }}>
      {/* Dimmed full folio */}
      <img
        src={SAMPLE_PAGE.image_url}
        alt=""
        draggable={false}
        style={{
          width,
          display: 'block',
          borderRadius: 8,
          boxShadow: '0 18px 50px rgba(40,30,20,0.26)',
          filter: 'brightness(0.66) saturate(0.82)',
        }}
      />

      {/* Spotlit line cutout */}
      <div style={{
        position: 'absolute',
        left: b.x * scale,
        top: b.y * scale,
        width: b.w * scale,
        height: b.h * scale,
        overflow: 'hidden',
        borderRadius: 4,
        boxShadow: '0 0 0 2.5px var(--tl-spotlight), 0 0 24px 3px var(--tl-spotlight-glow)',
      }}>
        <img
          src={SAMPLE_PAGE.image_url}
          alt=""
          draggable={false}
          style={{
            position: 'absolute',
            left: -b.x * scale,
            top: -b.y * scale,
            width,
            maxWidth: 'none',
            display: 'block',
          }}
        />
      </div>

      {/* RTL leading-edge caret */}
      <div style={{
        position: 'absolute',
        left: (b.x + b.w) * scale,
        top: (b.y + b.h / 2) * scale,
        transform: 'translate(3px, -50%)',
        width: 0,
        height: 0,
        borderTop: '6px solid transparent',
        borderBottom: '6px solid transparent',
        borderRight: '7px solid var(--tl-spotlight)',
      }} />
    </div>
  )
}
