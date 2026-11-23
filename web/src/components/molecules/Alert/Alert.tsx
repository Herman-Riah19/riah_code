import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Icon } from '@/components/atoms/Icon'
import { Button } from '@/components/atoms/Button'

export type AlertVariant = 'info' | 'success' | 'warning' | 'error'

export interface AlertProps {
  variant?: AlertVariant
  title?: string
  message: string
  onDismiss?: () => void
  className?: string
}

const VARIANT_STYLES: Record<AlertVariant, string> = {
  info: 'border-info bg-info/10 text-info-foreground',
  success: 'border-green-500 bg-green-100 text-green-800',
  warning: 'border-yellow-500 bg-yellow-100 text-yellow-800',
  error: 'border-destructive bg-red-100 text-red-800',
}

const ICON_MAP: Record<AlertVariant, string> = {
  info: 'info-icon',
  success: 'check-circle-icon',
  warning: 'alert-triangle-icon',
  error: 'alert-circle-icon',
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  message,
  onDismiss,
  className,
}) => {
  return (
    <Box
      className={[
        'rounded-lg border p-4 gap-3',
        VARIANT_STYLES[variant],
        className,
      ].filter(Boolean).join(' ')}
    >
      <Flex align="start" gap="sm">
        <Icon
          name={ICON_MAP[variant]}
          size="md"
          color="inherit"
          aria-hidden
          className="flex-shrink-0 mt-0.5"
        />
        <Flex direction="column" gap="xs" className="flex-1 min-w-0">
          {title && (
            <Text weight="semibold" size="sm" color="default">
              {title}
            </Text>
          )}
          <Text size="sm" color="default">
            {message}
          </Text>
        </Flex>
        {onDismiss && (
          <Button
            variant="ghost"
            size="xs"
            onClick={onDismiss}
            aria-label="Fermer"
            className="flex-shrink-0 opacity-70 hover:opacity-100"
          >
            <Icon name="x-icon" size="sm" aria-hidden />
          </Button>
        )}
      </Flex>
    </Box>
  )
}