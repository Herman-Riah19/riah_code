import type React from 'react'

export interface DividerProps {
  orientation?: 'horizontal' | 'vertical'
  variant?: 'subtle' | 'default' | 'accent'
  spacing?: 'none' | 'sm' | 'md' | 'lg'
  className?: string
  style?: React.CSSProperties
}

const VARIANT_MAP: Record<'subtle' | 'default' | 'accent', string> = {
  subtle: 'border-border/50',
  default: 'border-border',
  accent: 'border-accent',
}

const SPACING_MAP: Record<'none' | 'sm' | 'md' | 'lg', string> = {
  none: 'my-0',
  sm: 'my-2',
  md: 'my-4',
  lg: 'my-6',
}

export const Divider: React.FC<DividerProps> = ({
  orientation = 'horizontal',
  variant = 'default',
  spacing = 'md',
  className = '',
  style,
}) => (
  <hr
    role="separator"
    aria-orientation={orientation}
    className={[
      orientation === 'horizontal' ? 'h-[1px] w-full' : 'w-[1px] h-full',
      VARIANT_MAP[variant],
      SPACING_MAP[spacing],
      className,
    ]
      .filter(Boolean)
      .join(' ')}
    style={style}
  />
)
