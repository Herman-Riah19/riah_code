import type React from 'react'

export type TextSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type TextWeight = 'normal' | 'medium' | 'semibold' | 'bold'
export type TextColor = 'default' | 'muted' | 'emphasis' | 'accent' | 'error' | 'success' | 'warning'
export type TextAlign = 'left' | 'center' | 'right'
export type TextAs = 'p' | 'span' | 'label' | 'small' | 'strong' | 'em' | 'li' | 'div' | 'a'

export interface TextProps extends React.HTMLAttributes<HTMLElement> {
  as?: TextAs
  size?: TextSize
  weight?: TextWeight
  color?: TextColor
  align?: TextAlign
  truncate?: boolean
  mono?: boolean
  className?: string
  children?: React.ReactNode
  style?: React.CSSProperties
  htmlFor?: string
  href?: string
  target?: string
  rel?: string
}

const SIZE_MAP: Record<TextSize, string> = {
  xs: 'text-xs',
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl',
}

const WEIGHT_MAP: Record<TextWeight, string> = {
  normal: 'font-normal',
  medium: 'font-medium',
  semibold: 'font-semibold',
  bold: 'font-bold',
}

const COLOR_MAP: Record<TextColor, string> = {
  default: 'text-foreground',
  muted: 'text-muted-foreground',
  emphasis: 'text-foreground',
  accent: 'text-accent-foreground',
  error: 'text-destructive',
  success: 'text-green-600',
  warning: 'text-yellow-600',
}

const ALIGN_MAP: Record<TextAlign, string> = {
  left: 'text-left',
  center: 'text-center',
  right: 'text-right',
}

export const Text: React.FC<TextProps> = ({
  as: Tag = 'p',
  size = 'md',
  weight = 'normal',
  color = 'default',
  align,
  truncate = false,
  mono = false,
  className = '',
  children,
  style,
  htmlFor,
  ...rest
}) => {
  const cls = [
    SIZE_MAP[size],
    WEIGHT_MAP[weight],
    COLOR_MAP[color],
    align ? ALIGN_MAP[align] : '',
    truncate ? 'truncate' : '',
    mono ? 'font-mono' : '',
    className,
  ].filter(Boolean).join(' ')

  return (
    <Tag className={cls} style={style} htmlFor={Tag === 'label' ? htmlFor : undefined} {...rest}>
      {children}
    </Tag>
  )
}
