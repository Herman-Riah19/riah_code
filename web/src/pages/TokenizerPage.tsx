import { useState } from 'react'
import { Box } from '@/components/atoms/Box'
import { Icon } from '@/components/atoms/Icon'
import { Button } from '@/components/atoms/Button'
import { Alert } from '@/components/molecules/Alert'
import { StatCard } from '@/components/molecules/StatCard'
import { TabBar, type TabBarItem } from '@/components/molecules/TabBar'
import { JobMonitor } from '@/components/organisms/JobMonitor'
import { TokenizerInfoPanel } from '@/components/organisms/TokenizerInfoPanel'
import { TokenizerTrainPanel } from '@/components/organisms/TokenizerTrainPanel'
import { TokenizerEncodePanel } from '@/components/organisms/TokenizerEncodePanel'
import { TokenizerPreviewPanel } from '@/components/organisms/TokenizerPreviewPanel'
import { TokenizerTokensTable } from '@/components/organisms/TokenizerTokensTable'
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

type TabId = 'preview' | 'info' | 'train' | 'encode' | 'tokens'

const TAB_ITEMS: TabBarItem<TabId>[] = [
  { id: 'preview', label: 'Previsualisation', icon: 'search-icon' },
  { id: 'info', label: 'Informations', icon: 'info-icon' },
  { id: 'train', label: 'Entrainement', icon: 'sparkles-icon' },
  { id: 'encode', label: 'Encodage', icon: 'hard-drive-icon' },
  { id: 'tokens', label: 'Tokens', icon: 'hash-icon' },
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

  const [activeTab, setActiveTab] = useState<TabId>('preview')

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

      {/* KPI Overview - always visible at the top */}
      <Box className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard
          title="Vocabulaire"
          value={info ? formatNumber(info.vocabSize) : '-'}
          subtitle="Tokens appris par le BPE"
          badge={{
            variant: info ? 'success' : 'muted',
            label: info ? 'Pret' : 'Vide',
          }}
        />
        <StatCard
          title="Compression"
          value={info ? info.compressionRatio.toFixed(2) : '-'}
          subtitle="Caracteres par token"
          badge={{
            variant: info ? 'accent' : 'muted',
            label: info ? 'BPE byte-level' : 'Indisponible',
          }}
        />
        <StatCard
          title="Taux OOV"
          value={info ? `${(info.oovRate * 100).toFixed(2)} %` : '-'}
          subtitle="Tokens inconnus a l encodage"
          badge={{
            variant: info ? (info.oovRate > 0 ? 'warning' : 'success') : 'muted',
            label: info ? (info.oovRate > 0 ? 'A surveiller' : 'Aucun') : 'Indisponible',
          }}
        />
        <StatCard
          title="Travaux"
          value={job ? '1' : '0'}
          subtitle={job ? `Statut: ${job.status}` : 'Aucun travail'}
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

      {/* Job Monitor - operational status */}
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

      {/* Tab navigation - Preview first (was at the bottom), then Info, Train, Encode, Tokens */}
      <TabBar
        items={TAB_ITEMS}
        activeId={activeTab}
        onChange={setActiveTab}
        className="mb-6"
      />

      {activeTab === 'preview' && (
        <TokenizerPreviewPanel
          preview={preview}
          isPreviewing={isPreviewing}
          error={previewError}
          onPreview={(text) => void runPreview(text)}
          onClear={clearPreview}
          isDisabled={isLoading}
          className="mb-8"
        />
      )}

      {activeTab === 'info' && (
        <TokenizerInfoPanel info={info} isLoading={isLoading} className="mb-8" />
      )}

      {activeTab === 'train' && (
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
      )}

      {activeTab === 'encode' && (
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
      )}

      {activeTab === 'tokens' && (
        <TokenizerTokensTable className="mb-8" />
      )}

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
