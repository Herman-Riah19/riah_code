import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Badge } from '@/components/atoms/Badge'
import { Icon } from '@/components/atoms/Icon'
import { Button } from '@/components/atoms/Button'
import { DataTableOrganism } from '@/components/organisms/DataTableOrganism'
import type { DataTableColumn } from '@/components/molecules/DataTable'
import { formatNumber, formatBytes, formatDate } from '@/utils/format'
import type { CorpusDataset } from '@/types/corpus'

export interface CorpusFileInfo {
  id: string
  filename: string
  source: string
  language: string
  sizeBytes: number
  tokenCount?: number
  updatedAt: string
}

export interface CorpusTableProps {
  files: CorpusFileInfo[]
  dataset?: CorpusDataset
  onFileClick?: (file: CorpusFileInfo) => void
  pageSize?: number
  className?: string
}

export const CorpusTable: React.FC<CorpusTableProps> = ({
  files = [],
  dataset,
  onFileClick,
  pageSize = 10,
  className,
}) => {
  const columns: DataTableColumn<CorpusFileInfo>[] = [
    {
      key: 'filename',
      label: 'Fichier',
      cell: (value) => (
        <Flex align="center" gap="sm" className="min-w-0">
          <Icon name="file-text-icon" size="xs" color="muted" aria-hidden />
          <Text size="sm" color="default" className="font-mono truncate">
            {String(value)}
          </Text>
        </Flex>
      ),
    },
    { key: 'source', label: 'Source' },
    {
      key: 'language',
      label: 'Langue',
      cell: (value) => (
        <Badge variant="accent" size="sm">
          {String(value).toUpperCase()}
        </Badge>
      ),
    },
    {
      key: 'sizeBytes',
      label: 'Taille',
      align: 'right',
      cell: (value) => (
        <Text size="sm" color="muted" className="font-mono">
          {formatBytes(Number(value))}
        </Text>
      ),
    },
    {
      key: 'tokenCount',
      label: 'Tokens',
      align: 'right',
      cell: (value) => (
        <Text size="sm" color="muted" className="font-mono">
          {value ? formatNumber(Number(value)) : '-'}
        </Text>
      ),
    },
    {
      key: 'updatedAt',
      label: 'Mise a jour',
      cell: (value) => (
        <Text size="sm" color="muted" className="font-mono">
          {formatDate(String(value))}
        </Text>
      ),
    },
    {
      key: 'action',
      label: 'Action',
      sortable: false,
      cell: (_value, row) => (
        <Button
          variant="ghost"
          size="xs"
          onClick={() => onFileClick?.(row)}
          aria-label={`Ouvrir ${row.filename}`}
        >
          <Icon name="external-link-icon" size="xs" aria-hidden />
        </Button>
      ),
    },
  ]

  return (
    <Box className={className}>
      <DataTableOrganism
        title={dataset ? `Corpus : ${dataset.source}` : 'Fichiers du corpus'}
        description={
          dataset
            ? `${formatNumber(files.length)} fichier(s) • ${formatBytes(dataset.totalSizeBytes)}`
            : 'Liste des fichiers du corpus.'
        }
        badge={{
          variant: files.length > 0 ? 'accent' : 'muted',
          label: files.length > 0 ? `${formatNumber(files.length)} fichier(s)` : 'Vide',
        }}
        columns={columns}
        data={files}
        pageSize={pageSize}
        emptyMessage="Aucun fichier trouve pour ce corpus."
        searchPlaceholder="Rechercher un fichier..."
        rowKey={(row) => row.id}
        onRowClick={(row) => onFileClick?.(row)}
      />
    </Box>
  )
}
