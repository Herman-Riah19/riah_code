import type React from 'react'

export type TextareaVariant = 'default' | 'error' | 'success'
export type TextareaResize = 'none' | 'vertical' | 'horizontal' | 'both'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: TextareaVariant
  resize?: TextareaResize
  isFullWidth?: boolean
  minRows?: number
  className?: string
}

const VARIANT_MAP: Record<TextareaVariant, string> = {
  default: 'border-input bg-background',
  error: 'border-destructive bg-background',
  success: 'border-green-500 bg-background',
}

const RESIZE_MAP: Record<TextareaResize, string> = {
  none: 'resize-none',
  vertical: 'resize-y',
  horizontal: 'resize-x',
  both: 'resize',
}

export const Textarea: React.FC<TextareaProps> = ({
  variant = 'default',
  resize = 'vertical',
  isFullWidth = false,
  minRows = 3,
  className = '',
  style,
  disabled,
  readOnly,
  ...rest
}) => (
  <textarea
    disabled={disabled}
    readOnly={readOnly}
    rows={minRows}
    className={[
      'flex w-full rounded-md border bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
      VARIANT_MAP[variant],
      RESIZE_MAP[resize],
      isFullWidth ? 'w-full' : '',
      className,
    ].filter(Boolean).join(' ')}
    style={style}
    {...rest}
  />
)
