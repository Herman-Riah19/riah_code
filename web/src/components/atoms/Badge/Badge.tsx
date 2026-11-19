import type React from 'react'

export type BadgeVariant = 'default' | 'accent' | 'success' | 'warning' | 'error' | 'muted'
export type BadgeSize = 'sm' | 'md' | 'lg'

export interface BadgeProps {
  variant?: BadgeVariant
  size?: BadgeSize
  dot?: boolean
  className?: string
  children?: React.ReactNode
  style?: React.CSSProperties
}

const VARIANT_MAP: Record<BadgeVariant, string> = {
  default: 'border border-input bg-muted px-2.5 py-0.5 text-xs font-semibold text-muted-foreground',
  accent: 'bg-accent text-accent-foreground px-2.5 py-0.5 text-xs font-semibold rounded-md',
  success: 'bg-green-100 text-green-800 px-2.5 py-0.5 text-xs font-semibold rounded-md',
  warning: 'bg-yellow-100 text-yellow-800 px-2.5 py-0.5 text-xs font-semibold rounded-md',
  error: 'bg-red-100 text-red-800 px-2.5 py-0.5 text-xs font-semibold rounded-md',
  muted: 'bg-muted px-2.5 py-0.5 text-xs font-semibold text-muted-foreground',
}

const SIZE_MAP: Record<BadgeSize, string> = {
  sm: 'h-6 min-w-6',
  md: 'h-8 min-w-8',
  lg: 'h-9 min-w-9',
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
  children,
  style,
}) => (
  <span
    className={[
      'inline-flex items-center rounded-full font-semibold',
      VARIANT_MAP[variant],
      SIZE_MAP[size],
      className,
    ].filter(Boolean).join(' ')}
    style={style}
  >
    {dot && <span className="mr-1 h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />}
    {children}
  </span>
)
