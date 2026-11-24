import { CardGrid } from '@/components/organisms/CardGrid'
import { ScrapePanel } from '@/components/organisms/ScrapePanel'
import { JobMonitor } from '@/components/organisms/JobMonitor'
import { CorpusTable } from '@/components/organisms/CorpusTable'
import { Alert } from '@/components/molecules/Alert'
import { StatCard } from '@/components/molecules/StatCard'
import { useCorpusDashboard } from '@/hooks/useCorpusDashboard'
import type { CorpusFileInfo } from '@/components/organisms/CorpusTable'
import { useState } from 'react'
import { formatNumber, formatBytes } from '@/utils/format'
import { Icon } from '@/components/atoms/Icon'
import { Box } from '@/components/atoms/Box'
import { Button } from '@/components/atoms/Button'
import type { JobConfigField } from '@/types/job'

const CORPUS_PROGRESS_LABELS: Record<string, string> = {
  documentsScraped: 'Documents scrapes',
  documentsCleaned: 'Documents nettoyes',
  documentsFiltered: 'Documents filtres',
  documentsDeduplicated: 'Documents dedupliques',
  documentsExported: 'Documents exportes (MD)',
  shardsWritten: 'Shards ecrits',
  totalTokens: 'Total tokens',
}

const CORPUS_CONFIG_FIELDS: JobConfigField[] = [
  { key: 'sources', label: 'Sources', icon: 'database-icon' },
  { key: 'languages', label: 'Langues', icon: 'globe-icon' },
  { key: 'maxArticlesPerLang', label: 'Max/doc', icon: 'file-text-icon' },
]

export function CorpusPage() {
  const {
    datasets,
    sources,
    job,
    isLoading,
    error,
    selectedSources,
    setSelectedSources,
    language,
    setLanguage,
    maxDocuments,
    setMaxDocuments,
    availableLanguages,
    startScrape,
    resumeScrape,
    clearError,
    refresh,
  } = useCorpusDashboard()

  const [tablePage, setTablePage] = useState(1)
  const TABLE_PAGE_SIZE = 10

  const handleStartScrape = () => {
    clearError()
    void startScrape()
  }

  const handleResumeScrape = () => {
    clearError()
    void resumeScrape()
  }

  // KPI aggregates
  const totalDocuments = datasets.reduce((sum, d) => sum + d.documentCount, 0)
  const totalSize = datasets.reduce((sum, d) => sum + d.totalSizeBytes, 0)
  const activeJob = job?.status === 'pending' || job?.status === 'running'

  const selectedSourceLabels = selectedSources
    .map((id) => sources.find((s) => s.id === id)?.label)
    .filter(Boolean)
    .join(', ')

  // Build file list from datasets for the tableau
  const corpusFiles: CorpusFileInfo[] = datasets.flatMap((dataset) =>
    Array.from({ length: Math.min(dataset.documentCount, 50) }, (_, i) => ({
      id: `${dataset.source}-${i}`,
      filename: `document_${i + 1}.md`,
      source: dataset.source,
      language: dataset.languages[i % dataset.languages.length],
      sizeBytes: Math.floor(dataset.totalSizeBytes / Math.max(dataset.documentCount, 1)),
      updatedAt: dataset.updatedAt,
    }))
  )

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
          title={datasets.length > 0 ? 'source(s) active(s)' : 'Aucune donnee'}
          value={datasets.length.toString()}
          badge={{
            variant: datasets.length > 0 ? 'success' : 'muted',
            label: datasets.length > 0 ? 'Actif' : 'Vide',
          }}
          trend={{
            value: totalDocuments > 0 ? `${formatNumber(totalDocuments)} documents` : '-',
            isPositive: true,
          }}
        />
        <StatCard
          title="Stockes sous data/corpus/markdown/"
          value={formatBytes(totalSize)}
          badge={{ variant: 'default', label: 'Fichiers .md' }}
        />
        <StatCard
          title="Sources de scraping"
          value={sources.length.toString()}
          badge={{
            variant: sources.length > 0 ? 'accent' : 'muted',
            label: sources.length > 0 ? 'Configures' : 'Aucune',
          }}
        />
        <StatCard
          title={`Travaux ${job ? `Statut: ${job.status}` : 'Aucun travail'}`}
          value={job ? '1' : '0'}
          badge={{
            variant: activeJob ? 'accent' : job?.status === 'failed' ? 'error' : 'success',
            label: activeJob
              ? 'En cours'
              : job?.status === 'failed'
              ? 'Echec'
              : 'Inactif',
          }}
        />
      </Box>

      {/* Job Monitor - operational status with freshness */}
      {job && (
        <JobMonitor
          job={job}
          title="Job de scraping"
          progressLabels={CORPUS_PROGRESS_LABELS}
          configFields={CORPUS_CONFIG_FIELDS}
          onResume={job.status === 'failed' ? handleResumeScrape : undefined}
          onDismiss={() => {}}
          className="mb-8"
        />
      )}

      {/* Scrape Panel - primary action zone */}
      <Box className="mb-8">
        <ScrapePanel
          sources={sources}
          selectedSources={selectedSources}
          onSourcesChange={setSelectedSources}
          language={language}
          availableLanguages={availableLanguages}
          onLanguageChange={setLanguage}
          maxDocuments={maxDocuments}
          onMaxDocumentsChange={setMaxDocuments}
          onStart={handleStartScrape}
          isStarting={activeJob}
          isDisabled={isLoading || activeJob}
        />
      </Box>

      {/* Corpus Table - exact lookup with pagination */}
      <Box className="mb-8">
        <CorpusTable
          files={corpusFiles}
          dataset={datasets[0]}
          onFileClick={(file) => alert(`Ouvert: ${file.filename}`)}
          page={tablePage}
          pageSize={TABLE_PAGE_SIZE}
          onPageChange={setTablePage}
        />
      </Box>

      {/* Corpus Grid - visual summary of all sources */}
      <CardGrid
        items={datasets}
        emptyTitle={isLoading ? 'Chargement...' : 'Aucun corpus disponible'}
        emptyDescription={
          isLoading
            ? 'Veuillez patienter pendant le chargement des donnees.'
            : 'Lancez un scraping pour creer votre premier corpus. Les fichiers .md seront generes dans le dossier data/corpus/markdown/.'
        }
        emptyAction={{
          label: selectedSourceLabels
            ? `Demarrer le scraping (${selectedSourceLabels})`
            : 'Selectionnez une source',
          onClick: handleStartScrape,
        }}
      />

      <Button
        variant="outline"
        size="sm"
        onClick={() => void refresh()}
        className="mt-6 self-start"
        leftIcon={<Icon name="refresh-cw-icon" size="sm" aria-hidden />}
      >
        Actualiser les donnees
      </Button>
    </>
  )
}