import type React from 'react'

export interface TabProps extends React.HTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode
  className?: string
  isActive?: boolean
}

export const Tab: React.FC<TabProps> = ({ className, isActive = false, ...rest }) => {
  return (
    <button
      className={[
        'inline-flex items-center justify-center rounded-md border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        isActive
          ? 'bg-accent text-accent-foreground'
          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    />
  )
}
