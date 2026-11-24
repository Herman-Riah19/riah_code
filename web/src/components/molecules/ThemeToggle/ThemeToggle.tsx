import type React from 'react'
import { Button } from '@/components/atoms/Button'
import { Icon } from '@/components/atoms/Icon'
import { Text } from '@/components/atoms/Text'
import { useTheme } from '@/hooks/useTheme'

export interface ThemeToggleProps {
  className?: string
  showLabel?: boolean
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ className, showLabel = false }) => {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'
  const label = isDark ? 'Activer le theme clair' : 'Activer le theme sombre'

  const icon = <Icon name={isDark ? 'sun-icon' : 'moon-icon'} size="sm" aria-hidden />

  return (
    <Button
      variant="ghost"
      size="xs"
      onClick={toggleTheme}
      aria-label={label}
      aria-pressed={isDark}
      className={['p-1.5', showLabel ? 'px-3' : '', className].filter(Boolean).join(' ')}
      leftIcon={showLabel ? icon : undefined}
    >
      {showLabel ? (
        <Text as="span" size="sm" color="default">
          {isDark ? 'Theme clair' : 'Theme sombre'}
        </Text>
      ) : (
        icon
      )}
    </Button>
  )
}
