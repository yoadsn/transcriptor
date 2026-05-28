import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, CONSENT_VERSION } from '../api'
import { useSession } from '../contexts/SessionContext'
import styles from './ConsentScreen.module.css'

export function ConsentScreen() {
  const navigate = useNavigate()
  const { setConsentGiven } = useSession()
  const [agreed, setAgreed] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [primerOpen, setPrimerOpen] = useState(false)

  async function handleAgree() {
    if (!agreed || submitting) return
    setSubmitting(true)
    try {
      await api.postConsent({ consent_type: 'contribution_license', version: CONSENT_VERSION })
      setConsentGiven(true)
      navigate('/work', { replace: true })
    } catch {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>ברוך הבא למתמלל</h1>

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>רישיון תרומה</h2>
          <p className={styles.sectionText}>
            התמלולים שתספק יישמרו במאגר נתונים ציבורי פתוח לתועלת המחקר ולשימור
            המורשת הכתובה. הנתונים ישמשו למחקר אקדמי ופיתוח כלי עיבוד שפה עברית.
          </p>
          <label className={styles.checkboxRow}>
            <input
              type="checkbox"
              className={styles.checkbox}
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
            />
            <span className={styles.checkboxLabel}>
              אני מסכים/ה ותורם/ת את התמלולים שלי לשימוש ציבורי פתוח
            </span>
          </label>
        </div>

        <div className={styles.section}>
          <p className={styles.telemetryNotice}>
            אנו רושמים נתוני שימוש כדי לשפר את איכות הנתונים ואת חוויית התמלול.
            לא נשמר מידע אישי מעבר לשם המשתמש שתבחר.
          </p>
        </div>

        <div className={styles.section}>
          <button
            type="button"
            className={styles.primerLink}
            onClick={() => setPrimerOpen(true)}
          >
            איך מתמללים? — מדריך קצר
          </button>
        </div>

        <button
          type="button"
          className={styles.agreeBtn}
          disabled={!agreed || submitting}
          onClick={handleAgree}
        >
          {submitting ? 'שומר…' : 'אני מסכים/ה — בואו נתחיל'}
        </button>
      </div>

      {primerOpen && (
        <div className={styles.modalOverlay} onClick={() => setPrimerOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>מדריך תמלול</h2>
            <div className={styles.modalContent}>
              <p>
                <strong>מה מתמללים?</strong> כתוב את הטקסט שאתה רואה בשורה כמו שהוא.
                אל תשנה שגיאות כתיב — העתק מה שכתוב.
              </p>
              <p>
                <strong>תיבות ואותיות חלקיות:</strong> אם אות חתוכה, כתוב את מה שנראה.
                אם אין דרך לדעת מה האות — השתמש בדגל &quot;לא מצליח לקרוא&quot;.
              </p>
              <p>
                <strong>ניקוד:</strong> אין צורך להוסיף ניקוד שאינו בכתב המקורי.
                אם יש ניקוד בכתב — כתוב אותו.
              </p>
              <p>
                <strong>מספרים:</strong> כתוב מספרים כפי שהם מופיעים — ספרות עבריות
                (א, ב, ג…) או ערביות (1, 2, 3…).
              </p>
              <p>
                <strong>שפות אחרות:</strong> אם השורה אינה בעברית — השתמש בדגל
                &quot;לא עברית&quot;.
              </p>
            </div>
            <button
              type="button"
              className={styles.modalCloseBtn}
              onClick={() => setPrimerOpen(false)}
            >
              סגור
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
