import { useCallback, useEffect, useState } from 'react'
import { tokenizerApi } from '@/services/tokenizerApi'
import type {
  TokenPreview,
  TokenizerDashboardState,
  TokenizerJob,
  TokenizerVocabInfo,
} from '@/types/tokenizer'

const POLL_INTERVAL_MS = 2000
const DEFAULT_VOCAB_SIZE = 32_000
const DEFAULT_MIN_FREQUENCY = 2
const DEFAULT_CORPUS_SAMPLE_SIZE = 20_000
const DEFAULT_NUM_THREADS = 4
const DEFAULT_SHARD_SIZE_TOKENS = 5_000_000

function toMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : 'Erreur inattendue'
}

function isActiveJob(job: TokenizerJob | null): boolean {
  return job?.status === 'pending' || job?.status === 'running'
}

export function useTokenizerDashboard(): TokenizerDashboardState {
  const [info, setInfo] = useState<TokenizerVocabInfo | null>(null)
  const [job, setJob] = useState<TokenizerJob | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [vocabSize, setVocabSize] = useState(DEFAULT_VOCAB_SIZE)
  const [minFrequency, setMinFrequency] = useState(DEFAULT_MIN_FREQUENCY)
  const [corpusSampleSize, setCorpusSampleSize] = useState(DEFAULT_CORPUS_SAMPLE_SIZE)
  const [numThreads, setNumThreads] = useState(DEFAULT_NUM_THREADS)
  const [trainLanguages, setTrainLanguages] = useState<string[]>(['fr'])

  const [shardSizeTokens, setShardSizeTokens] = useState(DEFAULT_SHARD_SIZE_TOKENS)
  const [encodeLanguages, setEncodeLanguages] = useState<string[]>([])

  const [preview, setPreview] = useState<TokenPreview | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)

  const loadInfo = useCallback(async () => {
    try {
      setInfo(await tokenizerApi.getInfo())
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const timer = window.setTimeout(() => {
      void (async () => {
        await loadInfo()
        if (!cancelled) setIsLoading(false)
      })()
    }, 0)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [loadInfo])

  useEffect(() => {
    if (!job || !isActiveJob(job)) return
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const nextJob = await tokenizerApi.getJobStatus(job.id)
          setJob(nextJob)
          if (nextJob.status === 'completed') {
            void loadInfo()
          }
        } catch (cause) {
          setError(toMessage(cause))
        }
      })()
    }, POLL_INTERVAL_MS)
    return () => window.clearTimeout(timer)
  }, [job, loadInfo])

  const train = useCallback(async () => {
    if (trainLanguages.length === 0) {
      setError('Selectionnez au moins une langue pour entrainer le tokenizer.')
      return
    }
    setIsSubmitting(true)
    setError(null)
    try {
      setJob(
        await tokenizerApi.train({
          vocabSize,
          minFrequency,
          corpusSampleSize,
          numThreads,
          languages: trainLanguages,
        }),
      )
    } catch (cause) {
      setError(toMessage(cause))
    } finally {
      setIsSubmitting(false)
    }
  }, [vocabSize, minFrequency, corpusSampleSize, numThreads, trainLanguages])

  const encode = useCallback(async () => {
    if (!info) {
      setError("Entrainez d'abord un tokenizer avant d'encoder le corpus.")
      return
    }
    setIsSubmitting(true)
    setError(null)
    try {
      setJob(
        await tokenizerApi.encode({
          shardSizeTokens,
          languages: encodeLanguages.length > 0 ? encodeLanguages : null,
        }),
      )
    } catch (cause) {
      setError(toMessage(cause))
    } finally {
      setIsSubmitting(false)
    }
  }, [info, shardSizeTokens, encodeLanguages])

  const runPreview = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) {
        setPreviewError('Saisissez un texte a tokenizer.')
        return
      }
      if (!info) {
        setPreviewError("Aucun tokenizer entraine n'est disponible.")
        return
      }
      setIsPreviewing(true)
      setPreviewError(null)
      try {
        setPreview(await tokenizerApi.preview(trimmed))
      } catch (cause) {
        setPreviewError(toMessage(cause))
      } finally {
        setIsPreviewing(false)
      }
    },
    [info],
  )

  const clearPreview = useCallback(() => {
    setPreview(null)
    setPreviewError(null)
  }, [])

  const clearError = useCallback(() => setError(null), [])

  const dismissJob = useCallback(() => setJob(null), [])

  const refresh = useCallback(() => {
    setError(null)
    void loadInfo()
  }, [loadInfo])

  return {
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
  }
}
