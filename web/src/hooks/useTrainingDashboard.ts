import { useCallback, useEffect, useRef, useState } from 'react'
import { trainingApi, createTrainingStream } from '@/services/trainingApi'
import type {
  CheckpointInfo,
  GenerationOutput,
  ModelPreset,
  TrainResumePayload,
  TrainStartPayload,
  TrainingDashboardState,
  TrainingHistoryEntry,
  TrainingJob,
  TrainingProgress,
} from '@/types/training'

const POLL_INTERVAL_MS = 2000
const DEFAULT_PRESET = '125M'
const DEFAULT_BATCH_SIZE = 8
const DEFAULT_SEQ_LEN = 512
const DEFAULT_MAX_STEPS = 100_000
const DEFAULT_LR = 3e-4
const DEFAULT_WARMUP_STEPS = 2000
const DEFAULT_EVAL_INTERVAL = 1000
const DEFAULT_CHECKPOINT_INTERVAL = 5000
const DEFAULT_DTYPE = 'bf16' as const
const DEFAULT_DECAY_STEPS = 100_000
const DEFAULT_EVAL_STEPS = 100

function toMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : 'Erreur inattendue'
}

function isActiveJob(job: TrainingJob | null): boolean {
  return job?.status === 'pending' || job?.status === 'running'
}

function presetToConfig(preset: string): { batchSize: number; seqLen: number; maxSteps: number; dtype: 'fp32' | 'fp16' | 'bf16' } {
  switch (preset) {
    case 'tiny':
      return { batchSize: 16, seqLen: 128, maxSteps: 10_000, dtype: 'fp32' }
    case '125M':
      return { batchSize: 8, seqLen: 512, maxSteps: 100_000, dtype: 'bf16' }
    case '350M':
      return { batchSize: 4, seqLen: 1024, maxSteps: 200_000, dtype: 'bf16' }
    case '760M':
      return { batchSize: 2, seqLen: 2048, maxSteps: 500_000, dtype: 'bf16' }
    case '1.3B':
      return { batchSize: 1, seqLen: 2048, maxSteps: 1_000_000, dtype: 'bf16' }
    default:
      return { batchSize: DEFAULT_BATCH_SIZE, seqLen: DEFAULT_SEQ_LEN, maxSteps: DEFAULT_MAX_STEPS, dtype: DEFAULT_DTYPE }
  }
}

