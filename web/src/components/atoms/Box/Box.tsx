import type React from 'react'

export type BoxPadding = 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
export type BoxRadius = 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full'
export type BoxBorder = 'none' | 'subtle' | 'default' | 'accent'
export type BoxBackground = 'transparent' | 'default' | 'muted' | 'accent'

export interface BoxProps extends React.HTMLAttributes<HTMLDivElement> {
  as?: keyof React.JSX.IntrinsicElements
  padding?: BoxPadding
  paddingX?: BoxPadding
  paddingY?: BoxPadding
  margin?: BoxPadding
  borderRadius?: BoxRadius
  border?: BoxBorder
  background?: BoxBackground
  className?: string
  children?: React.ReactNode
  style?: React.CSSProperties
}

const PADDING_MAP: Record<BoxPadding, string> = {
  none: 'p-0',
  xs: 'p-1',
  sm: 'p-2',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
  '2xl': 'p-10',
}

const MARGIN_MAP: Record<BoxPadding, string> = {
  none: 'm-0',
  xs: 'm-1',
  sm: 'm-2',
  md: 'm-4',
  lg: 'm-6',
  xl: 'm-8',
  '2xl': 'm-10',
}

const RADIUS_MAP: Record<BoxRadius, string> = {
  none: 'rounded-none',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  full: 'rounded-full',
}

const BORDER_MAP: Record<BoxBorder, string> = {
  none: '',
  subtle: 'border border-border',
  default: 'border border-border',
  accent: 'border border-border',
}

const BACKGROUND_MAP: Record<BoxBackground, string> = {
  transparent: 'bg-transparent',
  default: 'bg-background',
  muted: 'bg-muted',
  accent: 'bg-accent',
}

export const Box: React.FC<BoxProps> = ({
  as: Tag = 'div',
  padding,
  paddingX,
  paddingY,
  margin,
  borderRadius = 'none',
  border = 'none',
  background = 'transparent',
  className = '',
  children,
  style,
  ...rest
}) => {
  const cls = [
    padding ? PADDING_MAP[padding] : '',
    paddingX ? PADDING_MAP[paddingX].replace('p-', 'px-') : '',
    paddingY ? PADDING_MAP[paddingY].replace('p-', 'py-') : '',
    margin ? MARGIN_MAP[margin] : '',
    RADIUS_MAP[borderRadius],
    BORDER_MAP[border],
    BACKGROUND_MAP[background],
    className,
  ].filter(Boolean).join(' ')

  return (
    // @ts-expect-error – polymorphic as prop
    <Tag className={cls} style={style} {...rest}>
      {children}
    </Tag>
  )
}
