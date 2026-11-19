import type React from 'react'
import { Card } from '@/components/atoms/Card'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Heading } from '@/components/atoms/Heading'
import { Text } from '@/components/atoms/Text'
import { Icon } from '@/components/atoms/Icon'

export interface FeatureCardProps {
  icon?: string
  title: string
  description: string
  className?: string
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  description,
  className,
}) => {
  return (
    <Card
      className={[
        'p-6 transition-shadow hover:shadow-md',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <Stack spacing="sm">
        {icon && (
          <Flex
            align="center"
            justify="center"
            className="h-10 w-10 rounded-lg bg-accent text-accent-foreground"
          >
            <Icon name={icon} size="md" color="inherit" aria-hidden />
          </Flex>
        )}
        <Heading level={3} size="md" weight="semibold" color="default">
          {title}
        </Heading>
        <Text size="sm" color="muted">
          {description}
        </Text>
      </Stack>
    </Card>
  )
}