export function useTrainingDashboard() {
  const [jobs, setJobs] = useState<TrainingJob[]>([])
  const [activeJob, setActiveJob] = useState<TrainingJob | null>(null)
  const [history, setHistory] = useState<TrainingHistoryEntry[]>([])
  const [checkpoints, setCheckpoints] = useState<CheckpointInfo[]>([])
  const [presets, setPresets] = useState<ModelPreset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [preset, setPreset] = useState(DEFAULT_PRESET)
  const [modelName, setModelName] = useState('default')
  const [batchSize, setBatchSize] = useState(DEFAULT_BATCH_SIZE)
  const [seqLen, setSeqLen] = useState(DEFAULT_SEQ_LEN)
  const [maxSteps, setMaxSteps] = useState(DEFAULT_MAX_STEPS)
  const [lr, setLr] = useState(DEFAULT_LR)
  const [warmupSteps, setWarmupSteps] = useState(DEFAULT_WARMUP_STEPS)
  const [evalInterval, setEvalInterval] = useState(DEFAULT_EVAL_INTERVAL)
  const [checkpointInterval, setCheckpointInterval] = useState(DEFAULT_CHECKPOINT_INTERVAL)
  const [dtype, setDtype] = useState<TrainingDashboardState['dtype']>(DEFAULT_DTYPE)

  // Evaluation
  const [evalPrompt, setEvalPrompt] = useState('Qu\'est-ce que l\'intelligence artificielle ?')
  const [evalResult, setEvalResult] = useState<GenerationOutput | null>(null)
  const [isEvaluating, setIsEvaluating] = useState(false)

  // SSE stream ref
  const streamRef = useRef<ReturnType<typeof createTrainingStream> | null>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)

  const clearError = useCallback(() => setError(null), [])

  const setFormField = useCallback(<K extends keyof TrainingDashboardState>(key: K, value: TrainingDashboardState[K]) => {
    switch (key) {
      case 'preset': {
        const selectedPreset = value as string
        const config = presetToConfig(selectedPreset)
        setPreset(selectedPreset)
        setBatchSize(config.batchSize)
        setSeqLen(config.seqLen)
        setMaxSteps(config.maxSteps)
        setDtype(config.dtype)
        break
      }
      case 'modelName': setModelName(value as string); break
      case 'batchSize': setBatchSize(value as number); break
      case 'seqLen': setSeqLen(value as number); break
      case 'maxSteps': setMaxSteps(value as number); break
      case 'lr': setLr(value as number); break
      case 'warmupSteps': setWarmupSteps(value as number); break
      case 'evalInterval': setEvalInterval(value as number); break
      case 'checkpointInterval': setCheckpointInterval(value as number); break
      case 'dtype': setDtype(value as 'fp32' | 'fp16' | 'bf16'); break
      case 'evalPrompt': setEvalPrompt(value as string); break
      default:
        // For other fields, we'll handle them individually
        break
    }
  }, [])

  const loadPresets = useCallback(async () => {
    try {
      setPresets(await trainingApi.listPresets())
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [])

  const loadJobs = useCallback(async () => {
    try {
      const jobsList = await trainingApi.listJobs()
      setJobs(jobsList)
      // Auto-select first active job
      const active = jobsList.find(isActiveJob)
      if (active && (!activeJob || activeJob.id !== active.id)) {
        setActiveJob(active)
      }
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [activeJob])

  const loadCheckpoints = useCallback(async () => {
    try {
      const ckpts = await trainingApi.listCheckpoints()
      setCheckpoints(ckpts)
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [])

  const selectJob = useCallback((job: TrainingJob) => {
    setActiveJob(job)
  }, [])

  const dismissJob = useCallback(() => {
    setActiveJob(null)
    setHistory([])
    // Stop any active stream
    if (streamRef.current) {
      streamRef.current.stop()
      streamRef.current = null
    }
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }
    setIsStreaming(false)
  }, [])

  const loadHistory = useCallback(async (jobId: string) => {
    try {
      const hist = await trainingApi.getHistory(jobId)
      setHistory(hist)
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [])

  const startStreaming = useCallback((jobId: string) => {
    if (streamRef.current) {
      streamRef.current.stop()
    }
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
    }

    const stream = createTrainingStream(jobId)
    streamRef.current = stream

    unsubscribeRef.current = stream.subscribe((data) => {
      if (data && typeof data === 'object' && 'disconnected' in data) {
        setIsStreaming(false)
        return
      }
      setIsStreaming(true)
      // Update active job progress in real-time
      setActiveJob((prev) => {
        if (!prev || prev.id !== jobId) return prev
        return { ...prev, progress: data as TrainingProgress }
      })
      // Also update jobs list
      setJobs((prev) => prev.map((j) => (j.id === jobId ? { ...j, progress: data as TrainingJob['progress'] } : j)))
    })

    stream.start()
  }, [])

  const stopStreaming = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.stop()
      streamRef.current = null
    }
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }
    setIsStreaming(false)
  }, [])

  // Auto-refresh active job and start/stop streaming
  useEffect(() => {
    if (!activeJob || !isActiveJob(activeJob)) {
      return
    }

    // Start SSE stream
    startStreaming(activeJob.id)

    // Also poll as fallback
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const nextJob = await trainingApi.getJob(activeJob.id)
          setActiveJob(nextJob)
          setJobs((prev) => prev.map((j) => (j.id === nextJob.id ? nextJob : j)))
          if (nextJob.status === 'completed' || nextJob.status === 'failed' || nextJob.status === 'cancelled') {
            stopStreaming()
            void loadHistory(nextJob.id)
            void loadJobs()
            void loadCheckpoints()
          }
        } catch (cause) {
          setError(toMessage(cause))
        }
      })()
    }, POLL_INTERVAL_MS)

    return () => {
      window.clearTimeout(timer)
      stopStreaming()
    }
  }, [activeJob, loadHistory, loadJobs, loadCheckpoints, startStreaming, stopStreaming])

  const startTraining = useCallback(async () => {
    setIsSubmitting(true)
    setError(null)
    try {
      const payload: TrainStartPayload = {
        preset,
        modelName,
        batchSize,
        seqLen,
        maxSteps,
        lr,
        warmupSteps,
        evalInterval,
        checkpointInterval,
        dtype,
        numWorkers: 0,
        microBatchSize: undefined,
        trainShards: undefined,
        valShards: undefined,
        optimizer: 'adamw',
        minLr: lr * 0.1,
        weightDecay: 0.1,
        beta1: 0.9,
        beta2: 0.95,
        eps: 1e-8,
        gradClip: 1.0,
        scheduler: 'cosine_warmup',
        maxEpochs: undefined,
        gradientAccumulationSteps: 1,
        logInterval: 10,
        keepLastNCheckpoints: 3,
        saveOptimizer: true,
        saveRng: true,
        useGradScaler: true,
        compileModel: false,
        tensorboard: false,
        labelSmoothing: 0,
        seed: 42,
        decaySteps: DEFAULT_DECAY_STEPS,
        evalSteps: DEFAULT_EVAL_STEPS,
      }

      const job = await trainingApi.startTraining(payload)
      setJobs((prev) => [job, ...prev])
      setActiveJob(job)
    } catch (cause) {
      setError(toMessage(cause))
    } finally {
      setIsSubmitting(false)
    }
  }, [preset, modelName, batchSize, seqLen, maxSteps, lr, warmupSteps, evalInterval, checkpointInterval, dtype])

  const cancelJob = useCallback(async (jobId: string) => {
    try {
      const updated = await trainingApi.cancelJob(jobId)
      setJobs((prev) => prev.map((j) => (j.id === jobId ? updated : j)))
      if (activeJob?.id === jobId) {
        setActiveJob(updated)
        stopStreaming()
      }
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [activeJob, stopStreaming])

  const resumeJob = useCallback(async (jobId: string, payload?: TrainResumePayload) => {
    try {
      const updated = await trainingApi.resumeTraining(jobId, payload ?? {})
      setJobs((prev) => [updated, ...prev.filter((j) => j.id !== jobId)])
      setActiveJob(updated)
    } catch (cause) {
      setError(toMessage(cause))
    }
  }, [])

  const evaluate = useCallback(async (jobId: string, prompt: string) => {
    setIsEvaluating(true)
    setError(null)
    try {
      const result = await trainingApi.evaluate(jobId, {
        prompt,
        maxTokens: 128,
        temperature: 0.7,
        topK: 50,
        topP: 0.9,
        repetitionPenalty: 1.1,
        stopSequences: [],
      })
      setEvalResult(result)
    } catch (cause) {
      setError(toMessage(cause))
    } finally {
      setIsEvaluating(false)
    }
  }, [])

  const refresh = useCallback(async () => {
    setError(null)
    await Promise.all([loadJobs(), loadPresets(), loadCheckpoints()])
  }, [loadJobs, loadPresets, loadCheckpoints])

  // Initial load
  useEffect(() => {
    let cancelled = false
    const timer = window.setTimeout(() => {
      void (async () => {
        await Promise.all([loadJobs(), loadPresets(), loadCheckpoints()])
        if (!cancelled) setIsLoading(false)
      })()
    }, 0)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [loadJobs, loadPresets, loadCheckpoints])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreaming()
    }
  }, [stopStreaming])

  return {
    jobs,
    activeJob,
    history,
    checkpoints,
    presets,
    isLoading,
    isSubmitting,
    isStreaming,
    error,
    preset,
    modelName,
    batchSize,
    seqLen,
    maxSteps,
    lr,
    warmupSteps,
    evalInterval,
    checkpointInterval,
    dtype,
    evalPrompt,
    evalResult,
    isEvaluating,
    loadJobs,
    startTraining,
    cancelJob,
    resumeJob,
    selectJob,
    dismissJob,
    loadHistory,
    loadCheckpoints,
    loadPresets,
    evaluate,
    setFormField,
    clearError,
    refresh,
  }
}