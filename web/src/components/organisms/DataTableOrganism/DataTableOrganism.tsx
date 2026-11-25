import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Badge } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { DataTable, type DataTableColumn } from '@/components/molecules/DataTable'

export interface DataTableOrganismProps<T> {
  title: string
  description?: string
  badge?: {
    variant: 'default' | 'accent' | 'success' | 'warning' | 'error' | 'muted'
    label: string
  }
  columns: DataTableColumn<T>[]
  data: T[]
  pageSize?: number
  isLoading?: boolean
  emptyMessage?: string
  searchPlaceholder?: string
  className?: string
  rowKey?: (row: T) => string | number
  onRowClick?: (row: T) => void
  actions?: React.ReactNode
}

/**
 * Organisme DataTable : titre + description + badge optionnel + DataTable
 * (recherche, tri, pagination).
 *
 * Concu pour etre reuse par n importe quelle page ou organism ayant besoin
 * d afficher un tableau de donnees dynamiques.
 */
export const DataTableOrganism = <T extends object>({
  title,
  description,
  badge,
  columns,
  data,
  pageSize,
  isLoading,
  emptyMessage,
  searchPlaceholder,
  className,
  rowKey,
  onRowClick,
  actions,
}: DataTableOrganismProps<T>) => {
  return (
    <Box
      className={[
        'rounded-xl border border-border bg-card p-6 shadow-sm',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <Stack spacing="md">
        <Flex align="start" justify="between" gap="md" wrap>
          <Stack spacing="sm">
            <Heading level={2} size="lg" weight="semibold" color="default">
              {title}
            </Heading>
            {description && <Text size="sm" color="muted">{description}</Text>}
          </Stack>
          <Flex align="center" gap="sm" wrap>
            {badge && (
              <Badge variant={badge.variant} size="sm">
                {badge.label}
              </Badge>
            )}
            {actions && <Box className="flex items-center gap-2">{actions}</Box>}
          </Flex>
        </Flex>

        <Divider className="my-2" />

        <DataTable<T>
          columns={columns}
          data={data}
          pageSize={pageSize}
          isLoading={isLoading}
          emptyMessage={emptyMessage}
          searchPlaceholder={searchPlaceholder}
          rowKey={rowKey}
          onRowClick={onRowClick}
        />
      </Stack>
    </Box>
  )
}

export default DataTableOrganism
