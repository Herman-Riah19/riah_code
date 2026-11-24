import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/atoms/Table'
import { Button } from '@/components/atoms/Button'
import { Badge } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { Icon } from '@/components/atoms/Icon'
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
  page?: number
  pageSize?: number
  onPageChange?: (page: number) => void
  className?: string
}

export const CorpusTable: React.FC<CorpusTableProps> = ({
  files = [],
  dataset,
  onFileClick,
  page = 1,
  pageSize = 10,
  onPageChange,
  className,
}) => {
  const totalPages = Math.ceil(files.length / pageSize) || 1
  const currentPage = Math.max(1, Math.min(page, totalPages))
  const startIndex = (currentPage - 1) * pageSize
  const paginatedFiles = files.slice(startIndex, startIndex + pageSize)

  return (
    <Box className={className}>
      {dataset && (
        <Stack spacing="sm" className="mb-6">
          <Heading level={2} size="xl" weight="semibold" color="default">
            Corpus : {dataset.source}
          </Heading>
          <Flex align="center" gap="md" wrap className="mb-2">
            {dataset.languages.map((lang) => (
              <Badge key={lang} variant="accent" size="sm">
                {lang.toUpperCase()}
              </Badge>
            ))}
            <Badge variant="muted" size="sm">
              {formatNumber(files.length)} fichier(s)
            </Badge>
            <Badge variant="default" size="sm">
              {formatBytes(dataset.totalSizeBytes)}
            </Badge>
          </Flex>
          <Divider />
        </Stack>
      )}

      <Box className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fichier</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Langue</TableHead>
              <TableHead className="text-right">Taille</TableHead>
              <TableHead className="text-right">Tokens</TableHead>
              <TableHead>Mise a jour</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedFiles.length > 0 ? (
              paginatedFiles.map((file) => (
                <TableRow key={file.id}>
                  <TableCell>
                    <Flex align="center" gap="sm" className="min-w-0">
                      <Icon name="file-text-icon" size="xs" color="muted" aria-hidden />
                      <Text size="sm" color="default" className="font-mono truncate">
                        {file.filename}
                      </Text>
                    </Flex>
                  </TableCell>
                  <TableCell>
                    <Text size="sm" color="default">{file.source}</Text>
                  </TableCell>
                  <TableCell>
                    <Badge variant="accent" size="sm">
                      {file.language.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Text size="sm" color="muted" className="font-mono">
                      {formatBytes(file.sizeBytes)}
                    </Text>
                  </TableCell>
                  <TableCell className="text-right">
                    <Text size="sm" color="muted" className="font-mono">
                      {file.tokenCount ? formatNumber(file.tokenCount) : '-'}
                    </Text>
                  </TableCell>
                  <TableCell>
                    <Text size="sm" color="muted">{formatDate(file.updatedAt)}</Text>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={() => onFileClick?.(file)}
                      aria-label={`Ouvrir ${file.filename}`}
                    >
                      <Icon name="external-link-icon" size="xs" aria-hidden />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell>
                  <Text size="sm" color="muted" className="text-center block">
                    Aucun fichier trouve pour ce corpus.
                  </Text>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>

      {totalPages > 1 && (
        <Box className="mt-4 flex items-center justify-between px-4 py-3">
          <Text size="sm" color="muted">
            Page {currentPage} sur {totalPages}
          </Text>
          <Flex align="center" gap="sm">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(currentPage - 1)}
              disabled={currentPage <= 1}
            >
              Precedent
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(currentPage + 1)}
              disabled={currentPage >= totalPages}
            >
              Suivant
            </Button>
          </Flex>
        </Box>
      )}
    </Box>
  )
}