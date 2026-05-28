import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import styles from './LoginScreen.module.css'

export function LoginScreen() {
  const { setToken, token } = useSession()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const urlToken = searchParams.get('token')
    if (urlToken) {
      setToken(urlToken)
      navigate('/consent', { replace: true })
      return
    }
    if (token) {
      navigate('/consent', { replace: true })
    }
  }, [searchParams, token, setToken, navigate])

  function handleGoogleLogin() {
    window.location.href = '/api/auth/google'
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.brand}>מתמלל</h1>
        <p className={styles.subtitle}>
          עזור לנו לתמלל כתב יד עברי היסטורי.
          <br />
          כל שורה שתתמלל משמרת חלק מהמורשת.
        </p>
        <button className={styles.loginBtn} onClick={handleGoogleLogin} type="button">
          התחבר עם Google
        </button>
      </div>
    </div>
  )
}
