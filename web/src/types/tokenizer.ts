import type { MonitorableJob } from './job'

/** Metadata persisted in `vocab_info.json` by the backend. */
export interface TokenizerVocabInfo {
  vocabSize: number
  specialTokenIds: Record<string, number>
  compressionRatio: number
  oovRate: number
  trainedAt: string
  configHash: string
}

export interface TokenizerTrainingProgress {
  vocabSize?: number
  compressionRatio?: number
  oovRate?: number
  trainedAt?: string
  configHash?: string
  specialTokenIds?: Record<string, number>
}

export interface CorpusEncodingProgress {
  totalTokens?: number
  totalDocuments?: number
  shardCount?: number
  avgTokensPerDoc?: number
  durationSeconds?: number
  languageDistribution?: Record<string, number>
}

export type TokenizerJobProgress = TokenizerTrainingProgress | CorpusEncodingProgress

export interface TokenizerJob extends MonitorableJob {
  progress: TokenizerJobProgress
}

export interface TrainTokenizerPayload {
  vocabSize: number
  minFrequency: number
  corpusSampleSize: number
  languages: string[]
  numThreads: number
}

export interface EncodeCorpusPayload {
  tokenizerPath?: string | null
  shardSizeTokens: number
  languages?: string[] | null
}

/** Result of the token preview playground. */
export interface TokenPreview {
  text: string
  tokenCount: number
  characterCount: number
  compressionRatio: number
  tokens: string[]
  tokenIds: number[]
  decoded: string
}

/** One vocabulary entry returned by the backend `/api/tokenizer/vocab`. */
export interface TokenizerVocabEntry {
  token: string
  tokenId: number
}

/** One token entry in the token explorer table. */
export interface TokenizerTokenEntry {
  token: string
  tokenId: number
  source: string
  language: string
  frequency: number
  firstSeen: string
}

export interface TokenizerDashboardState {
  info: TokenizerVocabInfo | null
  job: TokenizerJob | null
  isLoading: boolean
  isSubmitting: boolean
  error: string | null
  // Training form
  vocabSize: number
  minFrequency: number
  corpusSampleSize: number
  numThreads: number
  trainLanguages: string[]
  setVocabSize: (value: number) => void
  setMinFrequency: (value: number) => void
  setCorpusSampleSize: (value: number) => void
  setNumThreads: (value: number) => void
  setTrainLanguages: (languages: string[]) => void
  // Encoding form
  shardSizeTokens: number
  encodeLanguages: string[]
  setShardSizeTokens: (value: number) => void
  setEncodeLanguages: (languages: string[]) => void
  // Preview
  preview: TokenPreview | null
  isPreviewing: boolean
  previewError: string | null
  // Actions
  train: () => Promise<void>
  encode: () => Promise<void>
  runPreview: (text: string) => Promise<void>
  clearPreview: () => void
  clearError: () => void
  dismissJob: () => void
  refresh: () => void
}
