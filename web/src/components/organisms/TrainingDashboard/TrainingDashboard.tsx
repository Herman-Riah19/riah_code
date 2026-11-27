import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Divider } from '@/components/atoms/Divider'
import { JobMonitor } from '@/components/organisms/JobMonitor'
import { TrainingCharts } from '@/components/organisms/TrainingCharts'
import type { TrainingJob, TrainingHistoryEntry } from '@/types/training'
import type { JobConfigField } from '@/types/job'

const TRAIN_CONFIG_FIELDS: JobConfigField[] = [
  { key: 'modelName', label: 'Modele', icon: 'sparkles-icon' },
  { key: 'batchSize', label: 'Batch size', icon: 'database-icon' },
  { key: 'seqLen', label: 'Seq length', icon: 'hash-icon' },
  { key: 'maxSteps', label: 'Max steps', icon: 'loader-icon' },
  { key: 'lr', label: 'Learning rate', icon: 'trending-up-icon' },
  { key: 'dtype', label: 'Precision', icon: 'cpu-icon' },
  { key: 'optimizer', label: 'Optimizer', icon: 'settings-icon' },
  { key: 'scheduler', label: 'Scheduler', icon: 'bar-chart-icon' },
]

const TRAIN_PROGRESS_LABELS: Record<string, string> = {
  step: 'Step actuel',
  epoch: 'Epoch',
  progress: 'Progression',
  loss: 'Loss (train)',
  bestValLoss: 'Best Val Loss',
  tokensSeen: 'Tokens vus',
  learningRate: 'Learning rate',
}

interface TrainingDashboardProps {
  job: TrainingJob | null
  history: TrainingHistoryEntry[]
  isStreaming: boolean
  onStart?: () => void
  onCancel?: () => void
  onResume?: () => void
  onDismiss?: () => void
  className?: string
}

