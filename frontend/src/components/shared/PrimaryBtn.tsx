import type { ReactNode, CSSProperties, MouseEvent } from 'react'

interface PrimaryBtnProps {
  children: ReactNode
  size?: 'sm' | 'md' | 'lg'
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void
  style?: CSSProperties
  disabled?: boolean
  type?: 'button' | 'submit'
}

export function PrimaryBtn({ children, size = 'md', onClick, style, disabled, type = 'button' }: PrimaryBtnProps) {
  const pad = size === 'lg' ? '14px 28px' : size === 'sm' ? '8px 16px' : '11px 22px'
  const fs = size === 'lg' ? 17 : size === 'sm' ? 14 : 15.5
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className="pg-primary"
      style={{ fontSize: fs, padding: pad, ...style }}
    >
      {children}
    </button>
  )
}

interface GhostBtnProps {
  children: ReactNode
  size?: 'sm' | 'md' | 'lg'
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void
  style?: CSSProperties
  type?: 'button' | 'submit'
}

export function GhostBtn({ children, size = 'md', onClick, style, type = 'button' }: GhostBtnProps) {
  const pad = size === 'lg' ? '14px 24px' : size === 'sm' ? '8px 14px' : '11px 20px'
  const fs = size === 'lg' ? 17 : size === 'sm' ? 14 : 15.5
  return (
    <button
      type={type}
      onClick={onClick}
      className="pg-ghost"
      style={{ fontSize: fs, padding: pad, ...style }}
    >
      {children}
    </button>
  )
}
