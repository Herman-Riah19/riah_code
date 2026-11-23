import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Badge } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { Button } from '@/components/atoms/Button'

export interface PageHeaderAction {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export interface PageHeaderProps {
  title: string
  subtitle?: string
  eyebrow?: string
  badge?: { variant: 'default' | 'accent' | 'success' | 'warning' | 'error' | 'muted'; label: string }
  actions?: PageHeaderAction[]
  className?: string
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  eyebrow,
  badge,
  actions = [],
  className,
}) => {
  return (
    <Box className={['w-full px-4 py-6 sm:px-6 lg:px-8', className].filter(Boolean).join(' ')} as="header">
      <Stack spacing="sm" className="mb-4">
        {eyebrow && (
          <Flex align="center" gap="sm">
            <Text size="sm" weight="semibold" color="accent" className="uppercase tracking-wide">
              {eyebrow}
            </Text>
            {badge && (
              <Badge variant={badge.variant} size="sm">
                {badge.label}
              </Badge>
            )}
          </Flex>
        )}
        <Heading level={1} size="2xl" weight="bold" color="default">
          {title}
        </Heading>
        {subtitle && <Text size="lg" color="muted">{subtitle}</Text>}
      </Stack>

      {actions.length > 0 && (
        <Divider />
      )}

      {actions.length > 0 && (
        <Flex align="center" justify="end" gap="sm" wrap className="pt-4">
          {actions.map((action, index) => (
            <Button
              key={index}
              variant={action.variant ?? 'primary'}
              onClick={action.onClick}
              isLoading={action.isLoading}
              leftIcon={action.leftIcon}
              rightIcon={action.rightIcon}
            >
              {action.label}
            </Button>
          ))}
        </Flex>
      )}
    </Box>
  )
}