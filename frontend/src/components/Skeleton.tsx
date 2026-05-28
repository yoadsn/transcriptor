import styles from './Skeleton.module.css'

export function WorkSkeleton() {
  return (
    <div aria-busy="true" aria-label="טוען…">
      <div className={[styles.skeleton, styles.stripSkeleton].join(' ')} />
      <div className={[styles.skeleton, styles.activeSkeleton].join(' ')} />
      <div className={[styles.skeleton, styles.inputSkeleton].join(' ')} />
      <div className={[styles.skeleton, styles.barSkeleton].join(' ')} />
    </div>
  )
}
