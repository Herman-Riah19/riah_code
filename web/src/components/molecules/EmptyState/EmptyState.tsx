import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Icon } from '@/components/atoms/Icon'
import { Button } from '@/components/atoms/Button'

export interface EmptyStateAction {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
}

export interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  actions?: EmptyStateAction[]
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = 'inbox-icon',
  title,
  description,
  actions = [],
  className,
}) => {
  return (
    <Box
      className={[
        'flex flex-col items-center justify-center py-16 px-4 text-center',
        className,
      ].filter(Boolean).join(' ')}
    >
      <Flex
        align="center"
        justify="center"
        className="h-16 w-16 rounded-full bg-muted text-muted-foreground mb-4"
      >
        <Icon name={icon} size="xl" color="muted" aria-hidden />
      </Flex>
      <Stack spacing="sm" className="max-w-sm">
        <Heading level={3} size="lg" weight="semibold" color="default">
          {title}
        </Heading>
        {description && (
          <Text size="md" color="muted">
            {description}
          </Text>
        )}
        {actions.length > 0 && (
          <Flex align="center" justify="center" gap="sm" className="pt-2 w-full">
            {actions.map((action, index) => (
              <Button
                key={index}
                variant={action.variant ?? 'primary'}
                onClick={action.onClick}
              >
                {action.label}
              </Button>
            ))}
          </Flex>
        )}
      </Stack>
    </Box>
  )
}