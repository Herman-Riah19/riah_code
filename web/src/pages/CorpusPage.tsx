import { useState } from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Icon } from '@/components/atoms/Icon'
import { Button } from '@/components/atoms/Button'
import { Alert } from '@/components/molecules/Alert'
import { StatCard } from '@/components/molecules/StatCard'
import { TabBar, type TabBarItem } from '@/components/molecules/TabBar'
import { JobMonitor } from '@/components/organisms/JobMonitor'
import { ScrapePanel } from '@/components/organisms/ScrapePanel'
import { CorpusTable } from '@/components/organisms/CorpusTable'
import { CardGrid } from '@/components/organisms/CardGrid'
import { useCorpusDashboard } from '@/hooks/useCorpusDashboard'
import type { CorpusFileInfo } from '@/components/organisms/CorpusTable'
import { formatNumber, formatBytes } from '@/utils/format'
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

type TabId = 'apercu' | 'tableau' | 'datasets'

const TAB_ITEMS: TabBarItem<TabId>[] = [
  { id: 'apercu', label: 'Aperçu', icon: 'dashboard-icon' },
  { id: 'tableau', label: 'Tableau', icon: 'file-text-icon' },
  { id: 'datasets', label: 'Sources', icon: 'database-icon' },
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

  const [activeTab, setActiveTab] = useState<TabId>('apercu')

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

      {/* KPI Overview - always visible at the top */}
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
          subtitle="Stockees sous data/corpus/markdown/"
          badge={{ variant: 'default', label: 'Fichiers .md' }}
        />
        <StatCard
          title="Sources"
          value={sources.length.toString()}
          subtitle="Disponibles pour le scraping"
          badge={{
            variant: sources.length > 0 ? 'accent' : 'muted',
            label: sources.length > 0 ? 'Configurees' : 'Aucune',
          }}
        />
        <StatCard
          title="Travaux"
          value={job ? '1' : '0'}
          subtitle={job ? `Statut: ${job.status}` : 'Aucun travail'}
          badge={{
            variant: activeJob
              ? 'accent'
              : job?.status === 'failed'
              ? 'error'
              : job?.status === 'completed'
              ? 'success'
              : 'muted',
            label: activeJob
              ? 'En cours'
              : job?.status === 'failed'
              ? 'Echec'
              : job?.status === 'completed'
              ? 'Termine'
              : 'Inactif',
          }}
        />
      </Box>

      {/* Tab navigation */}
      <TabBar
        items={TAB_ITEMS}
        activeId={activeTab}
        onChange={setActiveTab}
        className="mb-6"
      />

      {activeTab === 'apercu' && (
        <Stack spacing="md">
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
        </Stack>
      )}

      {activeTab === 'tableau' && (
        <CorpusTable
          files={corpusFiles}
          dataset={datasets[0]}
          onFileClick={(file) => alert(`Ouvert: ${file.filename}`)}
        />
      )}

      {activeTab === 'datasets' && (
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
      )}

      <Button
        variant="outline"
        size="sm"
        onClick={refresh}
        className="self-start"
        leftIcon={<Icon name="refresh-cw-icon" size="sm" aria-hidden />}
      >
        Actualiser les donnees
      </Button>
    </>
  )
}
