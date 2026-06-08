interface BrandMarkProps {
  size?: number
  withName?: boolean
}

export function BrandMark({ size = 30, withName = true }: BrandMarkProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{
        width: size,
        height: size,
        borderRadius: size * 0.27,
        background: 'oklch(0.6 0.09 60)',
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'var(--font-serif)',
        fontSize: size * 0.6,
        fontWeight: 700,
        flex: '0 0 auto',
      }}>ת</div>
      {withName && (
        <span style={{
          fontFamily: 'var(--font-serif)',
          fontSize: size * 0.66,
          fontWeight: 500,
          color: 'var(--tl-ink)',
          letterSpacing: '0.01em',
        }}>תַּעְתִּיק</span>
      )}
    </div>
  )
}
