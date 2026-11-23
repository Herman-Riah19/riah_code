import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Badge } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { Icon } from '@/components/atoms/Icon'
import { formatBytes, formatNumber, formatDate } from '@/utils/format'
import type { CorpusDataset } from '@/types/corpus'

export interface ResourceCardProps {
  dataset: CorpusDataset
  onClick?: () => void
  className?: string
}

export const ResourceCard: React.FC<ResourceCardProps> = ({
  dataset,
  onClick,
  className,
}) => {
  return (
    <Box
      as={onClick ? 'button' : 'div'}
      onClick={onClick}
      className={[
        'p-5 transition-all hover:shadow-md cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring',
        'rounded-xl border border-border bg-card',
        className,
      ].filter(Boolean).join(' ')}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <Flex align="start" justify="between" gap="sm" className="mb-3">
        <Flex align="center" gap="sm" className="flex-1 min-w-0">
          <Flex
            align="center"
            justify="center"
            className="h-10 w-10 rounded-lg bg-accent text-accent-foreground flex-shrink-0"
          >
            <Icon name="database-icon" size="md" color="inherit" aria-hidden />
          </Flex>
          <Stack spacing="xs" className="min-w-0">
            <Heading level={3} size="md" weight="semibold" color="default" className="truncate">
              {dataset.source}
            </Heading>
            <Flex align="center" gap="xs" wrap>
              {dataset.languages.map((lang) => (
                <Badge key={lang} variant="accent" size="sm">
                  {lang.toUpperCase()}
                </Badge>
              ))}
            </Flex>
          </Stack>
        </Flex>
        <Text size="xs" color="muted" className="flex-shrink-0 whitespace-nowrap">
          MAJ {formatDate(dataset.updatedAt)}
        </Text>
      </Flex>

      <Divider />

      <Flex align="center" justify="between" gap="md" wrap className="text-sm">
        <Box className="flex items-center gap-2">
          <Icon name="file-text-icon" size="xs" color="muted" aria-hidden />
          <Text weight="medium" color="default">
            {formatNumber(dataset.documentCount)} documents
          </Text>
        </Box>
        <Box className="flex items-center gap-2">
          <Icon name="hard-drive-icon" size="xs" color="muted" aria-hidden />
          <Text weight="medium" color="default">
            {formatBytes(dataset.totalSizeBytes)}
          </Text>
        </Box>
      </Flex>

      <Text
        size="xs"
        color="muted"
        className="mt-2 truncate font-mono"
        style={{ opacity: 0.8 }}
      >
        {dataset.path}
      </Text>
    </Box>
  )
}