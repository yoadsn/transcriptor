import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'
import styles from './DoneScreen.module.css'

export function DoneScreen() {
  const navigate = useNavigate()
  const [dayCount, setDayCount] = useState(0)
  const [ready, setReady] = useState(false)
  const [loading, setLoading] = useState(false)
  const [nothingLeft, setNothingLeft] = useState(false)

  useEffect(() => {
    api.getProgress().then((data) => {
      if (data) setDayCount(data.text_count)
    }).catch(() => {})

    const timer = setTimeout(() => setReady(true), 2000)
    return () => clearTimeout(timer)
  }, [])

  async function handleContinue() {
    setLoading(true)
    try {
      const session = await api.nextSession()
      if (!session) {
        setNothingLeft(true)
        setLoading(false)
        return
      }
      navigate('/work')
    } catch {
      setLoading(false)
    }
  }

  if (nothingLeft) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>
          <div className={styles.emptyState}>
            <p className={styles.emptyTitle}>אין כרגע שורות לתמלול — תודה!</p>
            <p className={styles.emptySubtitle}>
              המאגר יתחדש בקרוב. תוכל/י לראות את ההישגים שלך.
            </p>
            <Link to="/me" className={styles.meLink}>
              ראה הישגים ולוח מובילים
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.celebration} aria-hidden="true">✓</div>
        <h1 className={styles.title}>סיימת את העמוד!</h1>

        <div className={styles.countWrapper}>
          <span className={styles.countNumber} dir="ltr">{dayCount}</span>
          <span className={styles.countLabel}>שורות תומללו עד כה</span>
        </div>

        <button
          type="button"
          className={styles.continueBtn}
          onClick={handleContinue}
          disabled={!ready || loading}
        >
          {loading ? 'טוען…' : ready ? 'המשך לעמוד הבא' : 'מעבד…'}
        </button>
      </div>
    </div>
  )
}
