import type React from 'react'

export type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6
export type HeadingSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl'
export type HeadingWeight = 'normal' | 'medium' | 'semibold' | 'bold'
export type HeadingColor = 'default' | 'muted' | 'accent'

export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: HeadingLevel
  size?: HeadingSize
  weight?: HeadingWeight
  color?: HeadingColor
  className?: string
  children?: React.ReactNode
  style?: React.CSSProperties
}

const DEFAULT_SIZE: Record<HeadingLevel, HeadingSize> = {
  1: '3xl',
  2: '2xl',
  3: 'xl',
  4: 'lg',
  5: 'md',
  6: 'sm',
}

const SIZE_MAP: Record<HeadingSize, string> = {
  xs: 'text-xs',
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl',
  '2xl': 'text-2xl',
  '3xl': 'text-3xl',
}

const WEIGHT_MAP: Record<HeadingWeight, string> = {
  normal: 'font-normal',
  medium: 'font-medium',
  semibold: 'font-semibold',
  bold: 'font-bold',
}

const COLOR_MAP: Record<HeadingColor, string> = {
  default: 'text-foreground',
  muted: 'text-muted-foreground',
  accent: 'text-accent-foreground',
}

export const Heading: React.FC<HeadingProps> = ({
  level = 2,
  size,
  weight = 'semibold',
  color = 'default',
  className = '',
  children,
  style,
  ...rest
}) => {
  const Tag = `h${level}` as const
  const resolvedSize = size ?? DEFAULT_SIZE[level]
  const cls = [
    SIZE_MAP[resolvedSize],
    WEIGHT_MAP[weight],
    COLOR_MAP[color],
    className,
  ].filter(Boolean).join(' ')

  return <Tag className={cls} style={style} {...rest}>{children}</Tag>
}
