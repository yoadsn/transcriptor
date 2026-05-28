import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import styles from './MeScreen.module.css'

interface LeaderboardEntry {
  display_name: string
  text_count: number
  isMe?: boolean
}

export function MeScreen() {
  const [progress, setProgress] = useState<number | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [loadingProgress, setLoadingProgress] = useState(true)
  const [loadingBoard, setLoadingBoard] = useState(true)

  useEffect(() => {
    api.getProgress().then((data) => {
      setProgress(data?.text_count ?? 0)
      setLoadingProgress(false)
    }).catch(() => {
      setLoadingProgress(false)
    })

    api.getLeaderboard().then((data) => {
      setLeaderboard(data ?? [])
      setLoadingBoard(false)
    }).catch(() => {
      setLoadingBoard(false)
    })
  }, [])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>הישגים ולוח מובילים</h1>
        <Link to="/work" className={styles.backLink}>חזור לתמלול</Link>
      </div>

      <div className={styles.content}>
        <div className={styles.metricCard}>
          {loadingProgress ? (
            <span className={styles.loading}>טוען…</span>
          ) : (
            <>
              <span className={styles.metricNumber}>{progress ?? 0}</span>
              <span className={styles.metricLabel}>שורות תומללו</span>
            </>
          )}
        </div>

        <div className={styles.leaderboardSection}>
          <h2 className={styles.leaderboardTitle}>לוח מובילים</h2>
          {loadingBoard ? (
            <p className={styles.loading}>טוען…</p>
          ) : leaderboard.length === 0 ? (
            <p className={styles.loading}>אין נתונים להצגה</p>
          ) : (
            <ul className={styles.leaderboardList}>
              {leaderboard.map((entry, idx) => (
                <li
                  key={`${entry.display_name}-${idx}`}
                  className={[
                    styles.leaderboardItem,
                    entry.isMe ? styles.leaderboardItemMe : '',
                  ].join(' ')}
                >
                  <span className={styles.rank} dir="ltr">
                    {idx + 1}
                  </span>
                  <span className={styles.displayName}>{entry.display_name}</span>
                  <span className={styles.lineCount} dir="ltr">
                    {entry.text_count}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <p className={styles.privacyNotice}>
          השם שלך מופיע בלוח המובילים לכל המשתמשים הרשומים.
        </p>
      </div>
    </div>
  )
}
