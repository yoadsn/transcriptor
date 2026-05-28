import styles from './WorkHeader.module.css'

interface WorkHeaderProps {
  pageNum: number
  lineNum: number
  total: number
  todayCount: number
  progress: number
}

export function WorkHeader({ pageNum, lineNum, total, todayCount, progress }: WorkHeaderProps) {
  const clampedProgress = Math.min(100, Math.max(0, progress))

  return (
    <header className={styles.header}>
      <span className={styles.brand}>מתמלל</span>
      <div className={styles.meta}>
        <span className={styles.pageInfo}>
          עמוד <span dir="ltr">{pageNum}</span> · שורה{' '}
          <span dir="ltr">{lineNum}</span> מתוך{' '}
          <span dir="ltr">{total}</span>
        </span>
        <span className={styles.todayCount}>
          <span dir="ltr">{todayCount}</span> היום
        </span>
        <div className={styles.progressWrapper}>
          <div
            className={styles.progressBar}
            style={{ width: `${clampedProgress}%` }}
            role="progressbar"
            aria-valuenow={clampedProgress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>
    </header>
  )
}
