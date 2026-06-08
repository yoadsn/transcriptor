import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import { BrandMark, ManuscriptPreview, PrimaryBtn } from '../components/shared'

function GoogleMark({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
      <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62Z"/>
      <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.02-3.7H.92v2.33A9 9 0 0 0 9 18Z"/>
      <path fill="#FBBC05" d="M3.98 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.92a9 9 0 0 0 0 8.1l3.06-2.33Z"/>
      <path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58A9 9 0 0 0 .92 4.95l3.06 2.33C4.68 5.16 6.66 3.58 9 3.58Z"/>
    </svg>
  )
}

function AuthField({ label, type, placeholder, value, onChange }: {
  label: string
  type: string
  placeholder: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <label style={{ display: 'block' }}>
      <span style={{
        display: 'block',
        fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 500,
        color: 'var(--tl-ink)', marginBottom: 6,
      }}>{label}</span>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        dir="auto"
        className="pg-input"
      />
    </label>
  )
}

interface AuthFormProps {
  mode: 'signin' | 'signup'
  isMobile?: boolean
  onSwitchMode: () => void
  onGuest: () => void
}

function AuthForm({ mode, isMobile, onSwitchMode, onGuest }: AuthFormProps) {
  const signup = mode === 'signup'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleGoogle = () => {
    window.location.href = '/api/auth/google'
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Wired to backend in Phase 5 — for now navigate happens via token redirect
    window.location.href = '/api/auth/google'
  }

  return (
    <div style={{ width: '100%', maxWidth: 380 }}>
      <h1 style={{
        fontFamily: 'var(--font-serif)',
        fontSize: isMobile ? 28 : 34, fontWeight: 500,
        color: 'var(--tl-ink)', margin: '0 0 6px',
      }}>
        {signup ? 'הצטרפו לתעתוק' : 'ברוכים השבים'}
      </h1>
      <p style={{
        fontFamily: 'var(--font-ui)', fontSize: 15,
        color: 'var(--tl-muted)', margin: '0 0 24px', lineHeight: 1.5,
      }}>
        {signup
          ? 'הצטרפו ותרמו לשימור כתבי יד עבריים.'
          : 'להתחבר כדי להמשיך מהיכן שעצרת.'}
      </p>

      <button className="pg-oauth" onClick={handleGoogle} type="button">
        <GoogleMark /> המשך עם Google
      </button>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        margin: '18px 0',
        fontFamily: 'var(--font-ui)', fontSize: 12.5, color: 'var(--tl-muted)',
      }}>
        <div style={{ flex: 1, height: 1, background: 'var(--tl-border)' }} />
        <span>או</span>
        <div style={{ flex: 1, height: 1, background: 'var(--tl-border)' }} />
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {signup && (
          <AuthField label="שם" type="text" placeholder="השם שיופיע בפרופיל" value={name} onChange={setName} />
        )}
        <AuthField label="אימייל" type="email" placeholder="name@example.com" value={email} onChange={setEmail} />
        <AuthField label="סיסמה" type="password" placeholder="לפחות 8 תווים" value={password} onChange={setPassword} />

        <PrimaryBtn type="submit" size="lg" style={{ width: '100%', justifyContent: 'center', marginTop: 6 }}>
          {signup ? 'יצירת חשבון' : 'התחברות'}
        </PrimaryBtn>
      </form>

      {/* Guest login — debug only, will be removed */}
      <button className="pg-guest" onClick={onGuest} type="button">
        המשך כאורח — בלי חשבון
      </button>

      <div style={{
        textAlign: 'center', marginTop: 14,
        fontFamily: 'var(--font-ui)', fontSize: 13.5, color: 'var(--tl-muted)',
      }}>
        {signup ? 'כבר יש לכם חשבון? ' : 'עדיין אין חשבון? '}
        <span
          style={{ color: 'var(--tl-accent-text)', fontWeight: 600, cursor: 'pointer' }}
          onClick={onSwitchMode}
        >
          {signup ? 'התחברו' : 'הצטרפו'}
        </span>
      </div>
    </div>
  )
}

export function AuthScreen() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setToken, isAuthenticated, guestLogin } = useSession()
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')

  // Handle token redirect from Google OAuth
  useEffect(() => {
    const urlToken = searchParams.get('token')
    if (urlToken) {
      setToken(urlToken)
      navigate('/work', { replace: true })
      return
    }
    if (isAuthenticated) {
      navigate('/work', { replace: true })
    }
  }, [searchParams, isAuthenticated, setToken, navigate])

  const handleGuest = () => {
    guestLogin()
    navigate('/work', { replace: true })
  }

  const isMobile = window.innerWidth < 768

  // ── mobile ──
  if (isMobile) {
    return (
      <div dir="rtl" lang="he" style={{
        minHeight: '100vh', overflowY: 'auto',
        background: 'var(--tl-page)',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ height: 50 }} />
        <div style={{
          padding: '24px 26px 30px',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', flex: 1,
        }}>
          <div style={{ marginBottom: 28 }}><BrandMark size={30} /></div>
          <AuthForm
            mode={mode}
            isMobile
            onSwitchMode={() => setMode(m => m === 'signin' ? 'signup' : 'signin')}
            onGuest={handleGuest}
          />
        </div>
      </div>
    )
  }

  // ── desktop ──
  return (
    <div dir="rtl" lang="he" style={{
      height: '100vh',
      display: 'grid',
      gridTemplateColumns: '1fr 1.05fr',
      background: 'var(--tl-page)',
    }}>
      {/* Form pane (right in RTL — rendered first) */}
      <div style={{
        display: 'flex', flexDirection: 'column',
        padding: '40px 56px',
      }}>
        <BrandMark size={30} />
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <AuthForm
            mode={mode}
            onSwitchMode={() => setMode(m => m === 'signin' ? 'signup' : 'signin')}
            onGuest={handleGuest}
          />
        </div>
      </div>

      {/* Manuscript panel (left in RTL — rendered second) */}
      <div style={{
        position: 'relative',
        background: 'oklch(0.32 0.03 60)',
        overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: 48,
      }}>
        <div style={{
          position: 'absolute', inset: 0, opacity: 0.5,
          background: 'radial-gradient(120% 90% at 50% 0%, oklch(0.5 0.05 60) 0%, transparent 60%)',
        }} />
        <div style={{ position: 'relative', marginBottom: 30 }}>
          <ManuscriptPreview width={360} tilt />
        </div>
        <div style={{ position: 'relative', textAlign: 'center', maxWidth: 380 }}>
          <div style={{
            fontFamily: 'var(--font-serif)', fontSize: 24, fontWeight: 500,
            color: '#fff', lineHeight: 1.35,
          }}>
            כל שורה שתתעתקו נשמרת לחוקרים — ולדורות הבאים.
          </div>
          <div style={{
            fontFamily: 'var(--font-ui)', fontSize: 14,
            color: 'rgba(255,255,255,0.7)', marginTop: 12, direction: 'rtl',
          }}>
            הצטרפתם ל-<span style={{ direction: 'ltr', display: 'inline-block' }}>2,317</span> מתנדבים
          </div>
        </div>
      </div>
    </div>
  )
}
