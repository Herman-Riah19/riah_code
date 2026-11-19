import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Button } from '@/components/atoms/Button'

export interface CallToActionAction {
  label: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
}

export interface CallToActionProps {
  title: string
  description?: string
  primaryAction?: CallToActionAction
  secondaryAction?: CallToActionAction
  note?: string
  className?: string
}

export const CallToAction: React.FC<CallToActionProps> = ({
  title,
  description,
  primaryAction,
  secondaryAction,
  note,
  className,
}) => {
  return (
    <Box
      as="section"
      className={['px-4 py-16 sm:px-6 lg:px-8', className].filter(Boolean).join(' ')}
    >
      <Box className="mx-auto max-w-4xl rounded-2xl border border-border bg-card px-6 py-12 text-center shadow-sm sm:px-12">
        <Stack align="center" spacing="sm">
          <Heading level={2} size="2xl" weight="bold" color="default">
            {title}
          </Heading>
          {description && (
            <Text size="lg" color="muted" className="max-w-2xl">
              {description}
            </Text>
          )}
          {(primaryAction || secondaryAction) && (
            <Flex align="center" justify="center" gap="sm" className="pt-4">
              {primaryAction && (
                <Button variant={primaryAction.variant ?? 'primary'} size="lg">
                  {primaryAction.label}
                </Button>
              )}
              {secondaryAction && (
                <Button variant={secondaryAction.variant ?? 'outline'} size="lg">
                  {secondaryAction.label}
                </Button>
              )}
            </Flex>
          )}
          {note && (
            <Text size="xs" color="muted" className="pt-2">
              {note}
            </Text>
          )}
        </Stack>
      </Box>
    </Box>
  )
}
