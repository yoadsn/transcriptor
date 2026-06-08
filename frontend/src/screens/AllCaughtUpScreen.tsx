import { TopNav } from '../components/shared'

const fmt = (n: number) => new Intl.NumberFormat('en-US').format(n)

// Placeholder — replace with real session data in Phase 5
const STATS = { today: 142, streak: 6, total: 3847 }

function CaughtUpStats({ isMobile }: { isMobile?: boolean }) {
  const items = [
    { v: String(STATS.today),    l: 'שורות היום' },
    { v: String(STATS.streak),   l: 'ימים ברצף' },
    { v: fmt(STATS.total),       l: 'סה״כ שורות' },
  ]
  return (
    <div style={{
      display: 'flex', gap: isMobile ? 0 : 10, width: '100%',
      maxWidth: isMobile ? 320 : 460,
      justifyContent: 'space-between',
    }}>
      {items.map((it, i) => (
        <div key={i} style={{ display: 'contents' }}>
          {i > 0 && (
            <div style={{
              width: 1, background: 'var(--tl-border)',
              alignSelf: 'stretch', margin: '4px 0',
            }} />
          )}
          <div style={{ flex: 1, textAlign: 'center', padding: '0 8px' }}>
            <div style={{
              fontFamily: 'var(--font-serif)',
              fontSize: isMobile ? 26 : 32, fontWeight: 700,
              color: 'var(--tl-ink)', direction: 'ltr',
            }}>{it.v}</div>
            <div style={{
              fontFamily: 'var(--font-ui)', fontSize: 12.5,
              color: 'var(--tl-muted)', marginTop: 3,
            }}>{it.l}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function AllCaughtUpScreen() {
  const isMobile = window.innerWidth < 768

  const body = (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      textAlign: 'center',
      maxWidth: isMobile ? 340 : 480,
      padding: isMobile ? '0 24px' : 0,
    }}>
      {/* green seal */}
      <div style={{ position: 'relative', width: 88, height: 88, marginBottom: 26 }}>
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          background: 'oklch(0.93 0.045 150)',
        }} />
        <div style={{
          position: 'absolute', inset: 14, borderRadius: '50%',
          background: 'oklch(0.88 0.07 150)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon name="check" size={34} color="oklch(0.46 0.1 150)" strokeWidth={2.4} />
        </div>
      </div>

      <h1 style={{
        fontFamily: 'var(--font-serif)',
        fontSize: isMobile ? 30 : 38, fontWeight: 500,
        color: 'var(--tl-ink)', margin: '0 0 12px', lineHeight: 1.15,
      }}>
        לא עליך המלאכה לגמור :)
      </h1>
      <p style={{
        fontFamily: 'var(--font-ui)',
        fontSize: isMobile ? 15.5 : 17, color: 'var(--tl-muted)',
        margin: '0 0 30px', lineHeight: 1.6,
      }}>
        אבל כל השורות תועתקו בינתיים. נוסיף שורות חדשות בקרוב.
      </p>

      <div style={{
        background: 'var(--tl-surface)', border: '0.5px solid var(--tl-border)',
        borderRadius: 16, padding: isMobile ? '18px 16px' : '20px 28px',
        marginBottom: 30, width: '100%',
        display: 'flex', justifyContent: 'center',
      }}>
        <CaughtUpStats isMobile={isMobile} />
      </div>

    </div>
  )

  return (
    <div dir="rtl" lang="he" style={{ minHeight: '100vh', background: 'var(--tl-page)', fontFamily: 'var(--font-ui)' }}>
      <TopNav active="work" compact={isMobile} safeTop={isMobile ? 50 : 0} />
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: isMobile ? '20px 0 40px' : '60px 0',
        minHeight: 'calc(100vh - 72px)',
      }}>
        {body}
      </div>
    </div>
  )
}
