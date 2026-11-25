import type React from 'react'
import { useState, useMemo, useCallback } from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/atoms/Table'
import { Icon } from '@/components/atoms/Icon'
import { Input } from '@/components/atoms/Input'
import { Button } from '@/components/atoms/Button'
import { formatNumber } from '@/utils/format'

export interface DataTableColumn<T> {
  key: string
  label: string
  sortable?: boolean
  align?: 'left' | 'center' | 'right'
  cell?: (value: unknown, row: T) => React.ReactNode
  className?: string
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  pageSize?: number
  isLoading?: boolean
  emptyMessage?: string
  searchPlaceholder?: string
  className?: string
  rowKey?: (row: T, index?: number) => string | number
  onRowClick?: (row: T) => void
}

/**
 * DataTable generique et reusable.
 *
 * Fournit : recherche textuelle, tri par colonne, pagination, et rendu
 * dynamique des colonnes via des renderers optionnels.
 *
 * Usage :
 *   <DataTable
 *     columns={[
 *       { key: 'name', label: 'Nom', sortable: true },
 *       { key: 'value', label: 'Valeur', align: 'right' },
 *     ]}
 *     data={rows}
 *     emptyMessage="Aucune donnee"
 *   />
 */
export const DataTable = <T extends object>({
  columns,
  data,
  pageSize = 10,
  isLoading = false,
  emptyMessage = 'Aucune donnee trouvee.',
  searchPlaceholder = 'Rechercher...',
  className,
  rowKey = (_row: T, index?: number) => String(index ?? 0),
  onRowClick,
}: DataTableProps<T>) => {
  const [currentPage, setCurrentPage] = useState(1)
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)

  const filtered = useMemo(() => {
    const term = search.toLowerCase().trim()
    if (!term) return data
    return data.filter((row) =>
      columns.some((col) => {
        const value = (row as Record<string, unknown>)[col.key]
        return String(value ?? '').toLowerCase().includes(term)
      }),
    )
  }, [data, search, columns])

  const sorted = useMemo(() => {
    if (!sort) return filtered
    const dir = sort.dir === 'asc' ? 1 : -1
    return [...filtered].sort((a, b) => {
      const av = (a as Record<string, unknown>)[sort.key]
      const bv = (b as Record<string, unknown>)[sort.key]
      if (typeof av === 'number' && typeof bv === 'number') {
        return (av - bv) * dir
      }
      return String(av ?? '').localeCompare(String(bv ?? ''), 'fr', {
        numeric: true,
        sensitivity: 'base',
      }) * dir
    })
  }, [filtered, sort])

  const handleSort = useCallback((key: string) => {
    setSort((prev) => {
      if (prev?.key === key) {
        return prev.dir === 'asc' ? { key, dir: 'desc' } : null
      }
      return { key, dir: 'asc' }
    })
  }, [])

  const totalPages = Math.ceil(sorted.length / pageSize) || 1
  const page = Math.max(1, Math.min(currentPage, totalPages))
  const startIndex = (page - 1) * pageSize
  const paginated = sorted.slice(startIndex, startIndex + pageSize)

  const handlePageChange = (delta: number) => {
    setCurrentPage((prev) => Math.max(1, Math.min(totalPages, prev + delta)))
  }

  const alignClass = (align?: 'left' | 'center' | 'right') => {
    if (align === 'right') return 'text-right'
    if (align === 'center') return 'text-center'
    return 'text-left'
  }

  const rowOf = (row: T): Record<string, unknown> => row as Record<string, unknown>

  return (
    <Box className={className}>
      <Stack spacing="sm">
        <Input
          placeholder={searchPlaceholder}
          value={search}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(event.currentTarget.value)
          }
          leftAddon={<Icon name="search-icon" size="sm" aria-hidden />}
          isFullWidth
          disabled={isLoading}
        />
      </Stack>

      <Box className="overflow-x-auto rounded-xl border border-border bg-muted/30">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => {
                const isSortable = col.sortable !== false
                return (
                  <TableHead
                    key={String(col.key)}
                    className={[
                      alignClass(col.align),
                      isSortable ? 'cursor-pointer select-none' : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    onClick={
                      isSortable ? () => handleSort(String(col.key)) : undefined
                    }
                  >
                    <Flex align="center" gap="xs">
                      <Text size="sm" weight="medium" color="muted">
                        {col.label}
                      </Text>
                      {isSortable && sort?.key === col.key && (
                        <Icon
                          name={sort.dir === 'asc' ? 'chevron-up-icon' : 'chevron-down-icon'}
                          size="xs"
                          color="accent"
                          aria-hidden
                        />
                      )}
                    </Flex>
                  </TableHead>
                )
              })}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginated.length > 0 ? (
              paginated.map((row: T, index: number) => {
                const key = rowKey(row, startIndex + index)
                return (
                  <TableRow
                    key={key}
                    onClick={() => onRowClick?.(row)}
                    className="cursor-pointer"
                  >
                    {columns.map((col) => (
                      <TableCell key={String(col.key)} className={alignClass(col.align)}>
                        {col.cell ? (
                          col.cell(rowOf(row)[col.key], row)
                        ) : (
                          <Text
                            size="sm"
                            color="default"
                            className={[
                              'font-mono',
                              col.align === 'right' ? 'text-right' : '',
                              col.align === 'center' ? 'text-center' : '',
                            ]
                              .filter(Boolean)
                              .join(' ')}
                          >
                            {String(rowOf(row)[col.key] ?? '-')}
                          </Text>
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                )
              })
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <Text size="sm" color="muted" className="text-center block">
                    {emptyMessage}
                  </Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>

      {totalPages > 1 && (
        <Flex align="center" justify="between" className="mt-4 pt-4">
          <Text size="sm" color="muted">
            Page {page} sur {totalPages} •{' '}
            {formatNumber(Math.min(startIndex + 1, sorted.length))} à{' '}
            {formatNumber(Math.min(startIndex + paginated.length, sorted.length))} sur{' '}
            {formatNumber(sorted.length)}
          </Text>
          <Box className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(-1)}
              disabled={page <= 1 || isLoading}
              aria-label="Page precedente"
            >
              <Icon name="chevron-left-icon" size="sm" aria-hidden />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(1)}
              disabled={page >= totalPages || isLoading}
              aria-label="Page suivante"
            >
              <Icon name="chevron-right-icon" size="sm" aria-hidden />
            </Button>
          </Box>
        </Flex>
      )}
    </Box>
  )
}

export default DataTable
