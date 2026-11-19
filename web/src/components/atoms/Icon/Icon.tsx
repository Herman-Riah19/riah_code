import type React from 'react'

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type IconColor = 'default' | 'muted' | 'accent' | 'error' | 'success' | 'warning' | 'inherit'

export interface IconProps {
  name: string
  size?: IconSize
  color?: IconColor
  className?: string
  style?: React.CSSProperties
  'aria-label'?: string
  'aria-hidden'?: boolean | 'true' | 'false'
}

const SIZE_MAP: Record<IconSize, string> = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
  xl: 'h-8 w-8',
}

const COLOR_MAP: Record<IconColor, string> = {
  default: 'text-foreground',
  muted: 'text-muted-foreground',
  accent: 'text-accent-foreground',
  error: 'text-destructive',
  success: 'text-green-600',
  warning: 'text-yellow-600',
  inherit: '',
}

export const Icon: React.FC<IconProps> = ({
  name,
  size = 'md',
  color = 'inherit',
  className = '',
  style,
  'aria-label': ariaLabel,
  'aria-hidden': ariaHidden,
}) => {
  const cls = [
    SIZE_MAP[size],
    COLOR_MAP[color],
    className,
  ].filter(Boolean).join(' ')

  return (
    <svg
      className={cls}
      style={style}
      role={ariaLabel ? 'img' : 'presentation'}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : (ariaHidden ?? true)}
    >
      <use href={`/icons.svg#${name}`} />
    </svg>
  )
}
