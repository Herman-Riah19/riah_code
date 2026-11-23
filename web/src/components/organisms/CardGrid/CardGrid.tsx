import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { ResourceCard, type ResourceCardProps } from '@/components/molecules/ResourceCard'

export interface CardGridProps {
  items: ResourceCardProps['dataset'][]
  onItemClick?: (dataset: ResourceCardProps['dataset']) => void
  emptyTitle?: string
  emptyDescription?: string
  emptyAction?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export const CardGrid: React.FC<CardGridProps> = ({
  items,
  onItemClick,
  emptyTitle = 'Aucun corpus disponible',
  emptyDescription = 'Lancez un scraping pour creer votre premier corpus.',
  emptyAction,
  className,
}) => {
  if (items.length === 0) {
    return (
      <Box className={['w-full', className].filter(Boolean).join(' ')} as="section" aria-labelledby="empty-title">
        <Box
          className="flex flex-col items-center justify-center py-16 px-4 text-center"
          role="status"
        >
          <Heading id="empty-title" level={3} size="lg" weight="semibold" color="default">
            {emptyTitle}
          </Heading>
          <Text size="md" color="muted" className="mt-2 max-w-sm">
            {emptyDescription}
          </Text>
          {emptyAction && (
            <button
              type="button"
              onClick={emptyAction.onClick}
              className="mt-4 inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              {emptyAction.label}
            </button>
          )}
        </Box>
      </Box>
    )
  }

  return (
    <Box className={['w-full', className].filter(Boolean).join(' ')} as="section" aria-label="Liste des corpus">
      <Box className="mx-auto grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {items.map((dataset, index) => (
          <ResourceCard key={index} dataset={dataset} onClick={onItemClick ? () => onItemClick(dataset) : undefined} />
        ))}
      </Box>
    </Box>
  )
}