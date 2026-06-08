import { cropBgStyle } from '../../utils/cropStyle'
import type { BBox, PageDims } from '../../types'

interface LineCropProps {
  bbox: BBox
  pageDims: PageDims
  imageUrl: string
  width?: number
  spotlight?: boolean
  dim?: boolean
}

export function LineCrop({ bbox, pageDims, imageUrl, width = 320, spotlight = false, dim = false }: LineCropProps) {
  const { style, height } = cropBgStyle(bbox, pageDims, width)

  return (
    <div
      style={{
        ...style,
        height,
        backgroundImage: `url(${imageUrl})`,
        borderRadius: 6,
        overflow: 'hidden',
        filter: dim ? 'brightness(0.7) saturate(0.85)' : 'none',
        boxShadow: spotlight
          ? '0 0 0 2.5px var(--tl-spotlight), 0 0 18px 2px var(--tl-spotlight-glow)'
          : 'inset 0 0 0 0.5px var(--tl-border)',
      }}
    />
  )
}
