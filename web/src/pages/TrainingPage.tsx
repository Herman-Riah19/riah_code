import { useState } from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'
import { Select } from '@/components/atoms/Select'
import { Badge } from '@/components/atoms/Badge'
import { Icon } from '@/components/atoms/Icon'
import { Alert } from '@/components/molecules/Alert'
import { StatCard } from '@/components/molecules/StatCard'
import { TabBar, type TabBarItem } from '@/components/molecules/TabBar'
import { TrainingDashboard } from '@/components/organisms/TrainingDashboard'
import { TrainingCharts } from '@/components/organisms/TrainingCharts'
import { useTrainingDashboard } from '@/hooks/useTrainingDashboard'
import { formatBillionProgress, formatNumber, formatTokensPerStep, formatTotalTokens } from '@/utils/format'

const PRESET_OPTIONS = [
  { value: 'tiny', label: 'Tiny (test)' },
  { value: '125M', label: '125M parametres' },
  { value: '350M', label: '350M parametres' },
  { value: '760M', label: '760M parametres' },
  { value: '1.3B', label: '1.3B parametres' },
]

const DTYPE_OPTIONS = [
  { value: 'fp32', label: 'FP32 (CPU)' },
  { value: 'fp16', label: 'FP16 (GPU)' },
  { value: 'bf16', label: 'BF16 (GPU, recommandé)' },
]

type TabId = 'dashboard' | 'charts' | 'jobs' | 'checkpoints' | 'evaluate'

const TAB_ITEMS: TabBarItem<TabId>[] = [
  { id: 'dashboard', label: 'Tableau de bord', icon: 'layout-dashboard-icon' },
  { id: 'charts', label: 'Graphiques', icon: 'bar-chart-icon' },
  { id: 'jobs', label: 'Historique jobs', icon: 'list-icon' },
  { id: 'checkpoints', label: 'Checkpoints', icon: 'hard-drive-icon' },
  { id: 'evaluate', label: 'Evaluation', icon: 'search-icon' },
]