export function TrainingDashboard({
  job,
  history,
  isStreaming,
  onStart,
  onCancel,
  onResume,
  onDismiss,
  className,
}: TrainingDashboardProps) {
  if (!job) {
    return (
      <Box className={['rounded-xl border border-border bg-card p-8 shadow-sm text-center', className].filter(Boolean).join(' ')}>
        <Stack spacing="md" align="center">
          <Heading level={2} size="xl" color="muted">
            Aucun entrainement en cours
          </Heading>
          <Text size="md" color="muted" className="max-w-md">
            Lancez un nouvel entrainement ou selectionnez un job existant pour voir les metriques en temps reel.
          </Text>
          {onStart && (
            <Box as="button"
              onClick={onStart}
              className="mt-4 px-6 py-3 rounded-lg bg-accent text-accent-foreground font-medium hover:bg-accent/90 transition-colors cursor-pointer"
              role="button"
              tabIndex={0}
            >
              Demarrer un entrainement
            </Box>
          )}
        </Stack>
      </Box>
    )
  }

  const isActive = job.status === 'pending' || job.status === 'running'
  const maxSteps = job.config?.trainingConfig?.maxSteps ?? job.progress?.maxSteps ?? 100000

  // Convert TrainingJob to MonitorableJob for JobMonitor
  const monitorableJob = {
    ...job,
    config: { ...job.config.trainingConfig, modelName: job.config.modelName },
  }

  return (
    <Box
      className={['rounded-xl border border-border bg-card shadow-sm overflow-hidden', className].filter(Boolean).join(' ')}
    >
      {/* Header with JobMonitor */}
      <JobMonitor
        job={monitorableJob}
        title="Entrainement"
        progressLabels={TRAIN_PROGRESS_LABELS}
        configFields={TRAIN_CONFIG_FIELDS}
        onResume={onResume}
        onDismiss={onDismiss}
      />

      <Divider />

      {/* Streaming indicator */}
      {(isActive || isStreaming) && (
        <Box className="px-6 py-3 bg-accent/5 border-b border-border">
          <Flex align="center" justify="between" gap="md">
            <Flex align="center" gap="sm">
              <Box
                className="w-2 h-2 rounded-full bg-accent animate-pulse"
                aria-hidden="true"
              />
              <Text size="sm" weight="medium" color="accent">
                {isStreaming ? 'Flux en direct actif' : 'Entrainement en cours...'}
              </Text>
            </Flex>
            {isActive && onCancel && (
              <Box
                as="button"
                onClick={onCancel}
                className="px-3 py-1.5 rounded-md bg-red-100 text-red-700 text-sm font-medium hover:bg-red-200 transition-colors cursor-pointer"
                role="button"
                tabIndex={0}
              >
                Annuler
              </Box>
            )}
          </Flex>
        </Box>
      )}

      {/* Charts */}
      <Box className="p-6">
        <TrainingCharts
          history={history}
          currentProgress={job.progress}
          maxSteps={maxSteps}
        />
      </Box>

      {/* Data info panel */}
      {job.config?.trainingConfig && (
        <Box className="px-6 pb-6">
          <Divider className="my-4" />
          <Stack spacing="md">
            <Heading level={3} size="md" weight="semibold">
              Donnees d'entrainement
            </Heading>
            <Flex wrap gap="lg" className="text-sm">
              <Box className="flex items-center gap-2">
                <Text color="muted">Shards train:</Text>
                <Text weight="medium" className="font-mono">
                  {job.config.trainingConfig.trainShards?.length ?? 0}
                </Text>
              </Box>
              <Box className="flex items-center gap-2">
                <Text color="muted">Shards val:</Text>
                <Text weight="medium" className="font-mono">
                  {job.config.trainingConfig.valShards?.length ?? 0}
                </Text>
              </Box>
              <Box className="flex items-center gap-2">
                <Text color="muted">Batch effectif:</Text>
                <Text weight="medium" className="font-mono">
                  {formatEstimatedTokensPerStep(job.config.trainingConfig)}
                </Text>
              </Box>
              <Box className="flex items-center gap-2">
                <Text color="muted">Gradient accum:</Text>
                <Text weight="medium" className="font-mono">
                  {job.config.trainingConfig.gradientAccumulationSteps ?? 1}
                </Text>
              </Box>
              <Box className="flex items-center gap-2">
                <Text color="muted">Tokens/step (est.):</Text>
                <Text weight="medium" className="font-mono">
                  {formatTokensPerStep(job.config.trainingConfig)}
                </Text>
              </Box>
              <Box className="flex items-center gap-2">
                <Text color="muted">Objectif 1B+ questions:</Text>
                <Text weight="medium" className="font-mono text-accent">
                  {formatBillionTarget(job.config.trainingConfig)}
                </Text>
              </Box>
            </Flex>
          </Stack>
        </Box>
      )}

      {/* Model performance panel */}
      {(job.result || (job.status === 'completed' && job.progress.bestValLoss !== null)) && (
        <Box className="px-6 pb-6">
          <Divider className="my-4" />
          <Stack spacing="md">
            <Heading level={3} size="md" weight="semibold">
              Performance du modele
            </Heading>
            <Flex wrap gap="lg" className="text-sm">
              <Box className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 min-w-[160px]">
                <Text size="xs" color="muted" weight="semibold">Perplexite (train)</Text>
                <Text size="xl" weight="bold" color="default" className="font-mono">
                  {job.progress.loss !== null ? Math.exp(job.progress.loss).toFixed(2) : 'N/A'}
                </Text>
              </Box>
              <Box className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 min-w-[160px]">
                <Text size="xs" color="muted" weight="semibold">Perplexite (val)</Text>
                <Text size="xl" weight="bold" color="default" className="font-mono">
                  {job.progress.bestValLoss !== null ? Math.exp(job.progress.bestValLoss).toFixed(2) : 'N/A'}
                </Text>
              </Box>
              <Box className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 min-w-[160px]">
                <Text size="xs" color="muted" weight="semibold">Loss final</Text>
                <Text size="xl" weight="bold" color="default" className="font-mono">
                  {job.result?.finalLoss !== undefined && job.result?.finalLoss !== null
                    ? job.result.finalLoss.toFixed(4)
                    : job.progress.loss?.toFixed(4) ?? 'N/A'}
                </Text>
              </Box>
              <Box className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 min-w-[160px]">
                <Text size="xs" color="muted" weight="semibold">Steps effectues</Text>
                <Text size="xl" weight="bold" color="default" className="font-mono">
                  {job.result?.steps ?? job.progress.step}
                </Text>
              </Box>
              <Box className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 min-w-[160px]">
                <Text size="xs" color="muted" weight="semibold">Tokens totaux</Text>
                <Text size="xl" weight="bold" color="default" className="font-mono">
                  {formatNumber(job.result?.tokensSeen ?? job.progress.tokensSeen)}
                </Text>
              </Box>
              <Box className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 min-w-[160px]">
                <Text size="xs" color="muted" weight="semibold">Duree</Text>
                <Text size="xl" weight="bold" color="default" className="font-mono">
                  {job.result?.elapsedSeconds ? formatDuration(job.result.elapsedSeconds) : 'N/A'}
                </Text>
              </Box>
            </Flex>
          </Stack>
        </Box>
      )}

      {/* Evaluation panel placeholder */}
      <Box className="px-6 pb-6">
        <Divider className="my-4" />
        <Stack spacing="md">
          <Heading level={3} size="md" weight="semibold">
            Evaluation Q&R (1B+ questions)
          </Heading>
          <Text size="sm" color="muted">
            Panel d'evaluation sur un large jeu de questions-reponses pour mesurer l'evolution des capacites.
            Disponible apres la premiere evaluation (evalInterval steps).
          </Text>
        </Stack>
      </Box>
    </Box>
  )
}

function formatEstimatedTokensPerStep(config: TrainingJob['config']['trainingConfig']): string {
  if (!config) return 'N/A'
  const batchSize = config.microBatchSize ?? config.batchSize
  const seqLen = config.seqLen
  const gradAccum = config.gradientAccumulationSteps
  const tokens = batchSize * seqLen * gradAccum
  return tokens >= 1e6 ? `${(tokens / 1e6).toFixed(1)}M` : tokens >= 1e3 ? `${(tokens / 1e3).toFixed(0)}k` : String(tokens)
}

function formatTokensPerStep(config: TrainingJob['config']['trainingConfig']): string {
  if (!config) return 'N/A'
  const batchSize = config.microBatchSize ?? config.batchSize
  const seqLen = config.seqLen
  const tokens = batchSize * seqLen
  return tokens >= 1e6 ? `${(tokens / 1e6).toFixed(1)}M` : tokens >= 1e3 ? `${(tokens / 1e3).toFixed(0)}k` : String(tokens)
}

function formatBillionTarget(config: TrainingJob['config']['trainingConfig']): string {
  if (!config) return 'N/A'
  const tokensPerStep = (config.microBatchSize ?? config.batchSize) * config.seqLen * config.gradientAccumulationSteps
  const totalSteps = config.maxSteps
  const totalTokens = tokensPerStep * totalSteps
  const billions = totalTokens / 1e9
  return billions >= 1 ? `${billions.toFixed(1)}B` : `${(billions * 1000).toFixed(0)}M`
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}min`
  return `${(seconds / 3600).toFixed(1)}h`
}

function formatNumber(num: number): string {
  if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`
  if (num >= 1e3) return `${(num / 1e3).toFixed(1)}k`
  return num.toLocaleString()
}