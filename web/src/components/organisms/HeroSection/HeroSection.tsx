import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Button } from '@/components/atoms/Button'
import { Badge } from '@/components/atoms/Badge'

export interface HeroAction {
  label: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
}

export interface HeroSectionProps {
  badge?: string
  title: string
  subtitle?: string
  primaryAction?: HeroAction
  secondaryAction?: HeroAction
  children?: React.ReactNode
  className?: string
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  badge,
  title,
  subtitle,
  primaryAction,
  secondaryAction,
  children,
  className,
}) => {
  return (
    <Box
      as="section"
      className={[
        'relative overflow-hidden border-b border-border bg-gradient-to-b from-accent/40 to-background',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <Stack
        align="center"
        spacing="md"
        className="mx-auto w-full max-w-4xl px-4 py-20 text-center sm:px-6 lg:px-8"
      >
        {badge && (
          <Badge variant="accent" size="md" dot>
            {badge}
          </Badge>
        )}
        <Heading level={1} size="3xl" weight="bold" color="default" className="tracking-tight">
          {title}
        </Heading>
        {subtitle && (
          <Text size="lg" color="muted" className="max-w-2xl">
            {subtitle}
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
        {children}
      </Stack>
    </Box>
  )
}
