import type React from 'react'

export type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type SpinnerColor = 'accent' | 'default' | 'white'

export interface SpinnerProps {
  size?: SpinnerSize
  color?: SpinnerColor
  label?: string
  className?: string
  style?: React.CSSProperties
}

const SIZE_MAP: Record<SpinnerSize, string> = {
  xs: 'h-4 w-4',
  sm: 'h-5 w-5',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-10 w-10',
}

const COLOR_MAP: Record<SpinnerColor, string> = {
  accent: 'text-accent-foreground',
  default: 'text-foreground',
  white: 'text-white',
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  color = 'accent',
  label = 'Chargement...',
  className = '',
  style,
}) => {
  const cls = [
    'animate-spin',
    SIZE_MAP[size],
    COLOR_MAP[color],
    className,
  ].filter(Boolean).join(' ')

  return (
    <svg
      role="status"
      aria-label={label}
      className={cls}
      style={style}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  )
}