export function TrainingPage() {
  const {
    jobs,
    activeJob,
    history,
    checkpoints,
    isLoading,
    isSubmitting,
    isStreaming,
    error,
    preset,
    modelName,
    batchSize,
    seqLen,
    maxSteps,
    lr,
    warmupSteps,
    evalInterval,
    checkpointInterval,
    dtype,
    evalPrompt,
    evalResult,
    isEvaluating,
    startTraining,
    cancelJob,
    resumeJob,
    selectJob,
    dismissJob,
    loadCheckpoints,
    evaluate,
    setFormField,
    clearError,
    refresh,
  } = useTrainingDashboard()

  const [activeTab, setActiveTab] = useState<TabId>('dashboard')

  const handleStartTraining = () => {
    void startTraining()
  }

  const handleCancel = (jobId: string) => {
    void cancelJob(jobId)
  }

  const handleResume = (jobId: string) => {
    void resumeJob(jobId)
  }

  const handleEvaluate = () => {
    if (!activeJob) return
    void evaluate(activeJob.id, evalPrompt)
  }

  const activeJobs = jobs.filter((j) => j.status === 'pending' || j.status === 'running')
  const completedJobs = jobs.filter((j) => j.status === 'completed')
  const failedJobs = jobs.filter((j) => j.status === 'failed')

  return (
    <Box className="h-full overflow-auto">
      <Stack spacing="lg" className="p-4 lg:p-6">
        {/* Page Header */}
        <Flex align="center" justify="between" gap="md" wrap className="mb-2">
          <Stack spacing="xs">
            <Heading level={1} size="2xl" weight="bold">
              Entrainement
            </Heading>
            <Text size="md" color="muted">
              Lancez, surveillez et evaluez vos modeles de langage
            </Text>
          </Stack>
          <Flex align="center" gap="sm">
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Icon name="refresh-cw-icon" size="sm" aria-hidden />}
              onClick={refresh}
              disabled={isLoading}
            >
              Actualiser
            </Button>
            <Button
              variant={isSubmitting ? 'primary' : 'outline'}
              size="md"
              leftIcon={isSubmitting ? <Icon name="loader-icon" size="sm" aria-hidden className="animate-spin" /> : <Icon name="play-icon" size="sm" aria-hidden />}
              onClick={handleStartTraining}
              disabled={isSubmitting || isLoading}
            >
              {isSubmitting ? 'Demarrage...' : 'Nouvel entrainement'}
            </Button>
          </Flex>
        </Flex>

        {/* Error Alert */}
        {error && (
          <Alert variant="error" onDismiss={clearError} title="Erreur" message={error} />
        )}

        {/* Stats Row */}
        <Flex wrap gap="md" className="mb-4">
          <StatCard title="Jobs actifs" value={activeJobs.length} />
          <StatCard title="Termines" value={completedJobs.length} />
          <StatCard title="Echecs" value={failedJobs.length} />
          <StatCard title="Checkpoints" value={checkpoints.length} />
        </Flex>

        {/* Tab Bar */}
        <TabBar
          items={TAB_ITEMS}
          activeId={activeTab}
          onChange={setActiveTab}
          className="mb-6"
        />

        {/* Tab Panels */}
        {activeTab === 'dashboard' && (
          <TrainingDashboard
            job={activeJob}
            history={history}
            isStreaming={isStreaming}
            onStart={handleStartTraining}
            onCancel={activeJob ? () => handleCancel(activeJob.id) : undefined}
            onResume={activeJob?.status === 'failed' ? () => handleResume(activeJob.id) : undefined}
            onDismiss={dismissJob}
          />
        )}

        {activeTab === 'charts' && (
          <Box className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <Flex align="start" justify="between" gap="md" className="mb-6">
              <Stack spacing="xs">
                <Heading level={2} size="lg" weight="semibold">
                  Graphiques d'entrainement
                </Heading>
                <Text size="sm" color="muted">
                  Visualisation temps reel des metriques (SSE + historique)
                </Text>
              </Stack>
              {activeJob && (
                <Flex align="center" gap="md">
                  <Badge variant={isStreaming ? 'success' : 'muted'} size="sm" dot>
                    {isStreaming ? 'Flux direct actif' : 'Polling seulement'}
                  </Badge>
                </Flex>
              )}
            </Flex>
            {activeJob ? (
              <TrainingCharts
                history={history}
                currentProgress={activeJob.progress}
                maxSteps={activeJob.config?.trainingConfig?.maxSteps ?? activeJob.progress.maxSteps}
              />
            ) : (
              <Box className="py-12 text-center">
                <Stack spacing="sm" align="center">
                  <Icon name="bar-chart-icon" size="xl" color="muted" aria-hidden />
                  <Text size="lg" color="muted" weight="medium">
                    Aucun job selectionne
                  </Text>
                  <Text size="sm" color="muted">
                    Selectionnez un job dans l'onglet "Historique jobs" ou lancez un nouvel entrainement.
                  </Text>
                </Stack>
              </Box>
            )}
          </Box>
        )}

        {activeTab === 'jobs' && (
          <Box className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
            <Box className="p-4 border-b border-border">
              <Heading level={2} size="lg" weight="semibold">
                Historique des entrainements
              </Heading>
            </Box>
            {isLoading ? (
              <Box className="p-8 text-center">
                <Icon name="loader-icon" size="xl" color="accent" className="animate-spin mx-auto mb-2" aria-hidden />
                <Text color="muted">Chargement...</Text>
              </Box>
            ) : jobs.length === 0 ? (
              <Box className="p-8 text-center">
                <Icon name="list-icon" size="xl" color="muted" aria-hidden className="mx-auto mb-2" />
                <Text size="lg" color="muted" weight="medium">Aucun entrainement</Text>
                <Text size="sm" color="muted">Lancez votre premier entrainement pour commencer.</Text>
              </Box>
            ) : (
              <Box className="divide-y divide-border">
                {jobs.map((job) => (
                  <Box
                    key={job.id}
                    className="p-4 hover:bg-muted/30 transition-colors cursor-pointer"
                    onClick={() => selectJob(job)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectJob(job) } }}
                  >
                    <Flex align="start" justify="between" gap="md">
                      <Flex align="center" gap="md" className="flex-1 min-w-0">
                        <Flex
                          align="center"
                          justify="center"
                          className={`relative h-10 w-10 rounded-lg flex-shrink-0 ${
                            job.status === 'running' ? 'bg-accent/20' :
                            job.status === 'completed' ? 'bg-green-100' :
                            job.status === 'failed' ? 'bg-red-100' :
                            job.status === 'cancelled' ? 'bg-muted/50' : 'bg-blue-100'
                          }`}
                        >
                          <Icon
                            name={
                              job.status === 'running' ? 'loader-icon' :
                              job.status === 'completed' ? 'check-circle-icon' :
                              job.status === 'failed' ? 'alert-circle-icon' :
                              job.status === 'cancelled' ? 'x-circle-icon' : 'clock-icon'
                            }
                            size="md"
                            color={
                              job.status === 'running' ? 'accent' :
                              job.status === 'completed' ? 'success' :
                              job.status === 'failed' ? 'error' : 'muted'
                            }
                            aria-hidden
                          />
                          {job.status === 'running' && (
                            <Icon name="loader-icon" size="md" color="accent" className="absolute animate-spin" aria-hidden />
                          )}
                        </Flex>
                        <Stack spacing="xs" className="min-w-0">
                          <Flex align="center" gap="sm" className="flex-wrap">
                            <Text size="md" weight="semibold" color="default" className="truncate">
                              {job.config?.modelName ?? job.config?.trainingConfig?.modelName ?? 'Entrainement'}
                            </Text>
                            <Badge
                              variant={
                                job.status === 'running' ? 'accent' :
                                job.status === 'completed' ? 'success' :
                                job.status === 'failed' ? 'error' :
                                job.status === 'cancelled' ? 'default' : 'muted'
                              }
                              size="sm"
                              dot
                            >
                              {job.status === 'running' ? 'En cours' :
                               job.status === 'completed' ? 'Termine' :
                               job.status === 'failed' ? 'Echec' :
                               job.status === 'cancelled' ? 'Annule' : 'En attente'}
                            </Badge>
                            {activeJob?.id === job.id && (
                              <Badge variant="accent" size="sm">Actif</Badge>
                            )}
                          </Flex>
                          <Flex align="center" gap="md" className="text-sm text-muted-foreground flex-wrap">
                            <Box className="flex items-center gap-1">
                              <Icon name="hash-icon" size="xs" aria-hidden />
                              <Text className="font-mono">{job.progress.step?.toLocaleString() ?? 0} / {job.progress.maxSteps?.toLocaleString() ?? '?'}</Text>
                            </Box>
                            <Box className="flex items-center gap-1">
                              <Icon name="calendar-icon" size="xs" aria-hidden />
                              <Text>{new Date(job.createdAt).toLocaleString('fr-FR')}</Text>
                            </Box>
                            {job.config?.trainingConfig?.modelConfig?.nParams && (
                              <Box className="flex items-center gap-1">
                                <Icon name="cpu-icon" size="xs" aria-hidden />
                                <Text>{formatNumber(job.config.trainingConfig.modelConfig.nParams)} params</Text>
                              </Box>
                            )}
                          </Flex>
                        </Stack>
                      </Flex>
                      <Flex align="center" gap="sm">
                        {job.status === 'running' && (
                          <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleCancel(job.id) }} leftIcon={<Icon name="x-circle-icon" size="sm" aria-hidden />}>
                            Annuler
                          </Button>
                        )}
                        {job.status === 'failed' && (
                          <Button variant="primary" size="sm" onClick={(e) => { e.stopPropagation(); handleResume(job.id) }} leftIcon={<Icon name="rotate-cw-icon" size="sm" aria-hidden />}>
                            Reprendre
                          </Button>
                        )}
                      </Flex>
                    </Flex>
                    {job.status === 'running' && (
                      <Box className="mt-3 h-1.5 rounded-full bg-muted overflow-hidden">
                        <Box
                          className="h-full bg-accent transition-all duration-500"
                          style={{ width: `${Math.min(100, (job.progress.progress ?? 0) * 100)}%` }}
                        />
                      </Box>
                    )}
                    {job.error && (
                      <Box className="mt-2 p-2 rounded bg-red-100 border border-red-200 text-red-800 text-sm">
                        {job.error}
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        )}

        {activeTab === 'checkpoints' && (
          <Box className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
            <Box className="p-4 border-b border-border flex align-center justify-between gap-md">
              <Heading level={2} size="lg" weight="semibold">Checkpoints</Heading>
              <Button variant="ghost" size="sm" onClick={loadCheckpoints} leftIcon={<Icon name="refresh-cw-icon" size="sm" aria-hidden />}>
                Actualiser
              </Button>
            </Box>
            {checkpoints.length === 0 ? (
              <Box className="p-8 text-center">
                <Icon name="hard-drive-icon" size="xl" color="muted" aria-hidden className="mx-auto mb-2" />
                <Text size="lg" color="muted" weight="medium">Aucun checkpoint</Text>
                <Text size="sm" color="muted">Les checkpoints apparaitront pendant l'entrainement.</Text>
              </Box>
            ) : (
              <Box className="divide-y divide-border">
                {checkpoints.map((ckpt) => (
                  <Box key={ckpt.id} className="p-4 hover:bg-muted/30 transition-colors">
                    <Flex align="center" justify="between" gap="md" wrap>
                      <Flex align="center" gap="md" className="flex-1 min-w-0">
                        <Box className={`flex items-center justify-center w-10 h-10 rounded-lg flex-shrink-0 ${
                          ckpt.isBest ? 'bg-yellow-100' : 'bg-muted/50'
                        }`}>
                          <Icon
                            name={ckpt.isBest ? 'sparkles-icon' : 'hard-drive-icon'}
                            size="md"
                            color={ckpt.isBest ? 'warning' : 'muted'}
                            aria-hidden
                          />
                        </Box>
                        <Stack spacing="xs" className="min-w-0">
                          <Flex align="center" gap="sm" className="flex-wrap">
                            <Text size="md" weight="semibold" color="default" className="truncate">
                              {ckpt.modelName ?? 'Model'} - Step {formatNumber(ckpt.step)}
                            </Text>
                            {ckpt.isBest && <Badge variant="warning" size="sm">Best</Badge>}
                            <Badge variant="default" size="sm">Epoch {ckpt.epoch}</Badge>
                          </Flex>
                          <Flex align="center" gap="md" className="text-sm text-muted-foreground flex-wrap">
                            <Box className="flex items-center gap-1">
                              <Icon name="alert-circle-icon" size="xs" aria-hidden />
                              <Text>Loss: {ckpt.loss.toFixed(4)}</Text>
                            </Box>
                            {ckpt.valLoss !== null && (
                              <Box className="flex items-center gap-1">
                                <Icon name="check-circle-icon" size="xs" aria-hidden />
                                <Text>Val Loss: {ckpt.valLoss.toFixed(4)}</Text>
                              </Box>
                            )}
                            <Box className="flex items-center gap-1">
                              <Icon name="calendar-icon" size="xs" aria-hidden />
                              <Text>{new Date(ckpt.createdAt).toLocaleString('fr-FR')}</Text>
                            </Box>
                            <Box className="flex items-center gap-1">
                              <Icon name="cpu-icon" size="xs" aria-hidden />
                              <Text>{formatNumber(ckpt.modelConfig.nParams)} params</Text>
                            </Box>
                          </Flex>
                        </Stack>
                      </Flex>
                    </Flex>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        )}

        {activeTab === 'evaluate' && (
          <Box className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
            <Box className="p-4 border-b border-border">
              <Heading level={2} size="lg" weight="semibold">Evaluation du modele</Heading>
            </Box>
            <Box className="p-6">
              {activeJob ? (
                <Stack spacing="lg">
                  <Box>
                    <Text size="sm" color="muted" className="mb-2">Prompt de test</Text>
                    <Input
                      value={evalPrompt}
                      onChange={(e) => setFormField('evalPrompt', e.target.value)}
                      placeholder="Entrez une question pour tester le modele..."
                      className="w-full"
                    />
                  </Box>
                  <Flex align="center" gap="md">
                    <Button
                      variant="primary"
                      size="md"
                      leftIcon={isEvaluating ? <Icon name="loader-icon" size="sm" aria-hidden className="animate-spin" /> : <Icon name="search-icon" size="sm" aria-hidden />}
                      onClick={handleEvaluate}
                      disabled={isEvaluating || !activeJob}
                    >
                      {isEvaluating ? 'Generation...' : 'Generer une reponse'}
                    </Button>
                    {evalResult && (
                      <Badge variant="success" size="md" dot>
                        Reponse generee ({evalResult.generatedTokens} tokens)
                      </Badge>
                    )}
                  </Flex>
                  {evalResult && (
                    <Box className="p-4 rounded-lg bg-muted/50 border border-border">
                      <Flex align="center" justify="between" gap="md" className="mb-2">
                        <Text size="sm" weight="semibold" color="muted">Reponse du modele</Text>
                        <Text size="xs" color="muted" className="font-mono">
                          Checkpoint: {evalResult.checkpointId}
                        </Text>
                      </Flex>
                      <Text size="md" color="default" className="whitespace-pre-wrap font-mono">
                        {evalResult.completion}
                      </Text>
                    </Box>
                  )}
                  <Box className="pt-4 border-t border-border">
                    <Text size="sm" color="muted" className="mb-2">Suggestions de prompts d'evaluation</Text>
                    <Flex wrap gap="sm">
                      {[
                        'Qu\'est-ce que l\'intelligence artificielle ?',
                        'Explique la relativite generale simplement.',
                        'Ecrire une fonction Python pour trier une liste.',
                        'Quels sont les dangers du changement climatique ?',
                        'Resume l\'histoire de France en 100 mots.',
                      ].map((prompt) => (
                        <Button
                          key={prompt}
                          variant="ghost"
                          size="sm"
                          onClick={() => setFormField('evalPrompt', prompt)}
                          className="truncate max-w-[200px]"
                        >
                          {prompt}
                        </Button>
                      ))}
                    </Flex>
                  </Box>
                </Stack>
              ) : (
                <Box className="py-12 text-center">
                  <Icon name="search-icon" size="xl" color="muted" aria-hidden className="mx-auto mb-2" />
                  <Text size="lg" color="muted" weight="medium">Aucun job selectionne</Text>
                  <Text size="sm" color="muted">Selectionnez un entrainement termine pour evaluer son modele.</Text>
                </Box>
              )}
            </Box>
          </Box>
        )}

        {/* New Training Form - shown when no active job and on dashboard tab */}
        {activeTab === 'dashboard' && !activeJob && !isLoading && (
          <Box className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <Heading level={2} size="lg" weight="semibold" className="mb-6">Nouvel entrainement</Heading>
            <Stack spacing="lg">
              <Flex wrap gap="lg">
                <Box className="flex-1 min-w-[200px]">
                  <Text size="sm" color="muted" className="mb-1 block">Preset d'architecture</Text>
                  <Select
                    value={preset}
                    onChange={(e) => setFormField('preset', e.target.value)}
                  >
                    {PRESET_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </Select>
                </Box>
                <Box className="flex-1 min-w-[200px]">
                  <Text size="sm" color="muted" className="mb-1 block">Nom du modele</Text>
                  <Input
                    value={modelName}
                    onChange={(e) => setFormField('modelName', e.target.value)}
                    placeholder="default"
                  />
                </Box>
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Precision</Text>
                  <Select
                    value={dtype}
                    onChange={(e) => setFormField('dtype', e.target.value as 'fp32' | 'fp16' | 'bf16')}
                  >
                    {DTYPE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </Select>
                </Box>
              </Flex>

              <Flex wrap gap="lg">
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Batch size</Text>
                  <Input
                    type="number"
                    value={batchSize}
                    onChange={(e) => setFormField('batchSize', parseInt(e.target.value) || 0)}
                    min={1}
                    max={4096}
                  />
                </Box>
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Sequence length</Text>
                  <Input
                    type="number"
                    value={seqLen}
                    onChange={(e) => setFormField('seqLen', parseInt(e.target.value) || 0)}
                    min={8}
                    max={8192}
                  />
                </Box>
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Max steps</Text>
                  <Input
                    type="number"
                    value={maxSteps}
                    onChange={(e) => setFormField('maxSteps', parseInt(e.target.value) || 0)}
                    min={1}
                    max={10_000_000}
                  />
                </Box>
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Learning rate</Text>
                  <Input
                    type="number"
                    step="0.000001"
                    value={lr}
                    onChange={(e) => setFormField('lr', parseFloat(e.target.value) || 0)}
                    min={0}
                  />
                </Box>
              </Flex>

              <Flex wrap gap="lg">
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Warmup steps</Text>
                  <Input
                    type="number"
                    value={warmupSteps}
                    onChange={(e) => setFormField('warmupSteps', parseInt(e.target.value) || 0)}
                    min={0}
                  />
                </Box>
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Eval interval</Text>
                  <Input
                    type="number"
                    value={evalInterval}
                    onChange={(e) => setFormField('evalInterval', parseInt(e.target.value) || 0)}
                    min={0}
                  />
                </Box>
                <Box className="flex-1 min-w-[150px]">
                  <Text size="sm" color="muted" className="mb-1 block">Checkpoint interval</Text>
                  <Input
                    type="number"
                    value={checkpointInterval}
                    onChange={(e) => setFormField('checkpointInterval', parseInt(e.target.value) || 0)}
                    min={0}
                  />
                </Box>
              </Flex>

              <Box className="p-4 rounded-lg bg-muted/50 border border-border">
                <Flex align="center" justify="between" gap="md" wrap>
                  <Stack spacing="xs">
                    <Text size="sm" weight="semibold" color="muted">Estimation de l'echelle</Text>
                    <Flex align="center" gap="md" className="text-sm">
                      <Box className="flex items-center gap-1">
                        <Icon name="database-icon" size="xs" color="muted" aria-hidden />
                        <Text as="span">Tokens/step: <Text as="span" weight="medium" className="font-mono">{formatTokensPerStep(batchSize, seqLen)}</Text></Text>
                      </Box>
                      <Box className="flex items-center gap-1">
                        <Icon name="trending-up-icon" size="xs" color="muted" aria-hidden />
                        <Text as="span">Total estime: <Text as="span" weight="medium" className="font-mono text-accent">{formatTotalTokens(batchSize, seqLen, maxSteps)}</Text></Text>
                      </Box>
                      <Box className="flex items-center gap-1">
                        <Icon name="target-icon" size="xs" color="muted" aria-hidden />
                        <Text as="span">Objectif 1B+: <Text as="span" weight="medium" className="font-mono">{formatBillionProgress(batchSize, seqLen, maxSteps)}</Text></Text>
                      </Box>
                    </Flex>
                  </Stack>
                </Flex>
              </Box>

              <Button
                variant="primary"
                size="lg"
                leftIcon={<Icon name="play-icon" size="md" aria-hidden />}
                onClick={handleStartTraining}
                disabled={isSubmitting}
                className="w-full sm:w-auto"
              >
                {isSubmitting ? 'Initialisation...' : 'Lancer l\'entrainement'}
              </Button>
            </Stack>
          </Box>
        )}
      </Stack>
    </Box>
  )
}
