import type React from 'react'
import { Box, type BoxProps } from '../Box'

export type FlexDirection = 'row' | 'column' | 'row-reverse' | 'column-reverse'
export type FlexAlign = 'start' | 'center' | 'end' | 'stretch' | 'baseline'
export type FlexJustify = 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'
export type FlexGap = 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl'

export interface FlexProps extends BoxProps {
  direction?: FlexDirection
  align?: FlexAlign
  justify?: FlexJustify
  wrap?: boolean
  gap?: FlexGap
  inline?: boolean
}

const DIRECTION_MAP: Record<FlexDirection, string> = {
  row: 'flex-row',
  column: 'flex-col',
  'row-reverse': 'flex-row-reverse',
  'column-reverse': 'flex-col-reverse',
}

const ALIGN_MAP: Record<FlexAlign, string> = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  stretch: 'items-stretch',
  baseline: 'items-baseline',
}

const JUSTIFY_MAP: Record<FlexJustify, string> = {
  start: 'justify-start',
  center: 'justify-center',
  end: 'justify-end',
  between: 'justify-between',
  around: 'justify-around',
  evenly: 'justify-evenly',
}

const GAP_MAP: Record<FlexGap, string> = {
  none: 'gap-0',
  xs: 'gap-1',
  sm: 'gap-2',
  md: 'gap-4',
  lg: 'gap-6',
  xl: 'gap-8',
}

export const Flex: React.FC<FlexProps> = ({
  direction = 'row',
  align = 'start',
  justify = 'start',
  wrap = false,
  gap = 'none',
  inline = false,
  className = '',
  ...rest
}) => {
  const cls = [
    inline ? 'inline-flex' : 'flex',
    DIRECTION_MAP[direction],
    ALIGN_MAP[align],
    JUSTIFY_MAP[justify],
    wrap ? 'flex-wrap' : 'flex-nowrap',
    GAP_MAP[gap],
    className,
  ].filter(Boolean).join(' ')

  return <Box className={cls} {...rest} />
}
