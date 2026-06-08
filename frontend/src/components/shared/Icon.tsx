interface IconProps {
  name: 'forward' | 'back' | 'check' | 'flag' | 'close' | 'spark'
  size?: number
  color?: string
  strokeWidth?: number
}

export function Icon({ name, size = 18, color = 'currentColor', strokeWidth = 1.6 }: IconProps) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 18 18',
    fill: 'none' as const,
    stroke: color,
    strokeWidth,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  }

  switch (name) {
    case 'forward': // RTL forward — points LEFT
      return <svg {...common}><path d="M11 4 L5 9 L11 14" /></svg>
    case 'back':
      return <svg {...common}><path d="M7 4 L13 9 L7 14" /></svg>
    case 'check':
      return <svg {...common}><path d="M3.5 9.5 L7 13 L14.5 5" /></svg>
    case 'flag':
      return (
        <svg width={size} height={size} viewBox="0 0 18 18" fill="none">
          <path d="M4 2 V16" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" />
          <path d="M4 3 H14 L11.4 6 L14 9 H4 Z" stroke={color} strokeWidth={strokeWidth}
            strokeLinejoin="round" fill="none" />
        </svg>
      )
    case 'close':
      return <svg {...common}><path d="M4 4 L14 14 M14 4 L4 14" /></svg>
    case 'spark':
      return (
        <svg width={size} height={size} viewBox="0 0 18 18" fill={color}>
          <path d="M9 1 L10.6 6.6 L16 8.2 L10.6 9.8 L9 17 L7.4 9.8 L2 8.2 L7.4 6.6 Z" />
        </svg>
      )
    default:
      return null
  }
}
