export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface CorpusDataset {
  source: string
  languages: string[]
  documentCount: number
  totalSizeBytes: number
  updatedAt: string
  path: string
}

export interface ScrapeSource {
  id: string
  label: string
  description: string
  languages: string[]
}

export interface PipelineProgress {
  documentsScraped?: number
  documentsCleaned?: number
  documentsFiltered?: number
  documentsDeduplicated?: number
  documentsExported?: number
  shardsWritten?: number
  totalTokens?: number
}

export interface CorpusJob {
  id: string
  jobType: string
  status: JobStatus
  config: Record<string, unknown>
  userId: string | null
  createdAt: string
  startedAt: string | null
  finishedAt: string | null
  progress: PipelineProgress
  error: string | null
}

export interface StartPipelinePayload {
  sources: string[]
  languages: string[]
  maxArticlesPerLang: number
}

export interface CorpusDashboardState {
  datasets: CorpusDataset[]
  sources: ScrapeSource[]
  job: CorpusJob | null
  isLoading: boolean
  isStarting: boolean
  error: string | null
  selectedSources: string[]
  language: string
  maxDocuments: number
  availableLanguages: string[]
  setSelectedSources: (sources: string[]) => void
  setLanguage: (language: string) => void
  setMaxDocuments: (value: number) => void
  refresh: () => void
  clearError: () => void
  startScrape: () => Promise<void>
  resumeScrape: () => Promise<void>
}
