import type React from 'react'

export type InputSize = 'sm' | 'md' | 'lg'
export type InputVariant = 'default' | 'error' | 'success'

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  size?: InputSize
  variant?: InputVariant
  leftAddon?: React.ReactNode
  rightAddon?: React.ReactNode
  isFullWidth?: boolean
  className?: string
}

const SIZE_MAP: Record<InputSize, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-3 text-base',
  lg: 'h-11 px-4 text-lg',
}

const VARIANT_MAP: Record<InputVariant, string> = {
  default: 'border-input bg-background',
  error: 'border-destructive bg-background',
  success: 'border-green-500 bg-background',
}

export const Input: React.FC<InputProps> = ({
  size = 'md',
  variant = 'default',
  leftAddon,
  rightAddon,
  isFullWidth = false,
  className = '',
  disabled,
  readOnly,
  ...rest
}) => {
  const inputEl = (
    <input
      disabled={disabled}
      readOnly={readOnly}
      className={[
        'flex h-full w-full rounded-md border bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        SIZE_MAP[size],
        VARIANT_MAP[variant],
        className,
      ].filter(Boolean).join(' ')}
      {...rest}
    />
  )

  if (!leftAddon && !rightAddon) return inputEl

  return (
    <span className={['inline-flex items-center rounded-md border border-input bg-background px-3 py-2', isFullWidth ? 'w-full' : ''].filter(Boolean).join(' ')}>
      {leftAddon && <span className="flex items-center gap-2 text-muted-foreground">{leftAddon}</span>}
      {inputEl}
      {rightAddon && <span className="flex items-center gap-2 text-muted-foreground">{rightAddon}</span>}
    </span>
  )
}
