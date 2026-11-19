import type React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
  className?: string
}

export const Card: React.FC<CardProps> = ({ className, children, ...rest }) => {
  return (
    <div
      className={[
        'rounded-xl border border-border bg-card text-card-foreground shadow-sm',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    >
      {children}
    </div>
  )
}
