import { Box } from '@/components/atoms/Box'
import { Button } from '@/components/atoms/Button'
import { Icon } from '@/components/atoms/Icon'
import { Alert } from '@/components/molecules/Alert'
import { StatCard } from '@/components/molecules/StatCard'
import { JobMonitor } from '@/components/organisms/JobMonitor'
import { TokenizerInfoPanel } from '@/components/organisms/TokenizerInfoPanel'
import { TokenizerTrainPanel } from '@/components/organisms/TokenizerTrainPanel'
import { TokenizerEncodePanel } from '@/components/organisms/TokenizerEncodePanel'
import { TokenizerPreviewPanel } from '@/components/organisms/TokenizerPreviewPanel'
import { useTokenizerDashboard } from '@/hooks/useTokenizerDashboard'
import { formatNumber } from '@/utils/format'
import type { JobConfigField } from '@/types/job'

const TOKENIZER_LANGUAGES = ['fr', 'en', 'es', 'de']

const TRAIN_PROGRESS_LABELS: Record<string, string> = {
  vocabSize: 'Taille du vocabulaire',
  compressionRatio: 'Compression (chars/token)',
  oovRate: 'Taux OOV',
}

const ENCODE_PROGRESS_LABELS: Record<string, string> = {
  totalTokens: 'Total tokens',
  totalDocuments: 'Documents encodes',
  shardCount: 'Shards ecrits',
  avgTokensPerDoc: 'Tokens / document',
  durationSeconds: 'Duree (s)',
}

const TRAIN_CONFIG_FIELDS: JobConfigField[] = [
  { key: 'languages', label: 'Langues', icon: 'globe-icon' },
  { key: 'vocabSize', label: 'Vocabulaire', icon: 'hash-icon' },
  { key: 'minFrequency', label: 'Frequence min' },
  { key: 'corpusSampleSize', label: 'Echantillon' },
  { key: 'numThreads', label: 'Threads' },
]

const ENCODE_CONFIG_FIELDS: JobConfigField[] = [
  { key: 'languages', label: 'Langues', icon: 'globe-icon' },
  { key: 'shardSizeTokens', label: 'Taille shard', icon: 'hard-drive-icon' },
]

export function TokenizerPage() {
  const {
    info,
    job,
    isLoading,
    isSubmitting,
    error,
    vocabSize,
    minFrequency,
    corpusSampleSize,
    numThreads,
    trainLanguages,
    setVocabSize,
    setMinFrequency,
    setCorpusSampleSize,
    setNumThreads,
    setTrainLanguages,
    shardSizeTokens,
    encodeLanguages,
    setShardSizeTokens,
    setEncodeLanguages,
    preview,
    isPreviewing,
    previewError,
    train,
    encode,
    runPreview,
    clearPreview,
    clearError,
    dismissJob,
    refresh,
  } = useTokenizerDashboard()

  const isActiveJob = job?.status === 'pending' || job?.status === 'running'
  const isEncodingJob = job?.jobType === 'corpus_encoding'
  const jobTitle = isEncodingJob
    ? "Job d'encodage du corpus"
    : "Job d'entrainement du tokenizer"
  const jobConfigFields = isEncodingJob ? ENCODE_CONFIG_FIELDS : TRAIN_CONFIG_FIELDS
  const jobProgressLabels = isEncodingJob ? ENCODE_PROGRESS_LABELS : TRAIN_PROGRESS_LABELS

  const handleTrain = () => {
    clearError()
    void train()
  }

  const handleEncode = () => {
    clearError()
    void encode()
  }

  return (
    <>
      {error && (
        <Alert
          variant="error"
          title="Erreur"
          message={error}
          onDismiss={clearError}
          className="mb-6"
        />
      )}

      {/* KPI Overview - decision cues at top-left */}
      <Box className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard
          title="Tokens appris par le BPE"
          value={info ? formatNumber(info.vocabSize) : '-'}
          badge={{
            variant: info ? 'success' : 'muted',
            label: info ? 'Pret' : 'Vide',
          }}
        />
        <StatCard
          title="Caracteres par token"
          value={info ? info.compressionRatio.toFixed(2) : '-'}
          badge={{
            variant: info ? 'accent' : 'muted',
            label: info ? 'BPE byte-level' : 'Indisponible',
          }}
        />
        <StatCard
          title="Tokens inconnus a l'encodage"
          value={info ? `${(info.oovRate * 100).toFixed(2)} %` : '-'}
          badge={{
            variant: info ? (info.oovRate > 0 ? 'warning' : 'success') : 'muted',
            label: info ? (info.oovRate > 0 ? 'A surveiller' : 'Aucun') : 'Indisponible',
          }}
        />
        <StatCard
          title={job ? `Statut: ${job.status}` : 'Aucun travail'}
          value={job ? '1' : '0'}
          badge={{
            variant: isActiveJob
              ? 'accent'
              : job?.status === 'failed'
              ? 'error'
              : job?.status === 'completed'
              ? 'success'
              : 'muted',
            label: isActiveJob
              ? 'En cours'
              : job?.status === 'failed'
              ? 'Echec'
              : job?.status === 'completed'
              ? 'Termine'
              : 'Inactif',
          }}
        />
      </Box>

      {/* Job Monitor - operational status with freshness */}
      {job && (
        <JobMonitor
          job={job}
          title={jobTitle}
          progressLabels={jobProgressLabels}
          configFields={jobConfigFields}
          onDismiss={dismissJob}
          className="mb-8"
        />
      )}

      {/* Tokenizer Info - current artifacts */}
      <Box className="mb-8">
        <TokenizerInfoPanel info={info} isLoading={isLoading} />
      </Box>

      {/* Training and encoding actions */}
      <Box className="grid grid-cols-1 gap-6 xl:grid-cols-2 mb-8">
        <TokenizerTrainPanel
          vocabSize={vocabSize}
          onVocabSizeChange={setVocabSize}
          minFrequency={minFrequency}
          onMinFrequencyChange={setMinFrequency}
          corpusSampleSize={corpusSampleSize}
          onCorpusSampleSizeChange={setCorpusSampleSize}
          numThreads={numThreads}
          onNumThreadsChange={setNumThreads}
          languages={trainLanguages}
          onLanguagesChange={setTrainLanguages}
          availableLanguages={TOKENIZER_LANGUAGES}
          onTrain={handleTrain}
          isStarting={isSubmitting}
          isDisabled={isLoading || isActiveJob}
        />
        <TokenizerEncodePanel
          shardSizeTokens={shardSizeTokens}
          onShardSizeTokensChange={setShardSizeTokens}
          languages={encodeLanguages}
          onLanguagesChange={setEncodeLanguages}
          availableLanguages={TOKENIZER_LANGUAGES}
          hasTokenizer={info !== null}
          onEncode={handleEncode}
          isStarting={isSubmitting}
          isDisabled={isLoading || isActiveJob}
        />
      </Box>

      {/* Token preview playground */}
      <TokenizerPreviewPanel
        preview={preview}
        isPreviewing={isPreviewing}
        error={previewError}
        onPreview={(text) => void runPreview(text)}
        onClear={clearPreview}
        isDisabled={isLoading}
        className="mb-8"
      />

      <Button
        variant="outline"
        size="sm"
        onClick={refresh}
        className="self-start"
        leftIcon={<Icon name="refresh-cw-icon" size="sm" aria-hidden />}
      >
        Actualiser les informations
      </Button>
    </>
  )
}
