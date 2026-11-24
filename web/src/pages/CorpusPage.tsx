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
          title="Corpus totaux"
          value={datasets.length.toString()}
          subtitle={datasets.length > 0 ? 'source(s) active(s)' : 'Aucune donnee'}
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
          title="Taille totale"
          value={formatBytes(totalSize)}
          subtitle="Stockes sous data/corpus/markdown/"
          badge={{ variant: 'default', label: 'Fichiers .md' }}
        />
        <StatCard
          title="Sources"
          value={sources.length.toString()}
          subtitle="Disponibles pour le scraping"
          badge={{
            variant: sources.length > 0 ? 'accent' : 'muted',
            label: sources.length > 0 ? 'Configures' : 'Aucune',
          }}
        />
        <StatCard
          title="Travaux"
          value={job ? '1' : '0'}
          subtitle={job ? `Statut: ${job.status}` : 'Aucun travail'}
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