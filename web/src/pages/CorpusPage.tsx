import { DashboardTemplate } from '@/components/templates/DashboardTemplate'
import { CardGrid } from '@/components/organisms/CardGrid'
import { ScrapePanel } from '@/components/organisms/ScrapePanel'
import { JobMonitor } from '@/components/organisms/JobMonitor'
import { Alert } from '@/components/molecules/Alert'
import { Icon } from '@/components/atoms/Icon'
import { useCorpusDashboard } from '@/hooks/useCorpusDashboard'

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
    refresh,
    clearError,
  } = useCorpusDashboard()

  const handleStartScrape = () => {
    clearError()
    void startScrape()
  }

  const handleResumeScrape = () => {
    clearError()
    void resumeScrape()
  }

  const selectedSourceLabels = selectedSources
    .map((id) => sources.find((s) => s.id === id)?.label)
    .filter(Boolean)
    .join(', ')

  return (
    <DashboardTemplate
      refresh={refresh}
      header={{
        eyebrow: 'Corpus',
        title: 'Tableau de bord Corpus',
        subtitle: 'Gerez vos jeux de donnees et lancez de nouveaux scrapings.',
        actions: [
          {
            label: 'Actualiser',
            variant: 'outline',
            onClick: refresh,
            leftIcon: <Icon name="refresh-cw-icon" size="sm" aria-hidden />,
          },
        ],
      }}
    >
      {error && (
        <Alert
          variant="error"
          title="Erreur"
          message={error}
          onDismiss={clearError}
          className="mb-6"
        />
      )}

      {job && (
        <JobMonitor
          job={job}
          onResume={job.status === 'failed' ? handleResumeScrape : undefined}
          onDismiss={() => {}}
          className="mb-6"
        />
      )}

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
        isStarting={job?.status === 'pending' || job?.status === 'running'}
        isDisabled={isLoading || (job?.status === 'pending' || job?.status === 'running')}
      />

      <CardGrid
        items={datasets}
        className="mt-6"
        emptyTitle={isLoading ? 'Chargement...' : 'Aucun corpus disponible'}
        emptyDescription={isLoading
          ? 'Veuillez patienter pendant le chargement des donnees.'
          : 'Lancez un scraping pour creer votre premier corpus. Les fichiers .md seront generes dans le dossier data/corpus/markdown/.'}
        emptyAction={{
          label: selectedSourceLabels
            ? `Demarrer le scraping (${selectedSourceLabels})`
            : 'Selectionnez une source',
          onClick: handleStartScrape,
        }}
      />
    </DashboardTemplate>
  )
}