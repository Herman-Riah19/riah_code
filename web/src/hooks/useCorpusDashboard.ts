import { useCallback, useEffect, useMemo, useState } from 'react'
import { corpusApi } from '@/services/corpusApi'
import type {
  CorpusDashboardState,
  CorpusDataset,
  CorpusJob,
  ScrapeSource,
} from '@/types/corpus'

const POLL_INTERVAL_MS = 2000
const DEFAULT_MAX_DOCUMENTS = 200

function toMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : 'Erreur inattendue'
}

function isActiveJob(job: CorpusJob | null): boolean {
  return job?.status === 'pending' || job?.status === 'running'
}

export function useCorpusDashboard(): CorpusDashboardState {
  const [datasets, setDatasets] = useState<CorpusDataset[]>([])
  const [sources, setSources] = useState<ScrapeSource[]>([])
  const [job, setJob] = useState<CorpusJob | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedSources, setSelectedSources] = useState<string[]>(['wikipedia'])
  const [language, setLanguage] = useState('fr')
  const [maxDocuments, setMaxDocuments] = useState(DEFAULT_MAX_DOCUMENTS)

  const loadDatasets = useCallback(async () => {
    try {
      setDatasets(await corpusApi.listDatasets())
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [])

  const loadAll = useCallback(async () => {
    setIsLoading(true)
    try {
      const [nextSources, nextDatasets] = await Promise.all([
        corpusApi.listSources(),
        corpusApi.listDatasets(),
      ])
      setSources(nextSources)
      setDatasets(nextDatasets)
      setSelectedSources((current) => {
        const available = nextSources.map((source) => source.id)
        const kept = current.filter((sourceId) => available.includes(sourceId))
        return kept.length > 0 ? kept : available.slice(0, 1)
      })
      const allLanguages = [
        ...new Set(nextSources.flatMap((source) => source.languages)),
      ]
      if (
        allLanguages.length > 0 &&
        !allLanguages.includes(language)
      ) {
        setLanguage(allLanguages[0])
      }
    } catch (cause) {
      setError(toMessage(cause))
    } finally {
      setIsLoading(false)
    }
  }, [language])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadAll()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadAll])

  const availableLanguages = useMemo(() => {
    const seen = new Set<string>()
    const languages: string[] = []
    for (const source of sources) {
      if (!selectedSources.includes(source.id)) continue
      for (const item of source.languages) {
        if (seen.has(item)) continue
        seen.add(item)
        languages.push(item)
      }
    }
    return languages
  }, [sources, selectedSources])

  useEffect(() => {
    if (!job || !isActiveJob(job)) return
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const nextJob = await corpusApi.getJobStatus(job.id)
          setJob(nextJob)
          if (nextJob.status === 'completed') {
            void loadDatasets()
          }
        } catch (cause) {
          setError(toMessage(cause))
        }
      })()
    }, POLL_INTERVAL_MS)
    return () => window.clearTimeout(timer)
  }, [job, loadDatasets])

  const startScrape = useCallback(async () => {
    if (selectedSources.length === 0) {
      setError('Selectionnez au moins une source.')
      return
    }
    setIsStarting(true)
    setError(null)
    try {
      const created = await corpusApi.startPipeline({
        sources: selectedSources,
        languages: [language],
        maxArticlesPerLang: Math.max(1, Math.round(maxDocuments)),
      })
      setJob(created)
    } catch (cause) {
      setError(toMessage(cause))
    } finally {
      setIsStarting(false)
    }
  }, [selectedSources, language, maxDocuments])

  const resumeScrape = useCallback(async () => {
    if (!job) return
    setError(null)
    try {
      setJob(await corpusApi.resumePipeline(job.id))
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [job])

  const refresh = useCallback(() => {
    setError(null)
    void loadDatasets()
  }, [loadDatasets])

  const clearError = useCallback(() => setError(null), [])

  return {
    datasets,
    sources,
    job,
    isLoading,
    isStarting,
    error,
    selectedSources,
    language,
    maxDocuments,
    availableLanguages,
    setSelectedSources,
    setLanguage,
    setMaxDocuments,
    refresh,
    clearError,
    startScrape,
    resumeScrape,
  }
}
