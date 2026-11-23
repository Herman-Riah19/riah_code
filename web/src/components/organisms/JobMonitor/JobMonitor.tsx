import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Badge, type BadgeVariant } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { Button } from '@/components/atoms/Button'
import { Icon } from '@/components/atoms/Icon'
import { Spinner } from '@/components/atoms/Spinner'
import { formatNumber } from '@/utils/format'
import type { CorpusJob, JobStatus } from '@/types/corpus'

export interface JobMonitorProps {
  job: CorpusJob | null
  onResume?: () => void
  onDismiss?: () => void
  className?: string
}

const STATUS_CONFIG: Record<JobStatus, { variant: BadgeVariant; icon: string; label: string }> = {
  pending: { variant: 'muted', icon: 'clock-icon', label: 'En attente' },
  running: { variant: 'accent', icon: 'loader-icon', label: 'En cours' },
  completed: { variant: 'success', icon: 'check-circle-icon', label: 'Termine' },
  failed: { variant: 'error', icon: 'alert-circle-icon', label: 'Echec' },
  cancelled: { variant: 'default', icon: 'x-circle-icon', label: 'Annule' },
}

const PROGRESS_LABELS: Record<string, string> = {
  documentsScraped: 'Documents scrapes',
  documentsCleaned: 'Documents nettoyes',
  documentsFiltered: 'Documents filtres',
  documentsDeduplicated: 'Documents dedupliques',
  documentsExported: 'Documents exportes (MD)',
  shardsWritten: 'Shards ecrits',
  totalTokens: 'Total tokens',
}

export const JobMonitor: React.FC<JobMonitorProps> = ({
  job,
  onResume,
  onDismiss,
  className,
}) => {
  if (!job) return null

  const statusConfig = STATUS_CONFIG[job.status] ?? STATUS_CONFIG.pending
  const isActive = job.status === 'pending' || job.status === 'running'
  const isTerminal = job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled'

  return (
    <Box
      className={[
        'rounded-xl border border-border bg-card p-6 shadow-sm',
        className,
      ].filter(Boolean).join(' ')}
      role="status"
      aria-live={isActive ? 'polite' : 'off'}
    >
      <Flex align="start" justify="between" gap="md" className="mb-4">
        <Flex align="center" gap="sm" className="flex-1 min-w-0">
          <Flex
            align="center"
            justify="center"
            className={`h-10 w-10 rounded-lg flex-shrink-0 ${
              job.status === 'running'
                ? 'bg-accent/20'
                : job.status === 'completed'
                ? 'bg-green-100'
                : job.status === 'failed'
                ? 'bg-red-100'
                : 'bg-muted/50'
            }`}
          >
            <Icon name={statusConfig.icon} size="md" color={job.status === 'running' ? 'accent' : job.status === 'completed' ? 'success' : job.status === 'failed' ? 'error' : 'muted'} aria-hidden />
            {job.status === 'running' && (
              <Spinner size="md" color="accent" className="absolute" />
            )}
          </Flex>
          <Stack spacing="xs" className="min-w-0">
            <Flex align="center" gap="sm">
              <Heading level={3} size="md" weight="semibold" color="default" className="truncate">
                Job de scraping
              </Heading>
              <Badge variant={statusConfig.variant} size="sm" dot>
                {statusConfig.label}
              </Badge>
            </Flex>
            <Text size="sm" color="muted" className="font-mono truncate">
              {job.id}
            </Text>
          </Stack>
        </Flex>

        <Flex align="center" gap="sm">
          {isTerminal && onDismiss && (
            <Button variant="ghost" size="sm" onClick={onDismiss} aria-label="Fermer">
              <Icon name="x-icon" size="sm" aria-hidden />
            </Button>
          )}
          {job.status === 'failed' && onResume && (
            <Button variant="outline" size="sm" onClick={onResume} leftIcon={<Icon name="rotate-cw-icon" size="sm" aria-hidden />}>
              Reprendre
            </Button>
          )}
        </Flex>
      </Flex>

      <Divider />

      <Stack spacing="md">
        {job.config && Object.keys(job.config).length > 0 && (
          <Box className="rounded-lg bg-muted/50 p-3">
            <Text size="xs" weight="semibold" color="muted" className="mb-2 uppercase tracking-wide">
              Configuration
            </Text>
            <Flex wrap gap="md" className="text-sm">
              <Box className="flex items-center gap-1">
                <Icon name="database-icon" size="xs" color="muted" aria-hidden />
                <Text color="default">
                  Sources: <Text weight="medium">{(job.config.sources as string[])?.join(', ') || '-'}</Text>
                </Text>
              </Box>
              <Box className="flex items-center gap-1">
                <Icon name="globe-icon" size="xs" color="muted" aria-hidden />
                <Text color="default">
                  Langues: <Text weight="medium">{(job.config.languages as string[])?.join(', ') || '-'}</Text>
                </Text>
              </Box>
              <Box className="flex items-center gap-1">
                <Icon name="file-text-icon" size="xs" color="muted" aria-hidden />
                <Text color="default">
                  Max/doc: <Text weight="medium">{formatNumber(job.config.maxArticlesPerLang as number)}</Text>
                </Text>
              </Box>
            </Flex>
          </Box>
        )}

        {job.progress && Object.keys(job.progress).length > 0 && (
          <Stack spacing="sm">
            <Text size="xs" weight="semibold" color="muted" className="uppercase tracking-wide">
              Progression
            </Text>
            <Box className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {Object.entries(job.progress).map(([key, value]) => {
                if (typeof value !== 'number') return null
                return (
                  <Box key={key} className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50">
                    <Text size="xs" color="muted">{PROGRESS_LABELS[key] ?? key}</Text>
                    <Text size="lg" weight="bold" color="default" className="font-mono">
                      {formatNumber(value)}
                    </Text>
                  </Box>
                )
              })}
            </Box>
          </Stack>
        )}

        {job.status === 'failed' && job.error && (
          <Box className="rounded-lg bg-red-100 border border-red-200 p-3">
            <Flex align="start" gap="sm">
              <Icon name="alert-circle-icon" size="sm" color="error" aria-hidden className="flex-shrink-0 mt-0.5" />
              <Text size="sm" color="error">
                <Text weight="semibold">Erreur: </Text>
                {job.error}
              </Text>
            </Flex>
          </Box>
        )}

        <Flex align="center" justify="between" gap="md" className="text-xs text-muted-foreground pt-2">
          <Box className="flex items-center gap-1">
            <Icon name="calendar-icon" size="xs" aria-hidden />
            <Text>Cree le {new Date(job.createdAt).toLocaleString('fr-FR')}</Text>
          </Box>
          {job.startedAt && (
            <Box className="flex items-center gap-1">
              <Icon name="play-icon" size="xs" aria-hidden />
              <Text>Debute le {new Date(job.startedAt).toLocaleString('fr-FR')}</Text>
            </Box>
          )}
          {job.finishedAt && (
            <Box className="flex items-center gap-1">
              <Icon name="square-icon" size="xs" aria-hidden />
              <Text>Fin le {new Date(job.finishedAt).toLocaleString('fr-FR')}</Text>
            </Box>
          )}
        </Flex>
      </Stack>
    </Box>
  )
}