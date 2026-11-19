import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { FeatureCard } from '@/components/molecules/FeatureCard'

export interface FeatureItem {
  id: string
  icon?: string
  title: string
  description: string
}

export interface FeaturesGridProps {
  eyebrow?: string
  title: string
  subtitle?: string
  items?: FeatureItem[]
  columns?: 2 | 3 | 4
  className?: string
}

const COLUMNS_MAP: Record<2 | 3 | 4, string> = {
  2: 'sm:grid-cols-2',
  3: 'sm:grid-cols-2 lg:grid-cols-3',
  4: 'sm:grid-cols-2 lg:grid-cols-4',
}

export const FeaturesGrid: React.FC<FeaturesGridProps> = ({
  eyebrow,
  title,
  subtitle,
  items = [],
  columns = 3,
  className,
}) => {
  return (
    <Box
      as="section"
      className={['px-4 py-16 sm:px-6 lg:px-8', className].filter(Boolean).join(' ')}
    >
      <Stack align="center" spacing="sm" className="mx-auto mb-12 max-w-2xl text-center">
        {eyebrow && (
          <Text size="sm" weight="semibold" color="accent" className="uppercase tracking-wide">
            {eyebrow}
          </Text>
        )}
        <Heading level={2} size="2xl" weight="bold" color="default">
          {title}
        </Heading>
        {subtitle && (
          <Text size="lg" color="muted">
            {subtitle}
          </Text>
        )}
      </Stack>

      <Box className={`mx-auto grid max-w-6xl grid-cols-1 gap-6 ${COLUMNS_MAP[columns]}`}>
        {items.map((item) => (
          <FeatureCard
            key={item.id}
            icon={item.icon}
            title={item.title}
            description={item.description}
          />
        ))}
      </Box>
    </Box>
  )
}
