import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Badge } from '@/components/atoms/Badge'

export interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: {
    value: string
    isPositive: boolean
  }
  badge?: {
    variant: 'default' | 'accent' | 'success' | 'warning' | 'error' | 'muted'
    label: string
  }
  className?: string
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  trend,
  badge,
  className,
}) => {
  return (
    <Box
      className={[
        'rounded-xl border border-border bg-card p-6 shadow-sm',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <Box className="flex items-center justify-between mb-4">
        <Box className="flex items-center gap-2">
          {badge && (
            <Badge variant={badge.variant} size="sm">
              {badge.label}
            </Badge>
          )}
          <Text size="sm" weight="medium" color="muted">
            {title}
          </Text>
        </Box>
      </Box>
      <Heading level={3} size="2xl" weight="bold" color="default">
        {value}
      </Heading>
      {trend && (
        <Text
          size="sm"
          weight="medium"
          color={trend.isPositive ? 'success' : 'error'}
          className="flex items-center gap-1 mt-2"
        >
          {trend.isPositive ? '▲' : '▼'} {trend.value}
        </Text>
      )}
    </Box>
  )
}
