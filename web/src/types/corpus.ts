import type { MonitorableJob } from './job'

export type { JobStatus } from './job'

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

export interface CorpusJob extends MonitorableJob {
  progress: PipelineProgress
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
