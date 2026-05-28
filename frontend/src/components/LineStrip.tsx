import { cropStyle } from '../utils/cropStyle'
import type { SessionLine, PageDims } from '../types'
import styles from './LineStrip.module.css'

interface LineStripProps {
  line: SessionLine
  pageDims: PageDims
  imageUrl: string
  role: 'previous' | 'active' | 'next'
  displayHeight?: number
}

const ACTIVE_HEIGHT = 100
const CONTEXT_HEIGHT = 48

export function LineStrip({ line, pageDims, imageUrl, role, displayHeight }: LineStripProps) {
  const height = displayHeight ?? (role === 'active' ? ACTIVE_HEIGHT : CONTEXT_HEIGHT)
  const css = cropStyle(line.bbox, pageDims, height)

  const stripClass = [
    styles.strip,
    role === 'active' ? styles.stripActive : styles.stripContext,
  ].join(' ')

  return (
    <div className={stripClass}>
      <div
        className={styles.image}
        style={{
          ...css,
          backgroundImage: `url(${imageUrl})`,
        }}
        role="img"
        aria-label={`שורה ${line.line_index + 1}`}
      />
      {role === 'active' && (
        <div className={styles.label}>
          תמלול <span dir="ltr">{line.transcription_count}</span> מתוך{' '}
          <span dir="ltr">3</span>
        </div>
      )}
    </div>
  )
}
